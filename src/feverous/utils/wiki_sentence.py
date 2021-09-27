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

from utils.util import process_text, WikiElement

class WikiSentence(WikiElement):
    def __init__(self, name, sentence, page):
        self.name = name
        self.content = process_text(sentence)
        self.page = page

    def id_repr(self):
        return self.name

    def get_id(self):
        return self.name

    def __str__(self):
        return self.content

    def get_ids(self):
        return [self.name]
