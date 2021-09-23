from database.feverous_db import FeverousDB
from utils.wiki_page import WikiPage
import jsonlines
import json
import unicodedata
from cleantext import clean
import unicodedata
from urllib.parse import unquote

from utils.log_helper import LogHelper

LogHelper.setup()
logger = LogHelper.get_logger(__name__)

DB = None



def clean_title(text):
    text = unquote(text)
    text = clean(text.strip(),fix_unicode=True,               # fix various unicode errors
    to_ascii=False,                  # transliterate to closest ASCII representation
    lower=False,                     # lowercase text
    no_line_breaks=False,           # fully strip line breaks as opposed to only normalizing them
    no_urls=True,                  # replace all URLs with a special token
    no_emails=False,                # replace all email addresses with a special token
    no_phone_numbers=False,         # replace all phone numbers with a special token
    no_numbers=False,               # replace all numbers with a special token
    no_digits=False,                # replace all digits with a special token
    no_currency_symbols=False,      # replace all currency symbols with a special token
    no_punct=False,                 # remove punctuations
    replace_with_url="<URL>",
    replace_with_email="<EMAIL>",
    replace_with_phone_number="<PHONE>",
    replace_with_number="<NUMBER>",
    replace_with_digit="0",
    replace_with_currency_symbol="<CUR>",
    lang="en"                       # set to 'de' for German special handling
    )
    return text


def init_db(wiki_path):
    global DB
    DB = FeverousDB(wiki_path)

def get_wikipage_by_id(id):
    page = id.split('_')[0]
    # page = clean_title(page) legacy function used for old train/dev set. Not needed with current data version.
    page = unicodedata.normalize('NFD', page).strip()
    lines = DB.get_doc_json(page)

    if lines == None:
        logger.info('Could not find page in database. Please ensure that the title is formatted correctly. If you using an old version (earlier than 04. June 2021, dowload the train and dev splits again and replace them in the directory accordingly.')
    pa = WikiPage(page, lines)
    return pa

def get_evidence_text_by_id(id, wikipage):
    id_org = id
    id = '_'.join(id.split('_')[1:])
    if id.startswith('cell_') or id.startswith('header_cell_'):
        content = wikipage.get_cell_content(id)
    elif id.startswith('item_'):
        content = wikipage.get_item_content(id)
    elif '_caption' in id:
        content = wikipage.get_caption_content(id)
    else:
        if id in wikipage.get_page_items(): #Filters annotations that are not in the most recent Wikidump (due to additionally removed pages)
            content =  str(wikipage.get_page_items()[id])
        else:
            logger.info('Evidence text: {} in {} not found.'.format(id, id_org))
            content = ''
    return content

def get_evidence_by_table(evidence):
    evidence_by_table = {}
    for ev in evidence:
        if '_cell_' in ev:
            table = ev.split("_cell_")[1].split('_')[0]
        elif '_caption_' in ev:
            table = ev.split("_caption_")[1].split('_')[0]
        else:
            continue
        if table in evidence_by_table:
            evidence_by_table[table].append(ev)
        else:
            evidence_by_table[table] = [ev]
    return [list(values) for key, values in evidence_by_table.items()]

def get_evidence_by_page(evidence):
    evidence_by_page = {}
    for ele in evidence:
        page = ele.split("_")[0]
        if page in evidence_by_page:
            evidence_by_page[page].append(ele)
        else:
            evidence_by_page[page] = [ele]
    return [list(values) for key, values in evidence_by_page.items()]


def calculate_header_type(header_content):
    real_count = 0
    text_count  = 0
    for ele in header_content:
        if ele.replace('.','',1).isdigit():
            real_count+=1
        else:
            text_count+=1
    if real_count >= text_count:
        return 'real'
    else:
        return 'text'

def group_evidence_by_header(table):
    cell_headers = {}
    for ele in table:
        if 'header_cell_' in ele:
            continue #Ignore evidence header cells for now, probably an exception anyways
        else:
            wiki_page = get_wikipage_by_id(ele)
            cell_header_ele = [ele.split('_')[0] + '_' +  el.get_id().replace('hc_', 'header_cell_') for el in wiki_page.get_context('_'.join(ele.split('_')[1:])) if "header_cell_" in el.get_id()]
            for head in cell_header_ele:
                if head in cell_headers:
                    cell_headers[head].append(get_evidence_text_by_id(ele, wiki_page))
                else:
                    cell_headers[head] =  [get_evidence_text_by_id(ele, wiki_page)]
    cell_headers_type = {}
    for ele, value in cell_headers.items():
        cell_headers[ele] = set(value)

    for key,item in cell_headers.items():
        cell_headers_type[key] = calculate_header_type(item)

    return cell_headers, cell_headers_type


def prepare_input_schlichtkrull(annotation, gold):
    sequence = [annotation.claim]
    if gold:
        evidence_by_page = get_evidence_by_page(annotation.flat_evidence)
    else:
        evidence_by_page = get_evidence_by_page(annotation.predicted_evidence)
    for ele in evidence_by_page:
        for evid in ele:
            wiki_page = get_wikipage_by_id(evid)
            if '_sentence_' in evid:
                sequence.append('. '.join([str(context) for context in wiki_page.get_context(evid)[1:]]) + ' ' + get_evidence_text_by_id(evid, wiki_page))
        tables = get_evidence_by_table(ele)

        for table in tables:
            sequence += linearize_cell_evidence(table)

    # print(sequence)
    return ' </s> '.join(sequence)


def linearize_cell_evidence(table):
    context = []
    caption_id = [ele for ele in table if '_caption_' in ele]
    context.append(table[0].split('_')[0])
    if len(caption_id) > 0:
        wiki_page = get_wikipage_by_id(caption_id[0])
        context.append(get_evidence_text_by_id(caption_id[0], wiki_page))
    cell_headers, cell_headers_type = group_evidence_by_header(table)
    for key, values in cell_headers.items():
        wiki_page = get_wikipage_by_id(key)
        lin = ''
        key_text = get_evidence_text_by_id(key, wiki_page)
        # print(key, key_text, values)
        for i, value in enumerate(values):
            lin += key_text.split('[H] ')[1].strip() + ' is ' + value #+ ' : ' + cell_headers_type[key]
            if i + 1 < len(values):
                lin += ' ; '
            else:
                lin += '.'

        context.append(lin)
    return context


def prepare_input(annotation, model_name, gold=False):
    if model_name == 'tabert':
        return prepare_tabert_input(annotation, gold)
    elif model_name == 'schlichtkrull':
        return prepare_input_schlichtkrull(annotation, gold)
