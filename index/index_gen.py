#Call this script from ../FEVEROUS directory
from feverous.database.feverous_db import FeverousDB
import numpy as np
import pickle
import sqlite3
from pathlib import Path
import argparse

def get_ids(page_ids_path, db_path):
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

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--page_ids_path", type=str, help= "Contains path of page_ids file")
    parser.add_argument("--db_path", type=str, help= "contains database path")

    args = parser.parse_args()

    page_ids = get_ids(args.page_ids_path, args.db_path)
    print(page_ids[:10])
