#!/usr/bin/env python3
# Copyright 2017-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import os


def get_class(name):
    if name == "tfidf":
        return TfidfDocRanker
    if name == "sqlite":
        return DocDB
    if name == "memory":
        return Simple
    raise RuntimeError("Invalid retriever class: %s" % name)


from .doc_db import DocDB
from .simple import Simple
from .tfidf_doc_ranker import TfidfDocRanker
