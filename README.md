# Fact Extraction and VERification Over Unstructured and Structured information

This repository maintains the code to generate and prepare the dataset, as well as the code of the annotation platform used to generate the FEVEROUS datset. Visit [http://fever.ai](https://fever.ai/task.html) to find out more about the shared task.

## Install Requirements

Create a new Conda environment and install torch: 
```
conda create -n feverous python=3.8
conda activate feverous
conda install pytorch==1.7.0 torchvision==0.8.0 torchaudio==0.7.0 -c pytorch
```
Then install the package requirements specified in `src/requirements.txt`. Then install the English Spacy model `python -m spacy download en_core_web_sm`.
Code has been tested for `python3.7` and `python3.8`.

## Prepare Data
Call the following script to download the FEVEROUS data:
```
./scripts/download_data.sh 
```
Or you can download the data from the [FEVEROUS dataset page](https://fever.ai/dataset/feverous.html) directly. Namely:

* Training Data
* Development Data
* Wikipedia Data as a database (sqlite3)

After downloading the data, unpack the Wikipedia data into the same folder (i.e. `data`).

## Reading Data

### Read Annotation Data
To process annotation files we provide a simple processing script `annotation_processor.py`. The script currently does not support the use of annotator operations.

### Read Wikipedia Data

This repository contains elementary code to assist you in reading and processing the provided Wikipedia data. By creating a a `WikiPage` object using the json data of a Wikipedia article, every element of an article is instantiated as a `WikiElement` on top of several utility functions you can then use (e.g. get an **element's context**, get an element by it's annotation id, ...). 

```python
from database.feverous_db import FeverousDB
from utils.wiki_page import WikiPage

db =  FeverousDB("path_to_the_wiki")

page_json = db.get_doc_json("Anarchism")
wiki_page = WikiPage("Anarchism", page_json)

context_sentence_14 = wiki_page.get_context('sentence_14') # Returns list of context Wiki elements

prev_elements = wiki_page.get_previous_k_elements('sentence_5', k=4) #Gets Wiki element before sentence_5
next_elements = wiki_page.get_next_k_elements('sentence_5', k=4) #Gets Wiki element after sentence_5
```

### WikiElement
There are five different types of `WikiElement`: `WikiSentence`, `WikiTable`, `WikiList`, `WikiSection`, and `WikiTitle`.

A `WikiElement` defines/overrides four functions:
* `get_ids`: Returns list of all ids in that element
* `get_id`: Return the specific id of that element
* `id_repr`: Returns a string representation of all ids in that element
* `__str__`: Returns a string representation of the element's content

`WikiSection` additionally defines a function `get_level` to get the depth level of the section. `WikiTable` and `WikiList` have some additional funcions, explained below. 

### Reading Tables
A `WikiTable` object takes a table from the Wikipedia Data and normalizes the table to `column_span=1` and `row_span=1`. It also adds other quality of life features to processing the table or its rows.

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
 
### Reading Lists
```python
wiki_lists = wiki_page.get_lists()
wiki_lists_0 = wiki_lists[0]
#String representation: Prefixes '-' for unsorted elements and enumerations (1., 2. ...) for sorted elements
print(str(wiki_lists_0))

wiki_lists[0].get_list_by_level(0) #returns list elements by level
 ```

## Baseline

### Retriever
Our baseline retriever module is a combination of entity matching and TF-IDF using DrQA. We first extract the top $k$ pages by matching extracted entities from the claim with Wikipedia articles. If less than k pages have been identified this way, the remaining pages are selected by Tf-IDF matching between the introductory sentence of an article and the claim. To use TF-IDF matching we need to build a TF-IDF index. Run:
```
PYTHONPATH=src python src/baseline/retriever/build_db.py --db_path data/feverous-wiki-pages.db --save_path data/feverous-wiki-docs.db
PYTHONPATH=src python src/baseline/retriever/build_tfidf.py --db_path data/feverous-wiki-docs.db --out_dir data/index/
 ```
 We can now extract the top k documents:
 ```
PYTHONPATH=src python src/baseline/retriever/document_entity_tfidf_ir.py  --model data/index/feverous-tfidf-ngram=2-hash=16777216 --db data/feverous-wiki-docs.db --count 5 --split dev --data_path data/
 ```
The top l sentences and q tables of the selected pages are then scored separately using TF-IDF. We set l=5 and q=3.
```
PYTHONPATH=src python src/baseline/retriever/sentence_tfidf_drqa.py --db data/feverous-wiki-pages.db--split dev --out_folder data --max_page 5 --max_sent 5 --use_precomputed false --data_path data/
PYTHONPATH=src python src/baseline/retriever/table_tfidf_drqa.py --db data/feverous-wiki-pages.db --split dev --max_page 5 --max_tabs 3 --use_precomputed false --data_path data/
 ```
Combine both retrieved sentences and tables into one file:
 ```
 PYTHONPATH=src python src/baseline/retriever/combine_retrieval.py --data_path data --max_page 5 --max_sent 5 --max_tabs 3 --split dev
 ```

For the next steps, we employ pre-trained transformers. You can either train these themselves (c.f. next section) or download our pre-trained models directly (We recommend training the model yourself as the version used in the paper has not been trained on the full training set). The Cell extraction model can be downloaded [here](https://drive.google.com/file/d/1PKsqwbzVUyWv6guXIUwksBYVARYMkCyU/view?usp=sharing). Extract the model and place it into the folder `models`.  

To extract relevant cells from extracted tables, run:
 ```
 PYTHONPATH=src python src/baseline/retriever/predict_cells_from_table.py --input_path data/dev.combined.not_precomputed.p5.s5.t3.jsonl --max_sent 5 --wiki_path data/feverous-wiki-pages.db --model_path models/feverous_cell_extractor
  ```
 
### Verdict Prediction
To predict the verdict given either download our fine-tuned model  [here](https://drive.google.com/file/d/1E08IO0gU7H4Tod2vriIM3agynIkrscK9/view?usp=sharing) or train it yourself (c.f. Training). Again, we recommend training the model yourself as the model used in the paper has not been trained on the full training set. Then run:
```
 PYTHONPATH=src python src/baseline/predictor/evaluate_verdict_predictor.py --input_path data/dev.combined.not_precomputed.p5.s5.t3.cells.jsonl --wiki_path data/feverous-wiki-pages.db --model_path models/feverous_verdict_predictor
 ```
 
### Training
TBA

## Evaluation
To evaluate your generated predictions locally, simply run the file `evaluate.py` as following:
```
python evaluation/evaluate.py --input_path data/dev.combined.not_precomputed.p5.s5.t3.cells.verdict.jsonl
 ```
Note that any input file needs to define the fields `label`, `predicted_label`, `evidence`, and `predicted_evidence` in the format specified in the file `feverous_scorer`.

## Shared Task submission
TBA
