#!/usr/bin/env python3

#Adapted from https://github.com/facebookresearch/DrQA/blob/master/scripts/retriever/build_db.py
# Copyright 2017-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
"""A script to read in and store documents in a sqlite database."""

import argparse
import sqlite3
import json
import os
import importlib.util

from multiprocessing import Pool as ProcessPool
from tqdm import tqdm
from baseline.drqa.retriever import utils
from utils.log_helper import LogHelper
from utils.wiki_page import WikiPage
from multiprocessing.pool import Pool
from database.feverous_db import FeverousDB

LogHelper.setup()
logger = LogHelper.get_logger("DrQA BuildDB")

# ------------------------------------------------------------------------------
# Preprocessing Function.
# ------------------------------------------------------------------------------
wiki_processor = None

PREPROCESS_FN = None
def init(filename):
    global PREPROCESS_FN
    if filename:
        PREPROCESS_FN = import_module(filename).preprocess


def import_module(filename):
    """Import a module given a full path to the file."""
    spec = importlib.util.spec_from_file_location('doc_filter', filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ------------------------------------------------------------------------------
# Store corpus.
# ------------------------------------------------------------------------------


def iter_files(path):
    """Walk through all files located under a root path."""
    if os.path.isfile(path):
        yield path
    elif os.path.isdir(path):
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                yield os.path.join(dirpath, f)
    else:
        raise RuntimeError('Path %s is invalid' % path)

def get_contents_sentence(entry):
    all_sentences = entry.get_sentences()
    intro_sents_index = entry.page_order.index('section_0') if 'section_0' in entry.page_order else len(entry.page_order) -1
    sentences_in_intro = [sent for sent in all_sentences if entry.page_order.index(sent.get_id()) < intro_sents_index]
    text = ' '.join([str(s) for s in sentences_in_intro])


    lines = '[SEP]'.join([s.get_id() + '\t' + str(s) for s in all_sentences])

    document = (utils.normalize(entry.title.content), text, lines)
    del all_sentences
    return document


def store_contents(wiki_processor, save_path, preprocess, num_workers=None):
    """Preprocess and store a corpus of documents in sqlite.

    Args:
        data_path: Root path to directory (or directory of directories) of files
          containing json encoded documents (must have `id` and `text` fields).
        save_path: Path to output sqlite db.
        preprocess: Path to file defining a custom `preprocess` function. Takes
          in and outputs a structured doc.
        num_workers: Number of parallel processes to use when reading docs.
    """
    if os.path.isfile(save_path):
        raise RuntimeError('%s already exists! Not overwriting.' % save_path)

    logger.info('Reading into database...')
    conn = sqlite3.connect(save_path)
    c = conn.cursor()
    c.execute("CREATE TABLE documents (id PRIMARY KEY, text, lines);")



    count = 0
    # with Pool(4) as p:
    #     for num, doc in enumerate(p.imap_unordered(get_contents, wiki_processor)):
    docs = db.get_doc_ids()
    for entry in tqdm(docs):
        page =  WikiPage(entry, db.get_doc_json(entry))
        doc = get_contents_sentence(page)
        count += 1
        c.execute("INSERT INTO documents VALUES (?,?,?)", doc)
        del doc
        if (count + 1) % 100000 == 0:
            conn.commit()
            # if (count + 1) % 1000 == 0:
            #     logger.info('Committing...')
            #     conn.commit()
    conn.commit()
    logger.info('Read %d docs.' % count)
    logger.info('Committing...')
    conn.commit()
    conn.close()



# ------------------------------------------------------------------------------
# Main.
# ------------------------------------------------------------------------------


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--db_path', type=str, help='/path/to/data')
    parser.add_argument('--save_path', type=str, help='/path/to/saved/db.db')
    parser.add_argument('--mode', type=str, help='intro')#Specify if only the introduction section should be considered
    parser.add_argument('--preprocess', type=str, default=None,
                        help=('File path to a python module that defines '
                              'a `preprocess` function'))
    parser.add_argument('--num-workers', type=int, default=None,
                        help='Number of CPU processes (for tokenizing, etc)')

    args = parser.parse_args()

    save_dir = os.path.dirname(args.save_path)
    if not os.path.exists(save_dir):
        logger.info("Save directory doesn't exist. Making {0}".format(save_dir))
        os.makedirs(save_dir)

    db =  FeverousDB(args.db_path)

    store_contents(
        db, args.save_path, args.preprocess, args.num_workers
    )
