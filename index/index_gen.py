#Call this script from ../FEVEROUS directory
from feverous.database.feverous_db import FeverousDB
from feverous.utils.wiki_window import *
from feverous.utils.wiki_row import *
import numpy as np
import pickle
import sqlite3
from pathlib import Path
import argparse
import pandas as pd
import blink.main_dense as main_dense
import blink.ner as NER

def get_page_ids(page_ids_path, db_path):
    my_file = Path(page_ids_path)
    if my_file.is_file():
        #ids already exists
        page_ids = np.load(page_ids_path, allow_pickle=True)
        return page_ids
    #page_ids doesnot exists
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("SELECT id FROM wiki;")
    page_ids = cur.fetchall()
    page_ids = np.asarray(page_ids).squeeze()
    with open(page_ids_path,"wb") as file:
        pickle.dump(page_ids,file)
    return page_ids

def build_index(model_args, worker_page_ids, db_path):
    model = main_dense.load_models(model_args, logger=None)
    ner_model = NER.get_model()
    db =  FeverousDB(db_path)
    worker_index = {}
    for page_id in worker_page_ids:
        page_json = db.get_doc_json(page_id)
        wiki_page = WikiPage(page_id, page_json)
        #Index all windows in the page
        window_obj = wiki_window(wiki_page)
        all_windows = window_obj.get_all_windows()
        for window_id in all_windows.keys():
            text = window_obj.get_window_content_and_context(window_id)
            annotated = main_dense._annotate(ner_model,[text])
            _, _, _, _, _, predictions, _, = main_dense.run(args, None, *model, test_data=annotated)
            entities = [pred_ents[0] for pred_ents in predictions]
            for entity in entities:
                if entity not in worker_index.keys():
                    worker_index[entity] = []
                worker_index[entity].append(window_id)
        #Index all rows in the page
        row_obj = wiki_row(wiki_page)
        all_rows = row_obj.get_all_rows()
        for row_id in all_rows.keys():
            text = row_obj.get_row_content_and_context(row_id)
            #Use here ELQ
            #TODO: tomorrow

    pass

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--page_ids_path", type=str, help= "Contains path of page_ids file")
    parser.add_argument("--db_path", type=str, help= "contains database path")
    parser.add_argument("--model_path", type=str, help="path to BLINK models")
    parser.add_argument("--num_threads", type=int)

    args = parser.parse_args()

    page_ids = get_page_ids(args.page_ids_path, args.db_path)
    
    models_path = args.model_path
    config = {
        "test_entities": None,
        "test_mentions": None,
        "interactive": False,
        "top_k": 10,
        "biencoder_model": models_path+"biencoder_wiki_large.bin",
        "biencoder_config": models_path+"biencoder_wiki_large.json",
        "entity_catalogue": models_path+"entity.jsonl",
        "entity_encoding": models_path+"all_entities_large.t7",
        "crossencoder_model": models_path+"crossencoder_wiki_large.bin",
        "crossencoder_config": models_path+"crossencoder_wiki_large.json",
        "fast": False, # set this to be true if speed is a concern
        "output_path": "logs/" # logging directory
    }
    model_args = argparse.Namespace(**config)
    pass