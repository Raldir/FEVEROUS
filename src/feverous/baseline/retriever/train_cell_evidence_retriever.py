import argparse
import collections
import itertools
import json
import math
import os
import sys
import unicodedata
from collections import Counter
from datetime import datetime
from urllib.parse import unquote

import jsonlines
import numpy as np
import torch
from cleantext import clean
from sklearn.metrics import accuracy_score, classification_report, precision_recall_fscore_support
from sklearn.model_selection import KFold, train_test_split
from tqdm import tqdm
from transformers import (
    AdamW,
    AutoTokenizer,
    BertForSequenceClassification,
    RobertaForTokenClassification,
    RobertaTokenizer,
    Trainer,
    TrainingArguments,
)
from transformers.modeling_outputs import SequenceClassifierOutput

from feverous.database.feverous_db import FeverousDB
from feverous.utils.log_helper import LogHelper
from feverous.utils.wiki_page import WikiPage

LogHelper.setup()
logger = LogHelper.get_logger(__name__)

from feverous.utils.annotation_processor import AnnotationProcessor, EvidenceType

avail_classes_test = None


class FEVEROUSDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels, use_labels=True):
        self.encodings = encodings
        self.labels = labels
        self.use_labels = use_labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        if self.use_labels:
            item["labels"] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)


def process_data(claim_verdict_list):
    text = [x[0] for x in claim_verdict_list]  # ["I love Pixar.", "I don't care for Pixar."]

    labels = [x[1] for x in claim_verdict_list]  # get value from enum
    #

    return text, labels


def score_by_cell_num(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)

    lab_by_cell_num = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
    pred_by_cell_num = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
    for i, lab in enumerate(labels):
        lab = list(lab)
        pred_c = list(preds[i])
        pred_c = [pred for i, pred in enumerate(pred_c) if lab[i] != -100]
        lab = [la for la in lab if la != -100]
        app = lab.count(1)
        if app <= 5:
            lab_by_cell_num[app] += lab
            pred_by_cell_num[app] += pred_c
        else:
            lab_by_cell_num[6] += lab
            pred_by_cell_num[6] += pred_c

    for key, value in lab_by_cell_num.items():
        logger.info("Num cells {}".format(key))
        precision, recall, f1, _ = precision_recall_fscore_support(value, pred_by_cell_num[key], average="micro")
        acc = accuracy_score(value, pred_by_cell_num[key])
        # map_verdict_to_index = {0:'Not enough Information', 1: 'Supported', 2:'Refuted'}
        class_rep = classification_report(value, pred_by_cell_num[key], output_dict=True)
        logger.info(class_rep)
        logger.info(acc, recall, precision, f1)
        logger.info("-----------------------------------")


def compute_metrics(pred):
    labels = list(itertools.chain(*pred.label_ids))
    preds = list(itertools.chain(*pred.predictions.argmax(-1)))
    preds = [pred for i, pred in enumerate(preds) if labels[i] != -100]
    labels = [lab for lab in labels if lab != -100]

    score_by_cell_num(pred)

    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average="micro")
    acc = accuracy_score(labels, preds)
    # map_verdict_to_index = {0:'Not enough Information', 1: 'Supported', 2:'Refuted'}
    class_rep = classification_report(labels, preds, output_dict=True)
    logger.info(class_rep)
    logger.info(acc, recall, precision, f1)
    return {"accuracy": acc, "f1": f1, "precision": precision, "recall": recall, "class_rep": class_rep}


def model_trainer(train_dataset, test_dataset, config):
    # model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels =4)
    model = RobertaForTokenClassification.from_pretrained(config["model_name"], num_labels=3, return_dict=True).to(
        config["device"]
    )

    training_args = TrainingArguments(
        output_dir=config["model_path"],  # output directory
        num_train_epochs=config["num_train_epochs"],  # total # of training epochs
        per_device_train_batch_size=config["per_device_train_batch_size"],  # batch size per device during training
        per_device_eval_batch_size=config["per_device_eval_batch_size"],  # batch size for evaluation
        # warmup_steps=0,                # number of warmup steps for learning rate scheduler
        weight_decay=config["weight_decay"],  # strength of weight decay
        logging_dir=os.path.join(config["model_path"], "logs"),
        learning_rate=config["learning_rate"],  # directory for storing logs
        logging_steps=config["logging_steps"],
        save_steps=config["save_steps"],
        # save_model = os.path.join(model_path, 'final_model')
    )

    trainer = Trainer(
        model=model,  # the instantiated 🤗 Transformers model to be trained
        args=training_args,  # training arguments, defined above
        train_dataset=train_dataset,  # training dataset
        eval_dataset=test_dataset,  # evaluation dataset
        compute_metrics=compute_metrics,
    )
    return trainer, model


def report_average(reports):
    mean_dict = dict()
    for label in reports[0].keys():
        dictionary = dict()

        if label in "accuracy":
            mean_dict[label] = sum(d[label] for d in reports) / len(reports)
            continue

        for key in reports[0][label].keys():
            dictionary[key] = sum(d[label][key] for d in reports) / len(reports)
        mean_dict[label] = dictionary

    return mean_dict


def clean_title(text):
    text = unquote(text)
    text = clean(
        text.strip(),
        fix_unicode=True,  # fix various unicode errors
        to_ascii=False,  # transliterate to closest ASCII representation
        lower=False,  # lowercase text
        no_line_breaks=False,  # fully strip line breaks as opposed to only normalizing them
        no_urls=True,  # replace all URLs with a special token
        no_emails=False,  # replace all email addresses with a special token
        no_phone_numbers=False,  # replace all phone numbers with a special token
        no_numbers=False,  # replace all numbers with a special token
        no_digits=False,  # replace all digits with a special token
        no_currency_symbols=False,  # replace all currency symbols with a special token
        no_punct=False,  # remove punctuations
        replace_with_url="<URL>",
        replace_with_email="<EMAIL>",
        replace_with_phone_number="<PHONE>",
        replace_with_number="<NUMBER>",
        replace_with_digit="0",
        replace_with_currency_symbol="<CUR>",
        lang="en",  # set to 'de' for German special handling
    )
    return text


def get_wikipage_by_id(id, db):
    page = id.split("_")[0]
    page = clean_title(page)
    page = unicodedata.normalize("NFD", page).strip()
    # pa = wiki_processor.process_title(page)
    # print(page)
    lines = db.get_doc_json(page)
    # print(lines)
    pa = WikiPage(page, lines)
    return pa, page


def convert_evidence_into_tables(annotation, db):
    evidence = annotation.get_evidence()[0]  # only bother with first set for now
    all_cells = []
    all_cells_id = []
    for piece in evidence:
        if "_cell_" in piece:
            all_cells.append(piece)
            all_cells_id.append("_".join(piece.split("_")[(2 if "header_cell_" in piece else 1) :]))
    cell_ids_by_table = {}
    table_by_id = {}
    for i, cell in enumerate(all_cells):
        pa, page = get_wikipage_by_id(cell, db)
        table = pa.get_table_from_cell(all_cells_id[i])
        tab_id = page + "_" + table.get_id().replace("t_", "table_")
        # print(tab_id)
        if tab_id in cell_ids_by_table:
            cell_ids_by_table[tab_id].append(all_cells_id[i])
        else:
            cell_ids_by_table[tab_id] = [all_cells_id[i]]
            table_by_id[tab_id] = table
    output_tables = []
    output_labels = []
    for id, cells in cell_ids_by_table.items():
        curr_tab = table_by_id[id]
        table_flat = [annotation.get_claim(), "</s>"]
        labels_flat = [0, 0]
        for row in curr_tab.rows:
            for j, cell in enumerate(row.row):
                table_flat.append(str(cell))
                if cell.get_id() in cells:
                    labels_flat.append(1)
                else:
                    labels_flat.append(0)
                if j < len(row.row) - 1:
                    table_flat.append("|")
                    labels_flat.append(0)
            table_flat.append("</s>")
            labels_flat.append(0)
        output_tables.append(table_flat)
        output_labels.append(labels_flat)
    return (output_tables, output_labels)


def tokenize_and_align_labels(text_in, labels_in, tokenizer):
    label_all_tokens = False
    tokenized_inputs = tokenizer(
        text_in,
        padding=True,
        truncation=True,
        # We use this argument because the texts in our dataset are lists of words (with a label for each word).
        is_split_into_words=True,
    )
    labels = []
    for i, label in enumerate(labels_in):
        word_ids = tokenized_inputs.word_ids(batch_index=i)
        previous_word_idx = None
        label_ids = []
        for word_idx in word_ids:
            if word_idx is None:
                label_ids.append(-100)
            elif word_idx != previous_word_idx:
                label_ids.append(label[word_idx])
            else:
                label_ids.append(label[word_idx] if label_all_tokens else -100)
            previous_word_idx = word_idx
        labels.append(label_ids)
    tokenized_inputs["labels"] = labels
    return tokenized_inputs, labels


def trainer_cell_retriever(annotations_train, annotations_dev, db, config):
    all_input = []
    all_labels = []

    all_input_dev = []
    all_labels_dev = []

    for i, anno in enumerate(tqdm(annotations_train)):
        tabs, labs = convert_evidence_into_tables(anno, db)
        all_input += tabs
        all_labels += labs

    for i, anno in enumerate(tqdm(annotations_dev)):
        tabs, labs = convert_evidence_into_tables(anno, db)
        all_input_dev += tabs
        all_labels_dev += labs

    claim_evidence_type_list = list(zip(all_input, all_labels))
    text_train, labels_train = process_data(claim_evidence_type_list)

    claim_evidence_type_list_dev = list(zip(all_input_dev, all_labels_dev))
    text_dev, labels_dev = process_data(claim_evidence_type_list_dev)

    tokenizer = AutoTokenizer.from_pretrained(config["model_name"], do_lower_case=True, add_prefix_space=True)

    text_train, labels_train = tokenize_and_align_labels(text_train, labels_train, tokenizer)
    text_dev, labels_dev = tokenize_and_align_labels(text_dev, labels_dev, tokenizer)

    train_dataset = FEVEROUSDataset(text_train, labels_train)
    dev_dataset = FEVEROUSDataset(text_dev, labels_dev)

    trainer, model = model_trainer(train_dataset, dev_dataset, config)
    trainer.train()
    scores = trainer.evaluate()


def train_cell_retriever(input_path: str, wiki_path: str, config_path: str):
    data_path_train = os.path.join(input_path, "train.jsonl")
    data_path_dev = os.path.join(input_path, "dev.jsonl")

    db = FeverousDB(wiki_path)

    with open(config_path, "r") as f:
        config = json.load(f)

    anno_processor_train = AnnotationProcessor(data_path_train, limit=10)
    anno_processor_dev = AnnotationProcessor(data_path_dev, limit=10)
    annotations_train = [annotation for annotation in anno_processor_train]
    annotations_dev = [annotation for annotation in anno_processor_dev]

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    config["device"] = device

    trainer_cell_retriever(annotations_train, annotations_dev, db, config)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_path", type=str, help="/path/to/data", default=None)
    parser.add_argument("--wiki_path", type=str)
    parser.add_argument("--config_path", type=str)

    args = parser.parse_args()

    train_cell_retriever(args.input_path, args.wiki_path, args.config_path)


if __name__ == "__main__":
    main()
