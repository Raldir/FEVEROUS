import argparse
import json
from tqdm import tqdm
from utils.annotation_processor import AnnotationProcessor
import unicodedata
from cleantext import clean
from urllib.parse import unquote
import sys


def average(list):
    return float(sum(list) / len(list))


def clean_title(text):
    text = unquote(text)
    text = unicodedata.normalize('NFD', text)
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
    return text


def page_coverage(args):
    print("Page coverage...")
    coverage = []
    coverage_all = []
    in_path = 'data/{}.jsonl'.format(args.split)
    annotation_processor = AnnotationProcessor(in_path)
    annotation_by_id = {el.get_id(): el for el in annotation_processor}

    with open("data/{1}.pages.p{2}.jsonl".format(args.input_path, split,k),"r") as f:
        for idx,line in enumerate(f):
            js = json.loads(line)
            id = js['id']
            anno = annotation_by_id[id]
            docs_gold = list(set([clean_title(t) for t in anno.get_titles(flat=True)]))
            docs_predicted =  [clean_title(t[0]) for t in js['predicted_pages'][:3]]
            if anno.get_verdict() in ['SUPPORTS', 'REFUTES']:
                coverage_ele = len(set(docs_predicted) & set(docs_gold)) / len(docs_gold)
                coverage.append(coverage_ele)
                coverage_all.append(coverage_ele)
            else:
                coverage_ele = len(set(docs_predicted) & set(docs_gold)) / len(docs_gold)
                coverage_all.append(coverage_ele)

    print(average(coverage))
    print(average(coverage_all))




if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--anno_path', type=str)
    parser.add_argument('--split', type=str)
    parser.add_argument('--input_path', type=str)
    parser.add_argument('--mode', type=str)
    parser.add_argument('--count', type=int, default=1)
    args = parser.parse_args()
    split = args.split
    k = args.count

    page_coverage(args)

    sys.exit()

    q = 0
    q_all = 0
    score = 0
    score_all = 0
    in_path = 'data/{0}.jsonl'.format(split)
    annotation_processor = AnnotationProcessor(in_path)
    annotation_by_id = {el.get_id(): el for el in annotation_processor}

    with open("data/{1}.pages.p{2}.jsonl".format(split,k),"r") as f:
        for idx,line in enumerate(f):
            js = json.loads(line)
            id = js['id']
            anno = annotation_by_id[id]
            docs_gold = list(set(anno.get_titles(flat=True)))
            docs_predicted =  [t[0] for t in js['predicted_pages']]
            if anno.get_verdict() in ['SUPPORTS', 'REFUTES']:
                for p in docs_gold:
                    q += 1
                    if p in docs_predicted:
                        score+= (1/(docs_predicted.index(p)+1)) #mean reciprocal rank
            else:
                for p in docs_gold:
                    q_all += 1
                    if p in docs_predicted:
                        score_all+= (1/(docs_predicted.index(p)+1)) #mean reciprocal rank
    print(score/q)
    print(score_all/q_all)
