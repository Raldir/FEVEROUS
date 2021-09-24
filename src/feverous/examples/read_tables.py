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
    wiki_tables = wiki_page.get_tables() #return list of all Wiki Tables

    wiki_table_0 = wiki_tables[0]
    wiki_table_0_rows = wiki_table_0.get_rows() #return list of WikiRows
    wiki_table_0_header_rows = wiki_table_0.get_header_rows() #return list of WikiRows that are headers
    is_header_row = wiki_table_0_rows[0].is_header_row() #or check the row directly whether it is a header


    cells_row_0 = wiki_table_0_rows[0].get_row_cells()#return list with WikiCells for row 0
    row_representation = '|'.join([str(cell) for cell in cells_row_0]) #get cell content seperated by vertical line
    row_representation_same = str(cells_row_0) #or just stringfy the row directly.

    #returns WikiTable from Cell_id. Useful for retrieving associated Tables for cell annotations.
    table_0_cell_dict = wiki_page.get_table_from_cell_id(cells_row_0[0].get_id())
    # print(table_0_cell_dict)
