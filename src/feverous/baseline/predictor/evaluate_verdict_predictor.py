import argparse
import collections
import copy
import itertools
import math
import os
import random
import sys
from collections import Counter
from datetime import datetime

import jsonlines
import json
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
    logger.info("Acc: {}, Recall: {}, Precision: {}, F1: {}".format(acc, recall, precision, f1))
    return {"accuracy": acc, "f1": f1, "precision": precision, "recall": recall, "class_rep": class_rep}


def model_trainer(test_dataset, config):
    model = AutoModelForSequenceClassification.from_pretrained(
        config["model_path"], num_labels=3, return_dict=True
    ).to(config["device"])

    training_args = TrainingArguments(
        output_dir="./results",  # output directory
        per_device_eval_batch_size=config["per_device_eval_batch_size"],  # batch size for evaluation
    )

    trainer = Trainer(
        model=model,  # the instantiated 🤗 Transformers model to be trained
        args=training_args,  # training arguments, defined above
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


def claim_evidence_predictor(annotations_dev, feverous_db, input_path, config):
    map_verdict_to_index = config["map_verdict_to_index"]
    map_index_to_verdict = {y: x for x, y in map_verdict_to_index.items()}

    claim_evidence_input_test = [
        (prepare_input(anno, "schlichtkrull", feverous_db), anno.get_verdict()) for anno in tqdm(annotations_dev)
    ]

    logger.info("Sample instance {}".format(claim_evidence_input_test[0][0]))

    text_test, labels_test = process_data(claim_evidence_input_test, map_verdict_to_index)

    # tokenizer = AutoTokenizer.from_pretrained('ynie/roberta-large-snli_mnli_fever_anli_R1_R2_R3-nli')
    tokenizer = AutoTokenizer.from_pretrained(config["model_name"])

    text_test = tokenizer(text_test, padding=True, truncation=True)
    test_dataset = FEVEROUSDataset(text_test, labels_test)

    trainer, model = model_trainer(test_dataset, config)
    predictions = trainer.predict(test_dataset)
    predictions = predictions.predictions.argmax(-1)

    predictions_map = {annota.get_id(): predictions[i] for i, annota in enumerate(annotations_dev)}

    with jsonlines.open(os.path.join(input_path.split(".jsonl")[0] + ".verdict.jsonl"), "w") as writer:
        with jsonlines.open(os.path.join(input_path)) as f:
            for i, line in enumerate(f.iter()):
                if i == 0:
                    writer.write({"header": ""})  # skip header line
                    continue
                line["predicted_label"] = map_index_to_verdict[predictions_map[line["id"]]]
                writer.write(line)

    logger.info("Finished predicting verdicts...")


def predict_verdict(input_path: str, config_path: str, wiki_path: str) -> None:
    feverous_db = FeverousDB(wiki_path)

    annotations_dev = None
    anno_processor_dev = AnnotationProcessor(input_path)
    annotations_dev = [annotation for annotation in anno_processor_dev]

    logger.info("Start predicting verdicts...")

    with open(config_path, "r") as f:
        config = json.load(f)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    config["device"] = device

    claim_evidence_predictor(annotations_dev, feverous_db, input_path, config)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_path", type=str, help="/path/to/data")
    parser.add_argument("--config_path", type=str, help="/path/to/data")
    parser.add_argument("--wiki_path", type=str)

    args = parser.parse_args()

    predict_verdict(args.input_path, args.config_path, args.wiki_path)


if __name__ == "__main__":
    main()
