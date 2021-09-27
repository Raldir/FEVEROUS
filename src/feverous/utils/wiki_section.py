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


class WikiSection(WikiElement):
    def __init__(self, name, section, page):
        self.content = section['value']
        self.level = section['level']
        self.name = name
        self.page = page

    def id_repr(self):
        return self.name

    def get_id(self):
        return self.name

    def get_ids(self):
        return [self.name]

    def __str__(self):
        return self.content

    def get_level(self):
        return self.level
