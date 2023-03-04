import argparse
import json
import unicodedata
from urllib.parse import unquote

from cleantext import clean
from tqdm import tqdm

from feverous.utils.annotation_processor import AnnotationProcessor, EvidenceType


def average(list):
    return float(sum(list) / len(list))


def clean_title(text):
    text = unquote(text)
    text = unicodedata.normalize("NFD", text)
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


def extract_tables_from_evidence(evidence_list):
    new_evidence = []
    for ev in evidence_list:
        if "_cell_" in ev:
            table_id = ev.split("_")[0] + "_table_" + ev.split("_")[2]
            if table_id not in new_evidence:
                new_evidence.append(table_id)
        elif "_header_cell" in ev:
            table_id = ev.split("_")[0] + "_table_" + ev.split("_")[3]
            if table_id not in new_evidence:
                new_evidence.append(table_id)
        elif "_item_" not in ev and "_caption_" not in ev:
            new_evidence.append(ev)
    return new_evidence


def average(list):
    return float(sum(list) / len(list))


def evidence_coverage(args):
    print("Evidence coverage...")
    coverage = []
    coverage_all = []
    # in_path = 'data/annotations/{0}.sentences.not_precomputed.p{1}.s{2}.jsonl'.format(split, args.max_page, args.max_sent)
    annotation_processor = AnnotationProcessor("data/{}.jsonl".format(args.split))
    if args.all == 0:
        annotation_by_id = {
            i: el
            for i, el in enumerate(annotation_processor)
            if el.has_evidence() and el.get_evidence_type(flat=True) == EvidenceType.SENTENCE
        }
    else:
        annotation_by_id = {i: el for i, el in enumerate(annotation_processor) if el.has_evidence()}

    with open(
        "data/{}.combined.not_precomputed.p{}.s{}.t{}.jsonl".format(
            args.split, args.max_page, args.max_sent, args.max_tabs
        ),
        "r",
    ) as f:
        for idx, line in enumerate(f):
            if idx == 0:
                continue
            js = json.loads(line)
            id = idx - 1  # js['id']
            if id not in annotation_by_id:
                continue
            anno = annotation_by_id[id]
            docs_gold_e = list(set(anno.get_evidence(flat=True)))
            docs_gold_s = set(list(set([clean_title(t) for t in docs_gold_e if "_sentence_" in t])))
            # docs_gold = extract_tables_from_evidence(docs_gold)
            docs_gold_t = set(
                [
                    clean_title(ev.split("_")[0]) + "_table_" + ev.split("_")[3 if "_header_cell_" in ev else 2]
                    for ev in docs_gold_e
                    if "_cell_" in ev
                ]
            )
            docs_gold = set(docs_gold_s | docs_gold_t)

            if len(docs_gold) == 0:
                continue
            docs_gold = set([clean_title(doc).strip() for doc in docs_gold])
            predicted_sentences = [
                clean_title(ele[0]) + "_sentence_" + ele[1].split("_")[1]
                for ele in js["predicted_evidence"]
                if ele[1].split("_")[0] == "sentence"
            ]
            predicted_tables = [
                clean_title(ele[0]) + "_table_" + ele[1].split("_")[1]
                for ele in js["predicted_evidence"]
                if ele[1].split("_")[0] == "table"
            ]
            docs_predicted = set(list(predicted_sentences + predicted_tables))
            #
            # print(docs_gold)
            # print(docs_predicted)
            # print('-----------')
            if args.all == 0:
                docs_predicted = [ele for ele in docs_predicted if "_sentence_" in ele]
            # print(docs_gold, docs_predicted)
            # docs_predicted =  [t[0] + '_' + t[1].replace('s_', 'sentence_') for t in js['predicted_sentences']]
            if anno.get_verdict() in ["SUPPORTS", "REFUTES"]:
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
    # parser.add_argument('--split', type=str)
    parser.add_argument("--input_file", type=str)
    parser.add_argument("--max_page", type=int, default=1)
    parser.add_argument("--max_sent", type=int, default=1)
    parser.add_argument("--max_tabs", type=int, default=1)
    parser.add_argument("--split", type=str, default=1)
    parser.add_argument("--all", type=int, default=1)
    args = parser.parse_args()
    # split = args.split

    # page_mrr(args)
    # page_coverage(args)
    # evidence_mrr(args)
    evidence_coverage(args)
