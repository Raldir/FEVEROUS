import argparse
import json
from multiprocessing.pool import ThreadPool

from baseline.drqa.retriever import utils
from utils.log_helper import LogHelper
from tqdm import tqdm
import numpy as np

from baseline.drqascripts.build_tfidf_lines import OnlineTfidfDocRanker
from baseline.drqa.retriever.doc_db import DocDB
from utils.wiki_page import WikiPage
from utils.util import JSONLineReader
import unicodedata



def tf_idf_sim(claim, lines,freqs=None):
    tfidf = OnlineTfidfDocRanker(args,[line["sentence"] for line in lines],freqs)
    line_ids,scores = tfidf.closest_docs(claim,args.max_sent)
    ret_lines = []
    for idx,line in enumerate(line_ids):
        ret_lines.append(lines[line])
        ret_lines[-1]["score"] = scores[idx]
    return ret_lines



def tf_idf_claim(line):
    if 'predicted_pages' in line:
        sorted_p = list(sorted(line['predicted_pages'], reverse=True, key=lambda elem: elem[1]))

        pages = [p[0] for p in sorted_p[:args.max_page]]
        p_lines = []
        for page in pages:
            page = unicodedata.normalize('NFD', page)
            # lines = db.get_doc_lines(page)
            try:
                lines = json.loads(db.get_doc_json(page))
            except:
                continue
            current_page = WikiPage(page, lines)
            all_sentences = current_page.get_sentences()
            sentences = [str(sent) for sent in all_sentences[:len(all_sentences)]]
            sentence_ids = [sent.get_id() for sent in all_sentences[:len(all_sentences)]]
            # lines = [line.split("\t")[1] if len(line.split("\t")[1]) > 1 else "" for line in
            #          lines.split("\n")]
            # lines = [line.split('\t')[1] for i,line in enumerate(lines.split('[SEP]'))]

            p_lines.extend(zip(sentences, [page] * len(lines), sentence_ids))

        lines = []
        for p_line in p_lines:
            lines.append({
                "sentence": p_line[0],
                "page": p_line[1],
                "line_on_page": p_line[2]
            })

        scores = tf_idf_sim(line["claim"], lines, doc_freqs)

        line["predicted_sentences"] = [(s["page"], s["line_on_page"]) for s in scores]
    return line


def tf_idf_claims_batch(lines):
    with ThreadPool(args.num_workers) as threads:
        results = threads.map(tf_idf_claim, lines)
    return results

def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

if __name__ == "__main__":
    LogHelper.setup()
    LogHelper.get_logger(__name__)

    parser = argparse.ArgumentParser()


    parser.add_argument('--db', type=str, help='/path/to/saved/db.db')
    parser.add_argument('--model', type=str, help='/path/to/saved/db.db')
    parser.add_argument('--in_file', type=str, help='/path/to/saved/db.db')
    parser.add_argument('--max_page',type=int)
    parser.add_argument('--max_sent',type=int)
    parser.add_argument('--data_path',type=str)
    parser.add_argument('--use_precomputed', type=str2bool, default=True)
    parser.add_argument('--split', type=str)
    parser.add_argument('--ngram', type=int, default=2,
                        help=('Use up to N-size n-grams '
                              '(e.g. 2 = unigrams + bigrams)'))
    parser.add_argument('--hash-size', type=int, default=int(np.math.pow(2, 24)),
                        help='Number of buckets to use for hashing ngrams')
    parser.add_argument('--tokenizer', type=str, default='simple',
                        help=("String option specifying tokenizer type to use "
                              "(e.g. 'corenlp')"))

    parser.add_argument('--num-workers', type=int, default=None,
                        help='Number of CPU processes (for tokenizing, etc)')
    args = parser.parse_args()
    doc_freqs=None
    if args.use_precomputed:
        _, metadata = utils.load_sparse_csr(args.model)
        doc_freqs = metadata['doc_freqs'].squeeze()

    db = DocDB(args.db)

    # print(db.get_doc_ids())

    jlr = JSONLineReader()

    with open("{0}/{1}.pages.p{2}.jsonl".format(args.data_path, args.split, args.max_page),"r") as f, open("{0}/{1}.sentences.{4}.p{2}.s{3}.jsonl".format(args.data_path, args.split, args.max_page, args.max_sent,"precomputed" if args.use_precomputed else "not_precomputed"), "w+") as out_file:
        lines = jlr.process(f)
        #lines = tf_idf_claims_batch(lines)

        for line in tqdm(lines):
            line = tf_idf_claim(line)
            out_file.write(json.dumps(line) + "\n")
