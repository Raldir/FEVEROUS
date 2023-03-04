#!/usr/bin/env python3

# Adapted from https://github.com/facebookresearch/DrQA/blob/master/scripts/retriever/build_db.py
# Copyright 2017-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

"""A script to build the tf-idf document matrices for retrieval."""

import os

from feverous.baseline.drqascripts.build_tfidf import *


def build_tfidf(
    db_path: str,
    out_dir: str,
    ngram: int = 2,
    hash_size: int = int(math.pow(2, 24)),
    tokenizer: str = "simple",
    num_workers: int = None,
) -> None:
    logging.info("Counting words...")
    count_matrix, doc_dict = get_count_matrix("sqlite", {"db_path": db_path}, ngram, hash_size, tokenizer, num_workers)

    logger.info("Making tfidf vectors...")
    tfidf = get_tfidf_matrix(count_matrix)

    logger.info("Getting word-doc frequencies...")
    freqs = get_doc_freqs(count_matrix)

    basename = os.path.splitext(os.path.basename(db_path))[0]
    basename += "-tfidf-ngram=%d-hash=%d-tokenizer=%s" % (ngram, hash_size, tokenizer)

    if not os.path.exists(out_dir):
        logger.info("Creating data directory")
        os.makedirs(out_dir)

    filename = os.path.join(out_dir, basename)

    logger.info("Saving to %s.npz" % filename)
    metadata = {
        "doc_freqs": freqs,
        "tokenizer": tokenizer,
        "hash_size": hash_size,
        "ngram": ngram,
        "doc_dict": doc_dict,
    }

    retriever.utils.save_sparse_csr(filename, tfidf, metadata)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db_path", type=str, default=None, help="Path to sqlite db holding document texts")
    parser.add_argument("--out_dir", type=str, default=None, help="Directory for saving output files")
    parser.add_argument(
        "--ngram", type=int, default=2, help=("Use up to N-size n-grams " "(e.g. 2 = unigrams + bigrams)")
    )
    parser.add_argument(
        "--hash-size", type=int, default=int(math.pow(2, 24)), help="Number of buckets to use for hashing ngrams"  # 24
    )
    parser.add_argument(
        "--tokenizer",
        type=str,
        default="simple",
        help=("String option specifying tokenizer type to use " "(e.g. 'corenlp')"),
    )
    parser.add_argument("--num-workers", type=int, default=None, help="Number of CPU processes (for tokenizing, etc)")
    args = parser.parse_args()

    build_tfidf(args.db_path, args.out_dir, args.ngram, args.hash_size, args.tokenizer, args.num_workers)
