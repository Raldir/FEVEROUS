#!/usr/bin/env python3
# Copyright 2017-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
"""A script to build the tf-idf document matrices for retrieval."""

import argparse
import logging
import math

from feverous.baseline.drqa import tokenizers
from feverous.baseline.drqa.retriever import TfidfDocRanker
from feverous.baseline.drqascripts.build_tfidf import get_count_matrix, get_doc_freqs, get_tfidf_matrix

logger = logging.getLogger()


class OnlineTfidfDocRanker(TfidfDocRanker):
    """Loads a pre-weighted inverted index of token/document terms.
    Scores new queries by taking sparse dot products.
    """

    def __init__(self, lines, ngram, hash_size, tokenizer, num_workers, freqs=None, strict=True):
        """
        Args:
            tfidf_path: path to saved model file
            strict: fail on empty queries or continue (and return empty result)
        """
        # Load from disk
        logging.info("Counting words...")
        count_matrix, doc_dict = get_count_matrix("memory", {"lines": lines}, ngram, hash_size, tokenizer, num_workers)

        logger.info("Making tfidf vectors...")
        tfidf = get_tfidf_matrix(count_matrix)

        if freqs is None:
            logger.info("Getting word-doc frequencies...")
            freqs = get_doc_freqs(count_matrix)

        metadata = {
            "doc_freqs": freqs,
            "tokenizer": tokenizer,
            "hash_size": hash_size,
            "ngram": ngram,
            "doc_dict": doc_dict,
        }

        self.doc_mat = tfidf
        self.ngrams = metadata["ngram"]
        self.hash_size = metadata["hash_size"]
        self.tokenizer = tokenizers.get_class(metadata["tokenizer"])()
        self.doc_freqs = metadata["doc_freqs"].squeeze()
        self.doc_dict = metadata["doc_dict"]
        self.num_docs = len(self.doc_dict[0])
        self.strict = strict