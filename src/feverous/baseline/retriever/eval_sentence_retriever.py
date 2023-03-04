import argparse
import json
import unicodedata
from urllib.parse import unquote

from cleantext import clean
from tqdm import tqdm

from feverous.utils.annotation_processor import AnnotationProcessor, EvidenceType
from feverous.utils.util import clean_title


def average(list):
    return float(sum(list) / len(list))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", type=str)
    parser.add_argument("--input_path", type=str)
    parser.add_argument("--max_page", type=int, default=1)
    parser.add_argument("--max_sent", type=int, default=1)
    parser.add_argument("--all", type=int, default=0)
    args = parser.parse_args()
    split = args.split

    # q = 0
    # q_all = 0
    # score = 0
    # score_all = 0
    in_path = "data/{0}.sentences.not_precomputed.p{1}.s{2}.jsonl".format(split, args.max_page, args.max_sent)

    # annotation_processor = AnnotationProcessor(args.input_path)
    # if args.all == 0:
    #     annotation_by_id = {el.get_id(): el for el in annotation_processor if el.has_evidence() and el.get_evidence_type(flat=True) == EvidenceType.SENTENCE}
    # else:
    #     annotation_by_id = {el.get_id(): el for el in annotation_processor if el.has_evidence()}
    #
    # with open(in_path,"r") as f:
    #     for idx,line in enumerate(f):
    #         js = json.loads(line)
    #         id = js['id']
    #         if id not in annotation_by_id:
    #             continue
    #         anno = annotation_by_id[id]
    #         docs_gold = list(set(anno.get_evidence(flat=True)))
    #         docs_predicted =  [t[0] + '_' + t[1].replace('s_', 'sentence_') for t in js['predicted_sentences']]
    #         if anno.get_verdict() in ['Supported', 'Refuted']:
    #             for p in docs_gold:
    #                 q += 1
    #                 if p in docs_predicted:
    #                     score+= (1/(docs_predicted.index(p)+1)) #mean reciprocal rank
    #         else:
    #             for p in docs_gold:
    #                 q_all += 1
    #                 if p in docs_predicted:
    #                     score_all+= (1/(docs_predicted.index(p)+1)) #mean reciprocal rank
    # print(score/q)
    # print(score_all/q_all)

coverage = []
coverage_all = []
# in_path = 'data/annotations/{0}.sentences.not_precomputed.p{1}.s{2}.jsonl'.format(split, args.max_page, args.max_sent)
annotation_processor = AnnotationProcessor("data/{}.jsonl".format(args.split))
if args.all == 0:
    annotation_by_id = {
        el.get_id(): el
        for el in annotation_processor
        if el.has_evidence() and el.get_evidence_type(flat=True) == EvidenceType.SENTENCE
    }
else:
    annotation_by_id = {el.get_id(): el for el in annotation_processor if el.has_evidence()}

with open(in_path, "r") as f:
    for idx, line in enumerate(f):
        js = json.loads(line)
        id = js["id"]
        if id not in annotation_by_id:
            continue
        anno = annotation_by_id[id]
        docs_gold = list(set([t for t in anno.get_evidence(flat=True) if "_sentence_" in t]))
        if len(docs_gold) == 0:
            continue
        # print(docs_gold)
        docs_predicted = [t[0] + "_" + t[1].replace("s_", "sentence_") for t in js["predicted_sentences"][:4]]
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
