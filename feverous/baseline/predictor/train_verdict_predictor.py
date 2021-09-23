import sys
from datetime import datetime
import math
from collections import Counter
from transformers import BertForSequenceClassification, Trainer, TrainingArguments, AdamW, BertTokenizer, BertPreTrainedModel, BertModel,  RobertaForSequenceClassification, RobertaTokenizer
from transformers.modeling_outputs import SequenceClassifierOutput
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report
from sklearn.model_selection import train_test_split
import torch
from sklearn.model_selection import KFold
import numpy as np
import collections
import argparse
import jsonlines
import itertools
import random
import copy
from tqdm import tqdm
from utils.annotation_processor import AnnotationProcessor, EvidenceType
import os

from utils.prepare_model_input import prepare_input, init_db

from utils.log_helper import LogHelper

LogHelper.setup()
logger = LogHelper.get_logger(__name__)

class FEVEROUSDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels, use_labels = True):
        self.encodings = encodings
        self.labels = labels
        self.use_labels = use_labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        if self.use_labels:
            item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

def process_data(claim_verdict_list):

    map_verdict_to_index = {'NOT ENOUGH INFO': 0, 'SUPPORTS': 1, 'REFUTES': 2}
    text = [x[0] for x in claim_verdict_list]#["I love Pixar.", "I don't care for Pixar."]

    labels = [map_verdict_to_index[x[1]] for x in claim_verdict_list] #get value from enum


    return text, labels



def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average='micro')
    acc = accuracy_score(labels, preds)
    class_rep = classification_report(labels, preds, target_names= ['NOT ENOUGH INFO', 'SUPPORTS', 'REFUTES'], output_dict=True)
    logger.info(class_rep)
    logger.info(acc, recall, precision, f1)
    return {
        'accuracy': acc,
        'f1': f1,
        'precision': precision,
        'recall': recall,
        'class_rep': class_rep
    }



def model_trainer(model_path, train_dataset, test_dataset=None):
    model = RobertaForSequenceClassification.from_pretrained('ynie/roberta-large-snli_mnli_fever_anli_R1_R2_R3-nli', num_labels =3, return_dict=True)#ynie/roberta-large-snli_mnli_fever_anli_R1_R2_R3-nli


    training_args = TrainingArguments(
    output_dir=model_path,          # output directory
    num_train_epochs=1,              # total # of training epochs
    per_device_train_batch_size=16,  # batch size per device during training
    per_device_eval_batch_size=16,   # batch size for evaluation
    # gradient_accumulation_steps=3,
    warmup_steps=0,                # number of warmup steps for learning rate scheduler
    weight_decay=0.01,               # strength of weight decay
    logging_dir= os.path.join(model_path, 'logs'),            # directory for storing logs
    logging_steps=1200,
    save_steps = 5900, #1200,
    learning_rate = 1e-05
    # save_strategy='epoch'
    )

    if test_dataset != None:
        trainer = Trainer(
        model=model,                         # the instantiated 🤗 Transformers model to be trained
        args=training_args,                  # training arguments, defined above
        train_dataset=train_dataset,         # training dataset
        eval_dataset=test_dataset,          # evaluation dataset
        compute_metrics = compute_metrics,
        )
    else:
        trainer = Trainer(
        model=model,                         # the instantiated 🤗 Transformers model to be trained
        args=training_args,                  # training arguments, defined above
        train_dataset=train_dataset,         # training dataset
        compute_metrics = compute_metrics,
        )
    return trainer, model

def sample_nei_instances(annotations):
    max_num_to_sample = 1
    additional_instances = []
    for k, anno in enumerate(tqdm(annotations)):
        if anno.get_verdict() == 'NOT ENOUGH INFO':
            continue
        if anno.get_evidence_type(flat=True) == EvidenceType['JOINT']:
            selected_elements = [[ele] for ele in anno.flat_evidence if '_sentence_' in ele]
            cells_selected = [ele for ele in anno.flat_evidence if '_cell_' in ele]
            for ele in cells_selected:
                same_table = [el for el in anno.flat_evidence if el.split('_')[:3] == ele.split('_')[:3]]
                cells_selected = [el for el in cells_selected if el not in same_table]
                selected_elements.append(same_table)

            random.shuffle(selected_elements)
            selected_elements = selected_elements[:max_num_to_sample]
            for i in range(len(selected_elements)):
                anno_new = copy.deepcopy(anno)
                anno_new.flat_evidence = [ele for ele in anno_new.flat_evidence if ele not in selected_elements[i]] # Careful if flat evidene is not used in the future anymore
                anno_new.verdict = 'NOT ENOUGH INFO'
                additional_instances.append(anno_new)


    logger.info('Added additional {} NEI instances'. format(len(additional_instances)))
    annotations +=additional_instances
    return annotations



def claim_evidence_predictor(annotations_train, annotations_dev, args):

    # print([anno.get_source() for anno in annotations[:50]])
    # print([anno.get_claim() for anno in annotations[:50]])
    claim_evidence_input = [(prepare_input(anno, 'schlichtkrull', gold=True), anno.get_verdict()) for i,anno in enumerate(tqdm(annotations_train))]
    # print(claim_evidence_input[0])

    # print(claim_evidence_input[:10])


    claim_evidence_input_test = [(prepare_input(anno, 'schlichtkrull', gold=True), anno.get_verdict()) for i, anno in enumerate(tqdm(annotations_dev))]

    # claim_evidence_type_list = [[(anno.get_claim(), type) for type in anno.get_evidence_type()] for anno in annotations if len(anno.get_evidence(flat=True)) > 0]
    # claim_evidence_type_list = list(itertools.chain.from_iterable(claim_evidence_type_list))
    #

    text_train, labels_train = process_data(claim_evidence_input)

    text_test, labels_test = process_data(claim_evidence_input_test)

    tokenizer = RobertaTokenizer.from_pretrained('ynie/roberta-large-snli_mnli_fever_anli_R1_R2_R3-nli')
    text_train = tokenizer(text_train, padding=True, truncation=True)
    train_dataset = FEVEROUSDataset(text_train, labels_train)
    text_test = tokenizer(text_test, padding=True, truncation=True)
    test_dataset = FEVEROUSDataset(text_test, labels_test)

    trainer, model = model_trainer(args.model_path, train_dataset, test_dataset)
    trainer.train()
    scores = trainer.evaluate()
    logger.info(scores['eval_class_rep'])

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--input_path', type=str, help='/path/to/data')
    parser.add_argument('--sample_nei',action='store_true', default=False)
    parser.add_argument('--model_path', type=str, help='/path/to/data')
    parser.add_argument('--wiki_path', type=str, help='/path/to/data')

    args = parser.parse_args()

    args.train_data_path = os.path.join(args.input_path, 'train.jsonl')
    args.dev_data_path = os.path.join(args.input_path, 'dev.jsonl')

    init_db(args.wiki_path)
    anno_processor_train =AnnotationProcessor(args.train_data_path, has_content = True)
    annotations_train = [annotation for annotation in anno_processor_train]
    annotations_train = annotations_train
    if args.sample_nei:
        annotations_train = sample_nei_instances(annotations_train)
    annotations_dev = None
    anno_processor_dev = AnnotationProcessor(args.dev_data_path, has_content = True)
    annotations_dev = [annotation for annotation in anno_processor_dev]

    claim_evidence_predictor(annotations_train, annotations_dev, args)



if __name__ == "__main__":
    main()
