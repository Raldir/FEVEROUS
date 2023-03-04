import argparse
import json
import os
import sqlite3
import traceback
import unicodedata

from tqdm import tqdm

from feverous.utils.wiki_processor import WikiDataProcessor

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db_path", type=str, help="/path/to/data")
    parser.add_argument("--wiki_path", type=str, help="/path/to/data")
    parser.add_argument("--wiki_name", type=str, help="/path/to/data")

    args = parser.parse_args()
    conn = sqlite3.connect(os.path.join(args.db_path, args.wiki_name))
    c = conn.cursor()
    c.execute("CREATE TABLE wiki (id PRIMARY KEY, data json)")
    wiki_proc = WikiDataProcessor(args.wiki_path)

    for i, line in enumerate(tqdm(wiki_proc.read_json_files())):
        try:
            title = unicodedata.normalize("NFD", line[0])
            content = unicodedata.normalize("NFD", json.dumps(line[1], ensure_ascii=False))
            c.execute("insert into wiki values (?, ?)", [title, content])
            if (i + 1) % 10000 == 0:
                conn.commit()
        except:
            traceback.print_exc()
            print(title, content)
            continue
    conn.commit()
    conn.close()
