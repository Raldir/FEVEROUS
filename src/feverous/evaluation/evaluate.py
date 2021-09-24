import argparse
import jsonlines
import os
import sys

import unicodedata
from cleantext import clean
from urllib.parse import unquote

from feverous_scorer import feverous_score

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--input_path', type=str)
    parser.add_argument('--use_gold_verdict', action='store_true', default=False)

    args = parser.parse_args()
    predictions = []

    with jsonlines.open(os.path.join(args.input_path)) as f:
         for i,line in enumerate(f.iter()):
            if i  == 0 :
                 continue
            if args.use_gold_verdict:
                line['predicted_label'] = line['label']
            line['evidence'] = [el['content'] for el in line['evidence']]
            for j in range(len(line['evidence'])):
                # line['evidence'][j] = [[el.split('_')[0], el.split('_')[1], '_'.join(el.split('_')[2:])] for el in  line['evidence'][j]]
                line['evidence'][j]= [[el.split('_')[0], el.split('_')[1] if 'table_caption' not in el and 'header_cell' not in el else '_'.join(el.split('_')[1:3]), '_'.join(el.split('_')[2:]) if 'table_caption' not in el and 'header_cell' not in el else '_'.join(el.split('_')[3:])] for el in  line['evidence'][j]]

            line['predicted_evidence']= [[el.split('_')[0], el.split('_')[1] if 'table_caption' not in el and 'header_cell' not in el else '_'.join(el.split('_')[1:3]), '_'.join(el.split('_')[2:]) if 'table_caption' not in el and 'header_cell' not in el else '_'.join(el.split('_')[3:])] for el in line['predicted_evidence']]
            # line['predicted_evidence'] = [[el.split('_')[0], el.split('_')[1], '_'.join(el.split('_')[2:])] for el in  line['predicted_evidence']]
            # print(line['predicted_evidence'])
            # line['label'] = line['verdict']
            predictions.append(line)
    print('Feverous scores...')
    strict_score, label_accuracy, precision, recall, f1 = feverous_score(predictions)
    print(strict_score)     #0.5
    print(label_accuracy)   #1.0
    print(precision)        #0.833 (first example scores 1, second example scores 2/3)
    print(recall)           #0.5 (first example scores 0, second example scores 1)
    print(f1)               #0.625
