import argparse
import json
from tqdm import tqdm
from utils.annotation_processor import AnnotationProcessor, EvidenceType
import jsonlines
import os


def average(list):
    return float(sum(list) / len(list))

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--split', type=str)
    parser.add_argument('--input_path', type=str)
    parser.add_argument('--max_page', type=int, default=1)
    parser.add_argument('--max_sent', type=int, default=1)
    parser.add_argument('--max_tabs', type=int, default=1)
    args = parser.parse_args()
    split = args.split


    in_path_sent = 'data/{0}.sentences.not_precomputed.p{1}.s{2}.jsonl'.format(split, args.max_page, args.max_sent)
    sentences_pred = {}
    with open(in_path_sent,"r") as f:
        for idx,line in enumerate(f):
            js = json.loads(line)
            sentences_pred[js['id']] = js['predicted_sentences']

    in_path_tabs = 'data/{0}.tables.not_precomputed.p{1}.t{2}.jsonl'.format(split, args.max_page, args.max_tabs)
    tabs_pred = {}
    with open(in_path_tabs,"r") as f:
        for idx,line in enumerate(f):
            js = json.loads(line)
            tabs_pred[js['id']] = js['predicted_tables']

    out_path = 'data/{0}.combined.not_precomputed.p{1}.s{2}.t{3}.jsonl'.format(split, args.max_page, args.max_sent, args.max_tabs)
    with jsonlines.open(os.path.join(out_path), 'w') as writer:
        with jsonlines.open(os.path.join(args.input_path)) as f:
             for i,line in enumerate(f.iter()):
                 if i == 0: continue # skip header line
                 if len(line['evidence'][0]['content']) == 0: continue
                 line['predicted_evidence'] = sentences_pred[line['id']] + tabs_pred[line['id']]
                 writer.write(line)
