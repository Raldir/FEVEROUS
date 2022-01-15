#Call this script from ../FEVEROUS directory
from feverous.database.feverous_db import FeverousDB
from feverous.utils.wiki_window import *
from feverous.utils.wiki_row import *
import threading
import numpy as np
import pickle
import sqlite3
from pathlib import Path
import argparse
import pandas as pd
import blink.main_dense as blink_main_dense
import elq.main_dense as elq_main_dense
import blink.ner as NER
from tqdm import tqdm
import time
import traceback
import logging
import random


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


def build_index(worker_page_ids, db_path, models_path, id, idx_path):
    print("Worker",i, "started", sep=" ")
    global worker_output
    pages_not_indexed = 0
    evd_not_indexed = 0
    #BLINK Model Initialization
    print("Worker",i, "loading BLINK model", sep=" ")
    start = time.time()
    blink_config = {
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
        "fast": True, # set this to be true if speed is a concern
        "output_path": "logs/" # logging directory
    }
    blink_model_args = argparse.Namespace(**blink_config)
    ner_model = NER.get_model()
    print("Flair Loaded!!!")
    blink_model = blink_main_dense.load_models(blink_model_args, logger=None)
    print("Worker",i, "Done loading BLINK model and took ",time.time()-start,"time" ,sep=" ")

    db =  FeverousDB(db_path)
    worker_id = "/worker1_"
    num = 0
    for batch_start in range(0,len(worker_page_ids),batch_size):
        worker_index = {}
        all_evidence_content_context = []
        evidence_ids = []
        batch = worker_page_ids[batch_start:min(len(worker_page_ids),batch_start+batch_size)]
        for page_id in tqdm(batch):
            page_json = db.get_doc_json(page_id)
            wiki_page = WikiPage(page_id, page_json)
            #Index all windows in the page
            window_obj = wiki_window(wiki_page)
            row_obj = wiki_row(wiki_page)
            all_window_ids = window_obj.get_all_windows()
            all_row_ids = row_obj.get_all_rows()
            all_evidence_content_context.extend(window_obj.get_all_content_context())
            all_evidence_content_context.extend(row_obj.get_all_content_context())
            for id in all_window_ids:
                evidence_ids.append("window_"+id)
            for id in all_row_ids:
                evidence_ids.append("row_"+id)
        
        per_evidence_ent_density = dict.fromkeys(evidence_ids, 0)
        start = time.time()
        annotated = blink_main_dense._annotate(ner_model,all_evidence_content_context)
        print(len(annotated))
        print("Time took for Flair: ", time.time()-start)
        start = time.time()
        index_to_id = {}
        id_to_index = {}
        for id in evidence_ids:
            index_to_id[len(index_to_id)] = id
            id_to_index[id] = len(index_to_id)-1
        for ent in annotated:
            per_evidence_ent_density[index_to_id[ent["sent_idx"]]] += 1
        try:
            _, _, _, _, _, predictions, _,not_indexed = blink_main_dense.run(blink_model_args, None, *blink_model, test_data=annotated,evd_not_indexed=evd_not_indexed, logger_evd = logger)
            print("Time took for BLINK ", time.time()-start)
            index = 0
            for id in evidence_ids:
                density = per_evidence_ent_density[id]
                if id_to_index[id] in not_indexed:
                    density -= not_indexed[id_to_index[id]]
                for _ in range(density):
                    try:
                        worker_index[predictions[index][0]].add(id)
                    except KeyError:
                        worker_index[predictions[index][0]] = set()
                        worker_index[predictions[index][0]].add(id)
                    index += 1
        except Exception as e:
            logger.error(len(annotated))
            logger.error(page_id)
            logger.error(traceback.format_exc())
            pages_not_indexed += 1

        with open(args.idx_path+worker_id+str(num)+".pkl","wb") as file:
            pickle.dump(worker_index,file)
        num+=1
    print("Worker",i,"has total",pages_not_indexed,"exceptions",sep=" ")
    print("Worker",i,"has total",evd_not_indexed,"evidences exceptions",sep=" ")
    pass


if __name__=="__main__":
    logging.basicConfig(filename="/mnt/infonas/data/harshiitb/MTP/MTP/Codebase/FEVEROUS/indexLog.log",
                    format='%(asctime)s %(message)s',
                    filemode='w')
    logger=logging.getLogger()
    logger.setLevel(logging.DEBUG)
    parser = argparse.ArgumentParser()
    start = time.time()
    parser.add_argument("--page_ids_path", type=str, help= "Contains path of page_ids file")
    parser.add_argument("--db_path", type=str, help= "contains database path")
    parser.add_argument("--model_path", type=str, help="path to BLINK models")
    parser.add_argument("--num_threads", type=int)
    parser.add_argument("--idx_path", type=str, help="path to store the index list. MUST NOT INCLUDE FILE NAME")

    args = parser.parse_args()
    print("Finding page_ids...")
    page_ids = get_page_ids(args.page_ids_path, args.db_path)[1:2000]
    # page_ids1 = random.sample(page_ids.tolist(),10000)
    # with open("random.pkl","wb") as file:
    #     pickle.dump(page_ids1,file)
    print("Page_ids calculated!")
    
    batch_size = 1000

    models_path = args.model_path
    i = 1
    build_index(page_ids, args.db_path, args.model_path, i, args.idx_path)
    
    #Merge all worker_outputs
    # dense_index = {}
    # for worker_index in worker_output:
    #     for entity,postings in worker_index.items():
    #         if entity not in dense_index.keys():
    #             dense_index[entity] = postings
    #         else:
    #             dense_index[entity].extend(postings)
    print("Time took for completition is: ", time.time()-start)
    pass