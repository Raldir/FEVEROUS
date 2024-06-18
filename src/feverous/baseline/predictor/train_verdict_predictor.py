import argparse
import collections
import copy
import itertools
import math
import json
import os
import random
import sys
from collections import Counter
from datetime import datetime

import jsonlines
import numpy as np
import torch
from sklearn.metrics import accuracy_score, classification_report, precision_recall_fscore_support
from sklearn.model_selection import KFold, train_test_split
from tqdm import tqdm
from transformers import (
    AdamW,
    AutoModelForSequenceClassification,
    AutoTokenizer,
    BertForSequenceClassification,
    BertModel,
    BertPreTrainedModel,
    BertTokenizer,
    RobertaForSequenceClassification,
    RobertaTokenizer,
    Trainer,
    TrainingArguments,
)
from transformers.modeling_outputs import SequenceClassifierOutput

from feverous.database.feverous_db import FeverousDB
from feverous.utils.annotation_processor import AnnotationProcessor, EvidenceType
from feverous.utils.log_helper import LogHelper
from feverous.utils.prepare_model_input import prepare_input

LogHelper.setup()
logger = LogHelper.get_logger(__name__)


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


def process_data(claim_verdict_list, map_verdict_to_index):
    text = [x[0] for x in claim_verdict_list]

    labels = [map_verdict_to_index[x[1]] for x in claim_verdict_list]  # get value from enum

    return text, labels


def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average="micro")
    acc = accuracy_score(labels, preds)
    class_rep = classification_report(
        labels, preds, target_names=["NOT ENOUGH INFO", "SUPPORTS", "REFUTES"], output_dict=True
    )
    logger.info(class_rep)
    logger.info(acc, recall, precision, f1)
    return {"accuracy": acc, "f1": f1, "precision": precision, "recall": recall, "class_rep": class_rep}


def model_trainer(train_dataset, test_dataset, config):
    model = AutoModelForSequenceClassification.from_pretrained(
        config["model_name"], num_labels=3, return_dict=True
    ).to(
        config["device"]
    )  # protobuf
    #     model = AutoModelForSequenceClassification.from_pretrained(
    #     "cross-encoder/nli-deberta-v3-large", num_labels=3, return_dict=True
    # )  # protobuf

    training_args = TrainingArguments(
        output_dir=config["model_path"],  # output directory
        num_train_epochs=config["num_train_epochs"],  # total # of training epochs
        per_device_train_batch_size=config["per_device_train_batch_size"],  # batch size per device during training
        per_device_eval_batch_size=config["per_device_eval_batch_size"],  # batch size for evaluation
        gradient_accumulation_steps=config["gradient_accumulation_steps"],
        warmup_steps=config["warmup_steps"],  # number of warmup steps for learning rate scheduler
        weight_decay=config["weight_decay"],  # strength of weight decay
        logging_dir=os.path.join(config["model_path"], "logs"),  # directory for storing logs
        logging_steps=config["logging_steps"],
        save_steps=config["save_steps"],  # 1200,
        learning_rate=config["learning_rate"]
        # save_strategy='epoch'
    )

    if test_dataset != None:
        trainer = Trainer(
            model=model,  # the instantiated 🤗 Transformers model to be trained
            args=training_args,  # training arguments, defined above
            train_dataset=train_dataset,  # training dataset
            eval_dataset=test_dataset,  # evaluation dataset
            compute_metrics=compute_metrics,
        )
    else:
        trainer = Trainer(
            model=model,  # the instantiated 🤗 Transformers model to be trained
            args=training_args,  # training arguments, defined above
            train_dataset=train_dataset,  # training dataset
            compute_metrics=compute_metrics,
        )
    return trainer, model


def sample_nei_instances(annotations, max_num_to_sample=1):
    additional_instances = []
    for k, anno in enumerate(tqdm(annotations)):
        if anno.get_verdict() == "NOT ENOUGH INFO":
            continue
        if anno.get_evidence_type(flat=True) == EvidenceType["JOINT"]:
            selected_elements = [[ele] for ele in anno.flat_evidence if "_sentence_" in ele]
            cells_selected = [ele for ele in anno.flat_evidence if "_cell_" in ele]
            for ele in cells_selected:
                same_table = [el for el in anno.flat_evidence if el.split("_")[:3] == ele.split("_")[:3]]
                cells_selected = [el for el in cells_selected if el not in same_table]
                selected_elements.append(same_table)

            random.shuffle(selected_elements)
            selected_elements = selected_elements[:max_num_to_sample]
            for i in range(len(selected_elements)):
                anno_new = copy.deepcopy(anno)
                anno_new.flat_evidence = [
                    ele for ele in anno_new.flat_evidence if ele not in selected_elements[i]
                ]  # Careful if flat evidene is not used in the future anymore
                anno_new.verdict = "NOT ENOUGH INFO"
                additional_instances.append(anno_new)

    logger.info("Added additional {} NEI instances".format(len(additional_instances)))
    annotations += additional_instances
    return annotations


def claim_evidence_predictor(annotations_train, annotations_dev, feverous_db, config):
    claim_evidence_input = [
        (prepare_input(anno, "schlichtkrull", feverous_db, gold=True), anno.get_verdict())
        for i, anno in enumerate(tqdm(annotations_train))
    ]

    claim_evidence_input_test = [
        (prepare_input(anno, "schlichtkrull", feverous_db, gold=True), anno.get_verdict())
        for i, anno in enumerate(tqdm(annotations_dev))
    ]

    print(claim_evidence_input[0])
    print(claim_evidence_input_test[0])

    text_train, labels_train = process_data(claim_evidence_input, config["map_verdict_to_index"])

    text_test, labels_test = process_data(claim_evidence_input_test, config["map_verdict_to_index"])

    tokenizer = AutoTokenizer.from_pretrained(config["model_name"])
    # tokenizer = AutoTokenizer.from_pretrained(
    # "cross-encoder/nli-deberta-v3-large"
    # )  # ynie/roberta-large-snli_mnli_fever_anli_R1_R2_R3-nli')
    text_train = tokenizer(text_train, padding=True, truncation=True)
    train_dataset = FEVEROUSDataset(text_train, labels_train)
    text_test = tokenizer(text_test, padding=True, truncation=True)
    test_dataset = FEVEROUSDataset(text_test, labels_test)

    trainer, model = model_trainer(train_dataset, test_dataset, config)
    trainer.train()
    scores = trainer.evaluate()
    logger.info(scores["eval_class_rep"])


def train_verdict_predictor(input_path: str, config_path: str, wiki_path: str, sample_nei: bool = True) -> None:
    feverous_db = FeverousDB(wiki_path)

    # train_data_path = os.path.join(input_path, "train.jsonl")
    # dev_data_path = os.path.join(input_path, "dev.jsonl")

    train_data_path = os.path.join(input_path, "train.combined.not_precomputed.p5.s5.t3.cells.jsonl")
    dev_data_path = os.path.join(input_path, "dev.combined.not_precomputed.p5.s5.t3.cells.jsonl")

    with open(config_path, "r") as f:
        config = json.load(f)

    anno_processor_train = AnnotationProcessor(train_data_path, with_content=False, limit=40000)
    annotations_train = [annotation for annotation in anno_processor_train]
    print(annotations_train[0].claim, annotations_train[0].flat_evidence)
    # annotations_train = annotations_train
    if sample_nei:
        annotations_train = sample_nei_instances(annotations_train, config["nei_sampling_ratio"])

    anno_processor_dev = AnnotationProcessor(dev_data_path, with_content=False)
    annotations_dev = [annotation for annotation in anno_processor_dev]

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    config["device"] = device

    claim_evidence_predictor(annotations_train, annotations_dev, feverous_db, config)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_path", type=str, help="/path/to/data")
    parser.add_argument("--sample_nei", action="store_true", default=False)
    parser.add_argument("--wiki_path", type=str, help="/path/to/data")
    parser.add_argument("--config_path", type=str, help="/path/to/data")

    args = parser.parse_args()
    train_verdict_predictor(args.input_path, args.config_path, args.wiki_path, args.sample_nei)


if __name__ == "__main__":
    main()
