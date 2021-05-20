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
