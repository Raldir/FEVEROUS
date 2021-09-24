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
    parser.add_argument('--max_page', type=int, default=1)
    parser.add_argument('--max_sent', type=int, default=1)
    parser.add_argument('--max_tabs', type=int, default=1)
    parser.add_argument('--data_path', type=str)
    args = parser.parse_args()
    split = args.split


    in_path_sent = '{0}/{1}.sentences.not_precomputed.p{2}.s{3}.jsonl'.format(args.data_path, split, args.max_page, args.max_sent)
    sentences_pred = {}
    with open(in_path_sent,"r") as f:
        for idx,line in enumerate(f):
            js = json.loads(line)
            # sentences_pred[js['id']] = js['predicted_sentences']
            sentences_pred[idx] = js['predicted_sentences']

    in_path_tabs = '{0}/{1}.tables.not_precomputed.p{2}.t{3}.jsonl'.format(args.data_path, split, args.max_page, args.max_tabs)
    tabs_pred = {}
    with open(in_path_tabs,"r") as f:
        for idx,line in enumerate(f):
            js = json.loads(line)
            tabs_pred[idx] = js['predicted_tables']

    out_path = '{0}/{1}.combined.not_precomputed.p{2}.s{3}.t{4}.jsonl'.format(args.data_path, split, args.max_page, args.max_sent, args.max_tabs)
    with jsonlines.open(os.path.join(out_path), 'w') as writer:
        with jsonlines.open("{0}/{1}.jsonl".format(args.data_path, args.split)) as f:
             for i,line in enumerate(f.iter()):
                 if i == 0:
                     writer.write({'header': ''})
                     continue # skip header line
                 # if len(line['evidence'][0]['content']) == 0: continue
                 line['predicted_evidence'] = sentences_pred[i-1] + tabs_pred[i-1]
                 line['id'] = i
                 writer.write(line)
