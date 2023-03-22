import argparse
import json
import unicodedata
from multiprocessing.pool import ThreadPool

import numpy as np
from tqdm import tqdm

from feverous.baseline.drqa.retriever import utils
from feverous.baseline.drqa.retriever.doc_db import DocDB
from feverous.baseline.drqascripts.build_tfidf_lines import OnlineTfidfDocRanker
from feverous.utils.log_helper import LogHelper
from feverous.utils.util import JSONLineReader
from feverous.utils.wiki_page import WikiPage


def tf_idf_sim(claim, lines, max_sent, ngram, hash_size, tokenizer, num_workers, freqs=None):
    tfidf = OnlineTfidfDocRanker(
        [line["sentence"] for line in lines], ngram, hash_size, tokenizer, num_workers, freqs=freqs
    )
    line_ids, scores = tfidf.closest_docs(claim, max_sent)
    ret_lines = []
    for idx, line in enumerate(line_ids):
        ret_lines.append(lines[line])
        ret_lines[-1]["score"] = scores[idx]
    return ret_lines


def tf_idf_claim(line, db, max_page, max_sent, ngram, hash_size, tokenizer, num_workers, doc_freqs):
    if "predicted_pages" in line:
        sorted_p = list(sorted(line["predicted_pages"], reverse=True, key=lambda elem: elem[1]))

        pages = [p[0] for p in sorted_p[:max_page]]
        p_lines = []
        for page in pages:
            page = unicodedata.normalize("NFD", page)
            try:
                lines = json.loads(db.get_doc_json(page))
            except:
                continue
            current_page = WikiPage(page, lines)
            all_sentences = current_page.get_sentences()
            sentences = [str(sent) for sent in all_sentences[: len(all_sentences)]]
            sentence_ids = [sent.get_id() for sent in all_sentences[: len(all_sentences)]]

            p_lines.extend(zip(sentences, [page] * len(lines), sentence_ids))

        lines = []
        for p_line in p_lines:
            lines.append({"sentence": p_line[0], "page": p_line[1], "line_on_page": p_line[2]})

        scores = tf_idf_sim(line["claim"], lines, max_sent, ngram, hash_size, tokenizer, num_workers, freqs=doc_freqs)

        line["predicted_sentences"] = [(s["page"], s["line_on_page"]) for s in scores]
    return line


def str2bool(v):
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


def sentence_tfidf_retrieval(
    db: str,
    max_page: int,
    max_sent: int,
    data_path: str,
    split: str,
    use_precomputed: bool = True,
    ngram: int = 2,
    hash_size: int = int(np.math.pow(2, 24)),
    tokenizer: str = "simple",
    num_workers: int = None,
    model: str = "data/index/feverous-wiki-docs-tfidf-ngram=2-hash=16777216-tokenizer=simple.npz",
) -> None:
    doc_freqs = None
    if use_precomputed:
        _, metadata = utils.load_sparse_csr(model)
        doc_freqs = metadata["doc_freqs"].squeeze()

    db = DocDB(db)

    jlr = JSONLineReader()

    with open("{0}/{1}.pages.p{2}.jsonl".format(data_path, split, max_page), "r") as f, open(
        "{0}/{1}.sentences.{4}.p{2}.s{3}.jsonl".format(
            data_path,
            split,
            max_page,
            max_sent,
            "precomputed" if use_precomputed else "not_precomputed",
        ),
        "w+",
    ) as out_file:
        lines = jlr.process(f)

        for line in tqdm(lines):
            line = tf_idf_claim(line, db, max_page, max_sent, ngram, hash_size, tokenizer, num_workers, doc_freqs)
            out_file.write(json.dumps(line) + "\n")


if __name__ == "__main__":
    LogHelper.setup()
    LogHelper.get_logger(__name__)

    parser = argparse.ArgumentParser()

    parser.add_argument("--db", type=str, help="/path/to/saved/db.db")
    parser.add_argument(
        "--model",
        type=str,
        default="data/index/feverous-wiki-docs-tfidf-ngram=2-hash=16777216-tokenizer=simple.npz",
        help="/path/to/saved/db.db",
    )
    parser.add_argument("--max_page", type=int)
    parser.add_argument("--max_sent", type=int)
    parser.add_argument("--data_path", type=str)
    parser.add_argument("--use_precomputed", type=str2bool, default=True)
    parser.add_argument("--split", type=str)
    parser.add_argument(
        "--ngram", type=int, default=2, help=("Use up to N-size n-grams " "(e.g. 2 = unigrams + bigrams)")
    )
    parser.add_argument(
        "--hash-size", type=int, default=int(np.math.pow(2, 24)), help="Number of buckets to use for hashing ngrams"
    )
    parser.add_argument(
        "--tokenizer",
        type=str,
        default="simple",
        help=("String option specifying tokenizer type to use " "(e.g. 'corenlp')"),
    )

    parser.add_argument("--num-workers", type=int, default=None, help="Number of CPU processes (for tokenizing, etc)")
    args = parser.parse_args()

    sentence_tfidf_retrieval(
        args.db,
        args.max_page,
        args.max_sent,
        args.data_path,
        args.split,
        args.use_precomputed,
        args.ngram,
        args.hash_size,
        args.tokenizer,
        args.num_workers,
        args.model,
    )
