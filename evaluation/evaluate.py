import argparse
import jsonlines
import os
import sys

import unicodedata
from cleantext import clean
from urllib.parse import unquote



from evaluation.feverous_scorer import feverous_score

def clean_title(text):
    text = unquote(text)
    text = clean(text.strip(),fix_unicode=True,               # fix various unicode errors
    to_ascii=False,                  # transliterate to closest ASCII representation
    lower=False,                     # lowercase text
    no_line_breaks=False,           # fully strip line breaks as opposed to only normalizing them
    no_urls=True,                  # replace all URLs with a special token
    no_emails=False,                # replace all email addresses with a special token
    no_phone_numbers=False,         # replace all phone numbers with a special token
    no_numbers=False,               # replace all numbers with a special token
    no_digits=False,                # replace all digits with a special token
    no_currency_symbols=False,      # replace all currency symbols with a special token
    no_punct=False,                 # remove punctuations
    replace_with_url="<URL>",
    replace_with_email="<EMAIL>",
    replace_with_phone_number="<PHONE>",
    replace_with_number="<NUMBER>",
    replace_with_digit="0",
    replace_with_currency_symbol="<CUR>",
    lang="en"                       # set to 'de' for German special handling
    )
    text = unicodedata.normalize('NFD', text).strip()
    return text



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
                line['evidence'][j] = [[clean_title(el.split('_')[0]), el.split('_')[1], '_'.join(el.split('_')[2:])] for el in  line['evidence'][j]]
            line['predicted_evidence'] = [[clean_title(el.split('_')[0]), el.split('_')[1], '_'.join(el.split('_')[2:])] for el in  line['predicted_evidence']]
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
