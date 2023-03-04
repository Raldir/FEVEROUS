python -m feverous.baseline.retriever.build_db --db_path ../data/feverous_wikiv1.db --save_path ../data/feverous-wiki-docs.db
python -m feverous/baseline/retriever/build_tfidf.py --db_path ../data/feverous-wiki-docs.db --out_dir ../data/index/
 ```
 We can now extract the top k documents:
 
 ```bash
PYTHONPATH=src/feverous python src/feverous/baseline/retriever/document_entity_tfidf_ir.py  --model data/index/feverous-wiki-docs-tfidf-ngram=2-hash=16777216-tokenizer=simple.npz --db data/feverous-wiki-docs.db --count 5 --split dev --data_path data/
 ```
The top l sentences and q tables of the selected pages are then scored separately using TF-IDF. We set l=5 and q=3.

```bash
python -m  feverous.baseline.retriever.sentence_tfidf_drqa --db ../data/feverous_wikiv1.db --split train --max_page 5 --max_sent 5 --use_precomputed false --data_path ../data/
python -m feverous.baseline.retriever.table_tfidf_drqa.py --db data/feverous_wikiv1.db --split train --max_page 5 --max_tabs 3 --use_precomputed false --data_path ../data/
 ```
 
Combine both retrieved sentences and tables into one file:
 
 ```bash
 PYTHONPATH=src/feverous python src/feverous/baseline/retriever/combine_retrieval.py --data_path data --max_page 5 --max_sent 5 --max_tabs 3 --split dev
 ```

For the next steps, we employ pre-trained transformers. You can either train these themselves (c.f. next section) or download our pre-trained models directly that have been used to produce the results from the paper. The Cell extraction model can be downloaded [here](https://drive.google.com/file/d/1Zu3RUFzThPpsSkBhlYc0CBoRpIRxauGR/view?usp=sharing). Extract the model and place it into the folder `models`.  

To extract relevant cells from extracted tables, run:
 ```bash
 PYTHONPATH=src/feverous python src/feverous/baseline/retriever/predict_cells_from_table.py --input_path data/dev.combined.not_precomputed.p5.s5.t3.jsonl --max_sent 5 --wiki_path data/feverous_wikiv1.db --model_path models/feverous_cell_extractor
  ```

### Verdict Prediction
To predict the verdict given either download our fine-tuned model  [here](https://drive.google.com/file/d/1SoxeTDp2NETbZdMpEle_QO8Cw0oxgUbV/view?usp=sharing) or train it yourself (c.f. Training). Then run:
```bash
 PYTHONPATH=src/feverous python src/feverous/baseline/predictor/evaluate_verdict_predictor.py --input_path data/dev.combined.not_precomputed.p5.s5.t3.cells.jsonl --wiki_path data/feverous_wikiv1.db --model_path models/feverous_verdict_predictor
 ```