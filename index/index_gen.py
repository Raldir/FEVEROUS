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
import os
import torch


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

def build_index(worker_page_ids, db_path, models_path, lock, id):
    print("Thread",i, "started", sep=" ")
    global worker_output
    not_indexed = 0
    #BLINK Model Initialization
    print("Thread",i, "loading BLINK model", sep=" ")
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
        "fast": False, # set this to be true if speed is a concern
        "output_path": "logs/" # logging directory
    }
    blink_model_args = argparse.Namespace(**blink_config)
    blink_model = blink_main_dense.load_models(blink_model_args, logger=None)
    ner_model = NER.get_model()
    print("Thread",i, "Done loading BLINK model", sep=" ")
    #ELQ model initialization
    # print("Thread",i, "loading ELQ model", sep=" ")
    # elq_config = {
    #     "interactive": False,
    #     "biencoder_model": models_path+"elq_wiki_large.bin",
    #     "biencoder_config": models_path+"elq_large_params.txt",
    #     "cand_token_ids_path": models_path+"entity_token_ids_128.t7",
    #     "entity_catalogue": models_path+"entity.jsonl",
    #     "entity_encoding": models_path+"all_entities_large.t7",
    #     "output_path": "logs/", # logging directory
    #     "faiss_index": "hnsw",
    #     "index_path": models_path+"faiss_hnsw_index.pkl",
    #     "num_cand_mentions": 10,
    #     "num_cand_entities": 10,
    #     "threshold_type": "joint",
    #     "threshold": -4.5,
    # }

    # elq_args = argparse.Namespace(**elq_config)
    # elq_model = elq_main_dense.load_models(elq_args, logger=None)

    db =  FeverousDB(db_path)
    worker_index = {}
    for page_id in tqdm(worker_page_ids):
        page_json = db.get_doc_json(page_id)
        wiki_page = WikiPage(page_id, page_json)
        #Index all windows in the page
        window_obj = wiki_window(wiki_page)
        row_obj = wiki_row(wiki_page)
        all_window_ids = window_obj.get_all_windows()
        all_row_ids = row_obj.get_all_rows()
        all_evidence_content_context = []
        all_evidence_content_context.extend(window_obj.get_all_content_context())
        all_evidence_content_context.extend(row_obj.get_all_content_context())
        evidence_ids = []
        for id in all_window_ids:
            evidence_ids.append("window_"+id)
        for id in all_row_ids:
            evidence_ids.append("row_"+id)
        
        per_evidence_ent_density = dict.fromkeys(evidence_ids, 0)
        annotated = blink_main_dense._annotate(ner_model,all_evidence_content_context)
        index_to_id = {}
        for id in evidence_ids:
            index_to_id[len(index_to_id)] = id
        for ent in annotated:
            per_evidence_ent_density[index_to_id[ent["sent_idx"]]] += 1
        try:
            _, _, _, _, _, predictions, _, = blink_main_dense.run(blink_model_args, None, *blink_model, test_data=annotated)
            index = 0
            for id in evidence_ids:
                for _ in range(per_evidence_ent_density[id]):
                    try:
                        worker_index[predictions[index][0]].append(id)
                    except KeyError:
                        worker_index[predictions[index][0]] = []
                        worker_index[predictions[index][0]].append(id)
                    index += 1
        except Exception as e:
            not_indexed += 1

    lock.acquire()
    print("Thread",i,"has total",not_indexed,"exceptions",sep=" ")
    worker_output.append(worker_index)
    lock.release()
    pass

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--page_ids_path", type=str, help= "Contains path of page_ids file")
    parser.add_argument("--db_path", type=str, help= "contains database path")
    parser.add_argument("--model_path", type=str, help="path to BLINK models")
    parser.add_argument("--num_threads", type=int)
    parser.add_argument("--idx_path", type=str, help="path to store the index list. MUST NOT INCLUDE FILE NAME")

    args = parser.parse_args()
    print("Finding page_ids...")
    page_ids = get_page_ids(args.page_ids_path, args.db_path)[1:]
    print("Page_ids calculated!")
    
    batch_size = 10 // args.num_threads
    threads = []


    models_path = args.model_path
    global worker_output
    worker_output = list()
    lock = threading.Lock()
    #Create threads
    print("Creating threads....")
    for i in range(args.num_threads):
        threads.append(threading.Thread(target=build_index , args=(
                        page_ids[i*batch_size:min((i+1)*batch_size, 10)],
                        args.db_path,
                        args.model_path,
                        lock,
                        i
        )))
    #Start threads
    for i in range(args.num_threads):
        threads[i].start()

    #wait until all threads are completed
    for i in range(args.num_threads):
        threads[i].join()
    
    #Merge all worker_outputs
    dense_index = {}
    for worker_index in worker_output:
        for entity,postings in worker_index.items():
            if entity not in dense_index.keys():
                dense_index[entity] = postings
            else:
                dense_index[entity].extend(postings)
            
    with open(args.idx_path+"/idx.pkl","wb") as file:
        pickle.dump(dense_index,file)
    pass