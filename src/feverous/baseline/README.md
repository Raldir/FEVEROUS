
### Evidence Retrieval
 We first extract the top $k$ pages by matching extracted entities from the claim with Wikipedia articles. If less than k pages have been identified this way, the remaining pages are selected by Tf-IDF matching between the introductory sentence of an article and the claim. To use TF-IDF matching we need to build a TF-IDF index. Run the code from the directory `src`, assuming that the FEVEROUS datebase is the file `data/feverous_wikiv1.db`:

```bash
python -m feverous.baseline.retriever.build_db --db_path ../data/feverous_wikiv1.db --save_path ../data/feverous-wiki-docs.db
python -m feverous/baseline/retriever/build_tfidf.py --db_path ../data/feverous-wiki-docs.db --out_dir ../data/index/
 ```
 We can now extract the top k documents:
 
 ```bash
PYTHONPATH=src/feverous python src/feverous/baseline/retriever/document_entity_tfidf_ir.py  --model data/index/feverous-wiki-docs-tfidf-ngram=2-hash=16777216-tokenizer=simple.npz --db data/feverous-wiki-docs.db --count 5 --split dev --data_path data/
 ```
The top l sentences and q tables of the selected pages are then scored separately using TF-IDF. We set l=5 and q=3.

```bash
python -m  feverous.baseline.retriever.sentence_tfidf_drqa --db ../data/feverous_wikiv1.db --split dev --max_page 5 --max_sent 5 --use_precomputed false --data_path ../data/
python -m feverous.baseline.retriever.table_tfidf_drqa --db ../data/feverous_wikiv1.db --split dev --max_page 5 --max_tabs 3 --use_precomputed false --data_path ../data/
 ```
 
Combine both retrieved sentences and tables into one file:
 
 ```bash
 python3 -m feverous.baseline.retriever.combine_retrieval --split dev --max_page 5 --max_sent 5 --max_tabs 3 --data_path ../data
 ```

For the next steps, we employ pre-trained transformers. You can either train these themselves (c.f. next section) or download our pre-trained models directly that have been used to produce the results from the paper. The Cell extraction model can be downloaded [here](https://drive.google.com/file/d/1Zu3RUFzThPpsSkBhlYc0CBoRpIRxauGR/view?usp=sharing). Extract the model and place it into the folder `models`.  

To extract relevant cells from extracted tables, run:
 ```bash
 python3 -m feverous.baseline.retriever.predict_cells_from_table --input_path ../data/dev.combined.not_precomputed.p5.s5.t3.jsonl --wiki_path ../data/feverous_wikiv1.db --config_path feverous/baseline/retriever/config_roberta.json
  ```

### Verdict Prediction
To predict the verdict given either download our fine-tuned model  [here](https://drive.google.com/file/d/1SoxeTDp2NETbZdMpEle_QO8Cw0oxgUbV/view?usp=sharing) or train it yourself (c.f. Training). Then run:
```bash
python3 -m src.feverous.baseline.predictor.evaluate_verdict_predictor --input_path ../data/dev.combined.not_precomputed.p5.s5.t3.cells.jsonl --wiki_path ../data/feverous_wikiv1.db --config_path feverous/baseline/predictor/config_debertav3_fever.json
 ```

### Training

For training both the cell extraction and verdict prediction models, we use the `trainer` by `huggingface`, thus for an exhaustive list of hyperparameters to tune check out [their page](https://huggingface.co/transformers/main_classes/trainer.html). The baseline uses mostly default hyperparameters. We specify configuration files with all hyperparameters we considered tuning, located in the associated source code folder, respectively.

To train the cell extraction model run:

```bash
python3 -m feverous.baseline.retriever.train_cell_evidence_retriever --wiki_path ../data/feverous_wikiv1.db --config_path feverous/baseline/retriever/config_roberta.json --input_path ../data
 ```

To train the verdict prediction model run respectively:
```bash
python3 -m feverous.baseline.predictor.train_verdict_predictor --wiki_path ../data/feverous_wikiv1.db --config_path feverous/baseline/predictor/config_roberta_old.json --input_path ../data --sample_nei
```

The models are saved every n steps, thus specify the correct path during inference accordingly.
