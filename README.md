# Fact Extraction and VERification Over Unstructured and Structured information

<p align="center">
    <a href="https://github.com/Raldir/FEVEROUS/blob/main/LICENSE">
        <img alt="GitHub" src="https://img.shields.io/github/license/Raldir/FEVEROUS">
    </a>
    <a href="https://pypi.org/project/feverous/">
        <img alt="GitHub release" src="https://img.shields.io/pypi/v/feverous">
    </a>
</p>


This repository maintains the code of the annotation platform, generating and preparing the dataset, as well as the baseline described in the NeurIPS 2021 Dataset and Benchmark paper: [FEVEROUS: Fact Extraction and VERification Over
Unstructured and Structured information](https://arxiv.org/pdf/2106.05707.pdf).

> Fact verification has attracted a lot of attention in the machine learning and natural language processing communities, as it is one of the key methods for detecting misinformation. Existing large-scale benchmarks for this task have focused mostly on textual sources, i.e. unstructured information, and thus ignored the wealth of information available in structured formats, such as tables. In this paper we introduce a novel dataset and benchmark, Fact Extraction and VERification Over Unstructured and Structured information (FEVEROUS), which consists of 87,026 verified claims. Each claim is annotated with evidence in the form of sentences and/or cells from tables in Wikipedia, as well as a label indicating whether this evidence supports, refutes, or does not provide enough information to reach a verdict. Furthermore, we detail our efforts to track and minimize the biases present in the dataset and could be exploited by models, e.g. being able to predict the label without using evidence. Finally, we develop a baseline for verifying claims against text and tables which predicts both the correct evidence and verdict for 18% of the claims.

## Shared Task

Visit [http://fever.ai](https://fever.ai/task.html) to find out more about the FEVER Workshop 2021 shared task @EMNLP on FEVEROUS.

## Change Log
* **21 March 2023** - Updated code and execution pipeline for FEVEROUS baseline.
* **06 March 2023** - Compatibility updates and refactoring code of reading Wikipedia.
* **24 Sep 2021** - The Feverous repository is now also accessible through PyPI. Install it using `python -m pip install feverous`.
* **24 Sep 2021** - The Feverous repository is now also accessible through PyPI. Install it using `python -m pip install feverous`.
* **Nov 2021** - FEVEROUS Shared Task Description paper is now [online](https://aclanthology.org/2021.fever-1.1.pdf). Congratulations to all participating teams!
* **20 Sep 2021** - Added verification challenge fields to the dataset and description to the paper.
* **14 Sep 2021** - Baseline updated: cell extractor and verdict prediction model trained on entire dataset
* **27 July 2021** - Submissions to the FEVEROUS Shared Task are closed. Everyone is still welcome to submit to the Post-Competition Leaderboard. 
* **24 July 2021** - Submissions to the FEVEROUS Shared Task are now open.
* **07 June 2021** - Release of the full training data and bug-fixed development split
* **20 May 2021** - Release of the first training data batch and the development split

## Install Requirements

Create a new Conda environment and install torch:

```bash
conda create -n feverous python=3.8
conda activate feverous
conda install pytorch==1.13.1 torchvision==0.14.1 torchaudio==0.13.1 -c pytorch
```

or with pip

```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install torch==1.13.1 torchvision==0.14.1 torchaudio==0.13.1
python3 -m pip install .
```

Then install the package requirements specified in `src/feverous/requirements.txt`. Then install the English Spacy model `python3 -m spacy download en_core_web_sm`.

Code has been tested for `python3.7` and `python3.8`.

## Prepare Data

Call the following script to download the FEVEROUS data:

```bash
./scripts/download_data.sh
```

Or you can download the data from the [FEVEROUS dataset page](https://fever.ai/dataset/feverous.html) directly. Namely:

* Training Data
* Development Data
* Wikipedia Data as a database (sqlite3)

After downloading the data, unpack the Wikipedia data into the same folder (i.e. `data`).

## Reading Data

### Read Wikipedia Data

This repository contains elementary code to assist you in reading and processing the provided Wikipedia data. By creating a a `WikiPage` object using the json data of a Wikipedia article, every element of an article is instantiated as a `WikiElement` on top of several utility functions you can then use (e.g. get an **element's context**, get an element by it's annotation id, ...).

```python
from feverous.database.feverous_db import FeverousDB
from feverous.utils.wiki_page import WikiPage

db =  FeverousDB("path_to_the_wiki")

page_json = db.get_doc_json("Anarchism")
wiki_page = WikiPage("Anarchism", page_json)

context_sentence_14 = wiki_page.get_context('sentence_14') # Returns list of context Wiki elements

prev_elements = wiki_page.get_previous_k_elements('sentence_5', k=4) # Gets Wiki element before sentence_5
next_elements = wiki_page.get_next_k_elements('sentence_5', k=4) # Gets Wiki element after sentence_5
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

wiki_table_0 = wiki_tables[0] # Select the first table on the Wikipedia article
wiki_table_0_rows = wiki_table_0.get_rows() # return list of WikiRows
wiki_table_0_header_rows = wiki_table_0.get_header_rows() # return list of WikiRows that are headers
is_header_row = wiki_table_0_rows[0].is_header_row() # or check the row directly whether it is a header


cells_row_0 = wiki_table_0_rows[0].get_row_cells() # return list with WikiCells for row 0
row_representation = '|'.join([str(cell) for cell in cells_row_0]) # get cell content seperated by vertical line
row_representation_same = str(cells_row_0) # or just stringfy the row directly.

#returns WikiTable from Cell_id. Useful for retrieving associated Tables for cell annotations.
table_0_cell_dict = wiki_page.get_table_from_cell_id(cells_row_0[0].get_id())
 ```

### Reading Lists

```python
wiki_lists = wiki_page.get_lists()
wiki_lists_0 = wiki_lists[0]
# String representation: Prefixes '-' for unsorted elements and enumerations (1., 2. ...) for sorted elements
print(str(wiki_lists_0))

wiki_lists[0].get_list_by_level(0) #returns list elements by level
 ```

## Baseline

Our baseline retriever module consists of following steps:

1. Bulding a TF-IDF index for retrieval using Wikipedia's introductory sections (using DrQA).
2. Select evidence documents using a combination of entity matching and TF-IDF (using DrQA).
3. Rerank the sentences and tables within the selected documents, keeping the top l sentences and q tables. Sentences and Tables are scored separately using TF-IDF. We set l=5 and q=3 in the paper. 
4. Select relevant cells from tables using a fine-tuned transformer, treating the task as a sequence labelling problem. The Cell extraction model as used to preduce the results in our paper can be downloaded [here](https://drive.google.com/file/d/1Zu3RUFzThPpsSkBhlYc0CBoRpIRxauGR/view?usp=sharing). Extract the model and place it into the folder `models`.  
5. Predict the claim's veracity via the retrieved sentence and table/cell evidence, using a fine-tuned transformer. You can download our fine-tuned model [here](https://drive.google.com/file/d/1SoxeTDp2NETbZdMpEle_QO8Cw0oxgUbV/view?usp=sharing).

To run the baseline, you can either execute each individual step manually (see `baseline/README`) or simply execute:

 ```bash

 python3 examples/baseline.py --split dev --doc_count 5 --sent_count 5 --tab_count 3 --config_path_cell_retriever src/feverous/baseline/retriever/config_roberta.json --config_path_verdict_predictor src/feverous/baseline/predictor/config_roberta_old.json

```
The script will create several intermediate prediction files, the final one being `data/dev.combined.not_precomputed.p5.s5.t3.cells.verdict.jsonl`.
Note that the python file assumes that you have downloaded models and data and placed them into the appropriate folder, as instructed above. For details on how to re-train the deployed models youself, see `baseline/README`. 


## Evaluation

To evaluate your generated predictions locally, simply run the file `evaluate.py` as following:

```bash
python src/feverous/evaluation/evaluate.py --input_path data/dev.combined.not_precomputed.p5.s5.t3.cells.verdict.jsonl
 ```
 
Note that any input file needs to define the fields `label`, `predicted_label`, `evidence`, and `predicted_evidence` in the format specified in the file `feverous_scorer`.

## Leaderboard Submission

Submission to the FEVEROUS Leaderboard remain open and are done via the EvalAI platform: https://eval.ai/web/challenges/challenge-page/1091/. 

Submissions are listed under the *After Competition: Test Phase*. You can also submit your predictions on the development split to get familar with the submission system. When submitting system predictions, you need to specify the system name, and, if available a link to the code. The Team name you specified on EvalAI will be used. The shared task which closed on the 27. July 2021 was run on the same blind test data.


Submission files have to be in the same format as required for `evaluate.py`. To convert predictions from the verdict prediction step to the leaderboard submission format, call the script `prepare_submission.py`.


## Contact

Contact us either by e-mail `rmya2@cam.ac.uk` or on the [Fever Workshop slack channel](https://join.slack.com/t/feverworkshop/shared_invite/zt-4v1hjl8w-Uf4yg~diftuGvj2fvw7PDA).
