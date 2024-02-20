import json
import linecache
import os
import pickle
import traceback


import jsonlines
from tqdm import tqdm

from feverous.utils.log_helper import LogHelper
from feverous.utils.wiki_page import WikiPage

LogHelper.setup()
logger = LogHelper.get_logger(__name__)


class WikiDataProcessor:
    def __init__(self, input_path, condition=None, filter=None, mode=None):
        """
        Args:
        condition: only get titles that are included in condition (list)
        filter: Filter for specific type of data, e.g. sentence_/table_ etc.
        mode: Specify mode from [intro, ..] to get special processed parts of page
        """
        self.titles = set([])
        self.input_path = input_path
        self.file_paths = self.get_json_files()
        self.pages = self.process_pages(condition, filter, mode)
        self.open_json = None
        self.filter = filter
        self.condition = condition
        self.mode = mode
        self.title_to_json_map = None
        # Do not use these in multithreaded mode!
        self.current_data = None
        self.current_file = None
        self.current_line = None

    def __iter__(self):
        return self.pages

    def __next__(self):
        return next(self.pages)

    def get_title_to_json_map(self, input_path):
        if os.path.isfile(os.path.join(input_path, "title_to_json_map.p")):
            title_to_json_map = pickle.load(open(os.path.join(input_path, "title_to_json_map.p"), "rb"))
        else:
            title_to_json_map = calculate_title_to_json_map(os.path.join(input_path))
            pickle.dump(title_to_json_map, open(os.path.join(input_path, "title_to_json_map.p"), "wb"))

        return title_to_json_map

    def process_pages(self, condition, filter, mode):
        for _, file in enumerate(tqdm(self.file_paths)):
            self.current_file = file
            with jsonlines.open(file) as f:
                for i, line in enumerate(f.iter()):
                    self.current_line = i
                    data = self.unescape_dict(line)
                    title = data["title"]
                    if len(data.keys()) <= 2:
                        continue
                    if title in self.titles:
                        continue
                    if condition != None:
                        if title in condition:
                            self.titles.add(title)
                            yield WikiPage(title, data, filter, mode)
                    else:
                        self.titles.add(title)
                        yield WikiPage(title, data, filter, mode)

    def process_json(self, file):
        self.current_file = file
        with jsonlines.open(file) as f:
            for i, line in enumerate(f.iter()):
                self.current_line = i
                line = self.unescape_dict(line)
                title = line["title"]
                if title in self.titles:
                    continue
                if len(line.keys()) <= 2:
                    continue
                self.titles.add(title)
                yield WikiPage(title, line, self.filter, self.mode)

    def process_title(self, title):
        if self.title_to_json_map == None:
            self.title_to_json_map = self.get_title_to_json_map(self.input_path)
        try:
            file, line = list(self.title_to_json_map[title])
        except Exception:
            traceback.print_exc()
            logger.info("Title", title)
            return None
        line_json = json.loads(linecache.getline(file, line + 1))
        return WikiPage(line_json["title"], line_json)

    def get_json_files(self):
        file_paths = []
        for root, dirs, files in os.walk(self.input_path):
            for file in files:
                if file.endswith(".jsonl"):
                    file_paths.append(os.path.join(root, file))
        return file_paths

    def read_json_files(self):
        for i, json_file in enumerate(tqdm(self.get_json_files())):
            with jsonlines.open(json_file) as f:
                for i, line in enumerate(f.iter()):
                    title = line["title"]
                    if title in self.titles:
                        logger.info(
                            "Title already in titles. Unexpected behavior occured. Please consider reporting this issue at https://github.com/Raldir/FEVEROUS"
                        )
                        # continue
                    if len(line.keys()) <= 2:
                        logger.info(line)
                        logger.info(
                            "Not 2 keys??? Unexpected behavior occured. Please consider reporting this issue at https://github.com/Raldir/FEVEROUS"
                        )
                        continue
                    self.titles.add(title)
                    yield (title, line)
