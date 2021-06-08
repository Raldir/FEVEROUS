from database.feverous_db import FeverousDB
from utils.wiki_page import WikiPage
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--db_file', type=str)
    args = parser.parse_args()
    db =  FeverousDB(args.db_file)

    page_json = db.get_doc_json("Anarchism")
    wiki_page = WikiPage("Anarchism", page_json)


    wiki_lists = wiki_page.get_lists() #return list of all Wiki Tables
    wiki_lists_0 = wiki_lists[0]
    #String representation: Prefixes '-' for unsorted elements and enumerations for sorted elements
    print(str(wiki_lists_0))

    wiki_lists[0].get_list_by_level(0) #returns list elements by level
