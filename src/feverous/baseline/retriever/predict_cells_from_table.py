import sys
from datetime import datetime
import math
from collections import Counter
from transformers import BertForSequenceClassification, Trainer, TrainingArguments, AdamW, RobertaForTokenClassification, RobertaTokenizer, AutoTokenizer
from transformers.modeling_outputs import SequenceClassifierOutput
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report
import unicodedata
from sklearn.model_selection import train_test_split
import torch
from sklearn.model_selection import KFold
import numpy as np
import collections
import argparse
import jsonlines
import json
from tqdm import tqdm
import itertools
import os
from cleantext import clean
from urllib.parse import unquote
import torch

from utils.annotation_processor import AnnotationProcessor, EvidenceType
from utils.wiki_page import WikiPage, get_wikipage_by_id
from database.feverous_db import FeverousDB
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

    text = [x[0] for x in claim_verdict_list]#["I love Pixar.", "I don't care for Pixar."]
    labels = [x[1] for x in claim_verdict_list] #get value from enum

    return text, labels


def compute_metrics(pred):
    labels = list(itertools.chain(*pred.label_ids))
    preds = list(itertools.chain(*pred.predictions.argmax(-1)))
    preds = [pred for i, pred in enumerate(preds) if labels[i] != -100]
    labels = [lab for lab in labels if lab != -100]

    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average='micro')
    acc = accuracy_score(labels, preds)
    # map_verdict_to_index = {0:'Not enough Information', 1: 'Supported', 2:'Refuted'}
    class_rep = classification_report(labels, preds, output_dict=True)
    return {
        'accuracy': acc,
        'f1': f1,
        'precision': precision,
        'recall': recall,
        'class_rep': class_rep
    }


def model_trainer(args, test_dataset):
    # model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels =4)
    model = RobertaForTokenClassification.from_pretrained(args.model_path, num_labels = 3, return_dict=True)

    #/anfs/bigdisc/rmya2/faiss_data/results_table_to_cell2/checkpoint-1400/'
    training_args = TrainingArguments(
    per_device_train_batch_size=16,  # batch size per device during training
    per_device_eval_batch_size=16,   # batch size for evaluation
    # warmup_steps=0,                # number of warmup steps for learning rate scheduler
    logging_dir='./logs',
    output_dir='./model_output'
    )

    trainer = Trainer(
    model=model,                         # the instantiated 🤗 Transformers model to be trained
    args=training_args,                  # training arguments, defined above
    eval_dataset=test_dataset,          # evaluation dataset
    compute_metrics = compute_metrics,
    )
    return trainer, model


def report_average(reports):
    mean_dict = dict()
    for label in reports[0].keys():
        dictionary = dict()

        if label in 'accuracy':
            mean_dict[label] = sum(d[label] for d in reports) / len(reports)
            continue

        for key in reports[0][label].keys():
            dictionary[key] = sum(d[label][key] for d in reports) / len(reports)
        mean_dict[label] = dictionary

    return mean_dict


def convert_evidence_into_tables_gold(annotation, db):
    evidence = annotation.get_evidence()[0] #only bother with first set for now
    all_cells = []
    all_cells_id = []
    for piece in evidence:
        if '_cell_' in piece:
            all_cells.append(piece)
            all_cells_id.append('_'.join(piece.split('_')[1:]))
    cell_ids_by_table = {}
    table_by_id = {}
    for i,cell in enumerate(all_cells):
        pa, page = get_wikipage_by_id(cell, db)
        if pa == None:
            continue
        table = pa.get_table_from_cell(all_cells_id[i])
        tab_id = page + "_"  + table.get_id().replace('t_', 'table_')
        if tab_id in cell_ids_by_table:
            cell_ids_by_table[tab_id].append(all_cells_id[i])
        else:
            cell_ids_by_table[tab_id] = [all_cells_id[i]]
            table_by_id[tab_id] = table
    output_tables = []
    output_tables_ids = []
    output_labels = []
    for id, cells in cell_ids_by_table.items():
        curr_tab = table_by_id[id]
        table_flat = [annotation.get_claim(), '</s>']
        table_flat_ids = [0, 0]
        labels_flat = [0, 0]
        for row in curr_tab.rows:
            for j, cell in enumerate(row.row):
                table_flat.append(str(cell))
                # table_flat_ids.append(id.split('_')[0] + cell.get_id().replace('hc_', '_header_cell_').replace('c_','_cell_'))
                table_flat_ids.append(id.split('_')[0] + '_' + cell.get_id().replace('hc_', 'header_cell_').replace('c_','cell_'))
                # cell_header_ele = [ele.split('_')[0] + '_' +  el.get_id().replace('hc_', 'header_cell_') for el in wiki_page.get_context('_'.join(ele.split('_')[1:])) if "header_cell_" in el.get_id()]
                if cell.get_id() in cells:
                    labels_flat.append(1)
                else:
                    labels_flat.append(0)
                if j < len(row.row) -1:
                    table_flat.append('|')
                    table_flat_ids.append(0)
                    labels_flat.append(0)
            table_flat.append('</s>')
            table_flat_ids.append(0)
            labels_flat.append(0)
        output_tables.append(table_flat)
        output_tables_ids.append(table_flat_ids)
        output_labels.append(labels_flat)
    return (output_tables, output_tables_ids, output_labels)

def convert_evidence_into_tables(annotation, db, args):
    predicted_sentences= [ele[0] + '_sentence_' + ele[1].split('_')[1] for ele in annotation.predicted_evidence  if ele[1].split('_')[0] == 'sentence']
    predicted_tables =  [ele[0] + '_table_' + ele[1].split('_')[1] for ele in annotation.predicted_evidence if ele[1].split('_')[0] == 'table']
    evidence = set(list(predicted_sentences[:3] + predicted_tables[:2]))
    tables = [ele for ele in evidence if '_table_' in ele]
    output_tables = []
    output_tables_ids = []
    for tab_id in tables:
        pa, page = get_wikipage_by_id(tab_id, db)
        if pa == None:
            continue
        curr_tab = pa.page_items['_'.join(tab_id.split('_')[1:])]
        table_flat = [annotation.get_claim(), '</s>']
        table_flat_ids = [0, 0]
        for row in curr_tab.rows:
            for j, cell in enumerate(row.row):
                table_flat.append(str(cell))
                table_flat_ids.append(page + '_' + cell.get_id().replace('hc_', 'header_cell_').replace('c_','cell_'))
                if j < len(row.row) -1:
                    table_flat.append('|')
                    table_flat_ids.append(0)
            table_flat.append('</s>')
            table_flat_ids.append(0)
        output_tables.append(table_flat)
        output_tables_ids.append(table_flat_ids)
    return (output_tables, output_tables_ids)



def tokenize_and_align_labels(text_in, labels_in, all_input_ids, tokenizer):
    label_all_tokens = False
    tokenized_inputs = tokenizer(
        text_in,
        padding=True,
        truncation=True,
        # We use this argument because the texts in our dataset are lists of words (with a label for each word).
        is_split_into_words=True,
    )
    labels = []
    all_input_ids_new = []
    for i, label in enumerate(labels_in):
        word_ids = tokenized_inputs.word_ids(batch_index=i)
        previous_word_idx = None
        label_ids = []
        input_ids = []
        for word_idx in word_ids:
            # Special tokens have a word id that is None. We set the label to -100 so they are automatically
            # ignored in the loss function.
            if word_idx is None:
                label_ids.append(-100)
                input_ids.append(-100)
            # We set the label for the first token of each word.
            elif word_idx != previous_word_idx:
                label_ids.append(label[word_idx])
                input_ids.append(all_input_ids[i][word_idx])
            # For the other tokens in a word, we set the label to either the current label or -100, depending on
            # the label_all_tokens flag.
            else:
                label_ids.append(label[word_idx] if label_all_tokens else -100)
                input_ids.append(all_input_ids[i][word_idx] if label_all_tokens else -100)
            previous_word_idx = word_idx
        labels.append(label_ids)
        all_input_ids_new.append(input_ids)
    tokenized_inputs["labels"] = labels
    return tokenized_inputs, all_input_ids_new, labels

def extract_cells_from_tables(annotations, args):
    db = FeverousDB(args.wiki_path)
    all_input = []
    all_input_ids = []
    all_labels = []
    anno_ids = []
    for i, anno in enumerate(tqdm(annotations)):
        tabs,tabs_ids = convert_evidence_into_tables(anno, db, args)
        all_input += tabs
        all_input_ids += tabs_ids
        all_labels += [[0] * len(el) for el in tabs] #dummy labels
        anno_ids += len(tabs) * [anno.get_id()]


    logger.info('Sample entry: {}'.format(all_input[0]))
    # logger.info('Sample label: {}'.format(all_labels[0]))
    logger.info('Sample id: {}'.format(anno_ids[0]))

    if not args.trivial_baseline:
        tokenizer = AutoTokenizer.from_pretrained('roberta-base', do_lower_case=True, add_prefix_space=True)


        text_test, all_input_ids, labels_test = tokenize_and_align_labels(all_input, all_labels, all_input_ids, tokenizer) #dummy labels

        # lab_after = [[pred for i, pred in enumerate(label) if labels_test[j][i] != -100] for j,label in enumerate(labels_test)]

        test_dataset = FEVEROUSDataset(text_test, labels_test)

        trainer, model = model_trainer(args, test_dataset)
        model_output = trainer.predict(test_dataset)

        # predictions = model_output.predictions.argmax(-1)
        predictions =  (model_output.predictions > 0.25).astype(int)
        # print(predictions)
        predictions = [[1 if ele[1]==1 else 0 for ele in e] for e in predictions]
        # print(predictions)
        # print([list(pred).count(1) for pred in predictions])
        labels = model_output.label_ids

        # preds = pred.predictions.argmax(-1)

        predictions = [[pred for i, pred in enumerate(pred_instance) if labels[j][i] != -100] for j,pred_instance in enumerate(predictions)]

        all_input_ids = [[pred for i, pred in enumerate(label) if labels[j][i] != -100] for j,label in enumerate(all_input_ids)]

        # print(predictions)
        predictions_map = {anno_ids[i]:[all_input_ids[i][j] for j,el in enumerate(predictions[i]) if predictions[i][j] == 1 and all_input_ids[i][j] != 0] for i,annota in enumerate(anno_ids)}
    else:
        predictions_map = {value: [e for e in all_input_ids[i] if e !=0][:25] for i, value in enumerate(anno_ids)}
    # print(predictions_map.keys())

    with jsonlines.open(os.path.join(args.input_path.split('.jsonl')[0] + '.cells.jsonl') , 'w') as writer:
        with jsonlines.open(os.path.join(args.input_path)) as f:
             for i,line in enumerate(f.iter()):
                 if i == 0:
                     writer.write({'header':''}) # skip header line
                     continue
                 # if len(line['evidence'][0]['content']) == 0: continue
                 predicted_sentences= [ele[0] + '_sentence_' + ele[1].split('_')[1] for ele in line['predicted_evidence'] if ele[1].split('_')[0] == 'sentence']
                 predicted_tables =  [ele[0] + '_table_' + ele[1].split('_')[1] for ele in line['predicted_evidence']  if ele[1].split('_')[0] == 'table' ]
                 line['predicted_evidence'] = set(list(predicted_sentences + predicted_tables))
                 if not args.trivial_baseline:
                     line['predicted_evidence'] = [ele for ele in line['predicted_evidence'] if ('_table_' not in ele and '_table_caption_' not in ele)]
                 else:
                     line['predicted_evidence'] = [ele for ele in line['predicted_evidence'] if ('_table_' not in ele and '_table_caption_' not in ele and '_sentence_' not in ele)]
                 # print(line['id'])
                 for key, value in predictions_map.items():
                     if key == line['id']:
                         line['predicted_evidence'] += predictions_map[key]
                 writer.write(line)

    logger.info('Finished extracting cells...')



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_path', type=str, help='/path/to/data')
    parser.add_argument('--model_path', type=str, help='/path/to/data')
    parser.add_argument('--trivial_baseline', action='store_true', default=False)
    parser.add_argument('--max_sent', type=int, default=5, help='/path/to/data')
    parser.add_argument('--wiki_path', type=str)

    args = parser.parse_args()

    anno_processor =AnnotationProcessor(args.input_path)
    annotations = [annotation for annotation in anno_processor]
    # annotations.sort(key=lambda x: x.source, reverse=True)
    logger.info('Start extracting cells from Tables...')
    extract_cells_from_tables(annotations, args)



if __name__ == "__main__":
    main()
