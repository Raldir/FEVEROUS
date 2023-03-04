import argparse
import json
import sys
import unicodedata
from urllib.parse import unquote

from cleantext import clean
from tqdm import tqdm

from feverous.utils.annotation_processor import AnnotationProcessor
from feverous.utils.util import clean_title


def average(list):
    return float(sum(list) / len(list))


def page_coverage(args):
    print("Page coverage...")
    coverage = []
    coverage_all = []
    in_path = "data/{}.jsonl".format(args.split)
    annotation_processor = AnnotationProcessor(in_path)
    annotation_by_id = {el.get_id(): el for el in annotation_processor}

    with open("data/{1}.pages.p{2}.jsonl".format(args.input_path, split, k), "r") as f:
        for idx, line in enumerate(f):
            js = json.loads(line)
            id = js["id"]
            anno = annotation_by_id[id]
            docs_gold = list(set([clean_title(t) for t in anno.get_titles(flat=True)]))
            docs_predicted = [clean_title(t[0]) for t in js["predicted_pages"][:3]]
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
    parser.add_argument("--anno_path", type=str)
    parser.add_argument("--split", type=str)
    parser.add_argument("--input_path", type=str)
    parser.add_argument("--mode", type=str)
    parser.add_argument("--count", type=int, default=1)
    args = parser.parse_args()
    split = args.split
    k = args.count

    page_coverage(args)

    sys.exit()

    q = 0
    q_all = 0
    score = 0
    score_all = 0
    in_path = "data/{0}.jsonl".format(split)
    annotation_processor = AnnotationProcessor(in_path)
    annotation_by_id = {el.get_id(): el for el in annotation_processor}

    with open("data/{1}.pages.p{2}.jsonl".format(split, k), "r") as f:
        for idx, line in enumerate(f):
            js = json.loads(line)
            id = js["id"]
            anno = annotation_by_id[id]
            docs_gold = list(set(anno.get_titles(flat=True)))
            docs_predicted = [t[0] for t in js["predicted_pages"]]
            if anno.get_verdict() in ["SUPPORTS", "REFUTES"]:
                for p in docs_gold:
                    q += 1
                    if p in docs_predicted:
                        score += 1 / (docs_predicted.index(p) + 1)  # mean reciprocal rank
            else:
                for p in docs_gold:
                    q_all += 1
                    if p in docs_predicted:
                        score_all += 1 / (docs_predicted.index(p) + 1)  # mean reciprocal rank
    print(score / q)
    print(score_all / q_all)
