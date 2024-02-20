import json
import os
import unicodedata
from typing import Dict, List

from urllib.parse import unquote
from cleantext import clean


from feverous.database.feverous_db import FeverousDB
from feverous.utils.wiki_page import WikiPage

ALL_TITLES = {}


def clean_title(text: str) -> str:
    text = unquote(text)
    text = clean(
        text.strip(),
        fix_unicode=True,  # fix various unicode errors
        to_ascii=False,  # transliterate to closest ASCII representation
        lower=False,  # lowercase text
        no_line_breaks=False,  # fully strip line breaks as opposed to only normalizing them
        no_urls=True,  # replace all URLs with a special token
        no_emails=False,  # replace all email addresses with a special token
        no_phone_numbers=False,  # replace all phone numbers with a special token
        no_numbers=False,  # replace all numbers with a special token
        no_digits=False,  # replace all digits with a special token
        no_currency_symbols=False,  # replace all currency symbols with a special token
        no_punct=False,  # remove punctuations
        replace_with_url="<URL>",
        replace_with_email="<EMAIL>",
        replace_with_phone_number="<PHONE>",
        replace_with_number="<NUMBER>",
        replace_with_digit="0",
        replace_with_currency_symbol="<CUR>",
        lang="en",
    )
    return text


def get_evidence_text_by_id(id: str, wikipage: WikiPage):
    id_org = id
    id = "_".join(id.split("_")[1:])
    if id.startswith("cell_") or id.startswith("header_cell_"):
        content = wikipage.get_cell_content(id)
    elif id.startswith("item_"):
        content = wikipage.get_item_content(id)
    elif "_caption" in id:
        content = wikipage.get_caption_content(id)
    else:
        if (
            id in wikipage.get_page_items()
        ):  # Filters annotations that are not in the most recent Wikidump (due to additionally removed pages)
            content = str(wikipage.get_page_items()[id])
        else:
            logger.info("Evidence text: {} in {} not found.".format(id, id_org))
            content = ""
    return content


def get_evidence_by_table(evidence: List[str]) -> List[List[str]]:
    """
    Given a list of evidence ids, returns a list of lists, where each list groups all evidence elements for a table (cells and captions).
    @param evidence: A list of evidence ids
    """

    evidence_by_table = {}
    for ev in evidence:
        if "_cell_" in ev:
            table = ev.split("_cell_")[1].split("_")[0]
        elif "_caption_" in ev:
            table = ev.split("_caption_")[1].split("_")[0]
        else:
            continue
        if table in evidence_by_table:
            evidence_by_table[table].append(ev)
        else:
            evidence_by_table[table] = [ev]
    return [list(values) for key, values in evidence_by_table.items()]


def get_evidence_by_page(evidence: List[str]) -> List[List[str]]:
    """
    Given a list of evidence ids, returns a list of lists, where each list groups all evidence elements for a page.
    @param evidence: A list of evidence ids
    """
    evidence_by_page = {}
    for ele in evidence:
        page = ele.split("_")[0]
        if page in evidence_by_page:
            evidence_by_page[page].append(ele)
        else:
            evidence_by_page[page] = [ele]
    return [list(values) for key, values in evidence_by_page.items()]


# def get_wikipage_by_id(id, db):
#     page = id.split('_')[0]
#     page = clean_title(page)
#     page = unicodedata.normalize('NFD', page).strip()
#     # pa = wiki_processor.process_title(page)
#     # print(page)
#     try:
#         lines = db.get_doc_json(page)
#         pa = WikiPage(page, lines)
#     except:
#         traceback.print_exc()
#         print(page)
#         pa = None
#     # print(lines)
#     return pa, page


def get_wikipage_by_id(id: str, db: FeverousDB) -> WikiPage:
    """
    Get a WikiPage object from a page id.
    @param id: id of the Wikipedia article
    @return: WikiPage object
    """

    page = id.split("_")[0]
    page = unicodedata.normalize("NFD", page).strip()
    lines = db.get_doc_json(page)

    if lines == None:
        logger.info(
            "Could not find page in database. Please ensure that the title is formatted correctly. If you using an old version (earlier than 04. June 2021, dowload the train and dev splits again and replace them in the directory accordingly."
        )
    pa = WikiPage(page, lines)
    return pa, page


def calculate_title_to_json_map(input_path: str):
    title_to_json_map = {}
    from utils.wiki_processor import WikiDataProcessor

    wiki_processor = WikiDataProcessor(os.path.join(input_path))
    for page in wiki_processor:
        title_to_json_map[page.title.content] = (wiki_processor.current_file, wiki_processor.current_line)
    return title_to_json_map


class Reader:
    def __init__(self, encoding="utf-8"):
        self.enc = encoding

    def read(self, file):
        with open(file, "r", encoding=self.enc) as f:
            return self.process(f)

    def process(self, f):
        pass


class JSONReader(Reader):
    def process(self, fp):
        return json.load(fp)


class JSONLineReader(Reader):
    def process(self, fp):
        data = []
        for line in fp.readlines():
            data.append(json.loads(line.strip()))
        return data
