# Fact Extraction and VERification Over Unstructured and Structured information

This repository (will) contains the code to generate and prepare the dataset, as well as the code of the annotation platform used to generate the FEVEROUS datset. Visit [http://fever.ai](https://fever.ai/task.html) to find out more about the shared task.

## Prepare Data
Download the data from the [resource page](https://fever.ai/resources.html). Namely:

* Training Data
* Development Data
* Wikipedia Data as a database (sqlite3)

### Retrieve context for Wikipedia elements

```python
from database.feverous_db import FeverousDB
from utils.wiki_page import WikiPage

db =  FeverousDB("path_to_the_wiki")

page_json = db.get_doc_json("Anarchism")
wiki_page = WikiPage("Anarchism", page_json)

context_sentence_0 = wiki_page.get_context('sentence_14') # Returns list of Wiki elements
```
### Reading Wikipedia data

#### Reading Tables
A `WikiTable` object takes a table from the Wikipedia Data and normalizes the table to `column_span` and `row_span=1`. It also adds other quality of life features to processing the table or its rows.

```python
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
 ```
