import json
import sys
import os
import jsonlines
import traceback
import logging
from tqdm import tqdm
import pickle
import itertools
import linecache
import html
import re

ALL_TITLES = {}


class WikiElement(object):
    def get_ids(self) -> list:
        """Returns list of all ids in that element"""
        pass

    def get_id(self) ->str:
        """Return the specific id of that element"""

    def id_repr(self) -> str:
        """Returns a string representation of all ids in that element"""
        pass

    def __str__(self) -> str:
        """Returns a string representation of the element's content"""
        pass

def process_text(text):
    return text.strip()

def calculate_title_to_json_map(input_path):
    title_to_json_map = {}
    from utils.wiki_processor import WikiDataProcessor
    wiki_processor = WikiDataProcessor(os.path.join(input_path))
    for page in wiki_processor:
        # if page.title.name in title_to_json_map:
        title_to_json_map[page.title.content] = (wiki_processor.current_file, wiki_processor.current_line)
        # else:
        #     title_to_json_map[page.title.name] = (wiki_processor.current_file, )
    return title_to_json_map


class Reader:
    def __init__(self,encoding="utf-8"):
        self.enc = encoding

    def read(self,file):
        with open(file,"r",encoding = self.enc) as f:
            return self.process(f)

    def process(self,f):
        pass


class JSONReader(Reader):
    def process(self,fp):
        return json.load(fp)


class JSONLineReader(Reader):
    def process(self,fp):
        data = []
        for line in fp.readlines():
            data.append(json.loads(line.strip()))
        return data
