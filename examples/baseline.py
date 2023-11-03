import argparse
import os

from feverous.baseline.predictor.evaluate_verdict_predictor import predict_verdict
from feverous.baseline.retriever import (
    build_db,
    build_tfidf,
    cell_retrieval,
    combine_retrieval,
    document_entity_tfidf_retrieval,
    sentence_tfidf_retrieval,
    table_tfidf_retrieval,
)
from feverous.evaluation.evaluate import feverous_evaluation

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", type=str, default="dev", help="Name of Split.")
    parser.add_argument("--data_path", type=str, default="data/", help="Path to data folder.")
    parser.add_argument("--db_path", type=str, default="data/feverous-wiki-pages.db", help="Path to FEVEROUS DB.")

    parser.add_argument(
        "--tf_idf_db_path",
        type=str,
        default="data/feverous-wiki-docs.db",
        help="Path for storing the TF-IDF DB for Doc Retrieval.",
    )
    parser.add_argument(
        "--tf_idf_index_path", type=str, default="data/index/", help=" Path for storing the TF-IDF Index."
    )

    parser.add_argument("--doc_count", type=int, default=5, help="Number of Documents to select.")
    parser.add_argument("--sent_count", type=int, default=5, help="Number of Sentences to select.")
    parser.add_argument("--tab_count", type=int, default=3, help="Number of Tables to select.")

    parser.add_argument(
        "--config_path_cell_retriever",
        type=str,
        default="src/feverous/baseline/retriever/config_roberta.json",
        help="Path to the json config file for the cell extractor.",
    )
    parser.add_argument(
        "--config_path_verdict_predictor",
        type=str,
        default="src/feverous/baseline/predictor/config_roberta_old.json",
        # default="src/feverous/baseline/predictor/config_debertav3_fever.json", # Use this one for a slightly improved verification model
        help="Path to the json config file for the verdict predictor.",
    )

    args = parser.parse_args()

    index_name = "data/index/feverous-wiki-docs-tfidf-ngram=2-hash=16777216-tokenizer=simple.npz"

    # Build the TF-iDF index for retrieval using introductory Wikipedia section
    build_db(db_path=args.db_path, save_path=args.tf_idf_db_path, mode="intro", preprocess=None, num_workers=None)
    build_tfidf(db_path=args.tf_idf_db_path, out_dir=args.tf_idf_index_path)

    # # Entity and TF-IDF based document selection
    document_entity_tfidf_retrieval(
        split=args.split, count=args.doc_count, db=args.tf_idf_db_path, data_path=args.data_path, model=index_name
    )

    # # Based on retrieved documents, re-rank sentenes and tables via TF-IDF and combine selected evidence
    sentence_tfidf_retrieval(
        split=args.split,
        max_page=args.doc_count,
        max_sent=args.sent_count,
        use_precomputed=False,
        db=args.db_path,
        data_path=args.data_path,
    )
    table_tfidf_retrieval(
        split=args.split,
        max_page=args.doc_count,
        max_tabs=args.tab_count,
        use_precomputed=False,
        db=args.db_path,
        data_path=args.data_path,
    )
    combine_retrieval(
        split=args.split,
        max_page=args.doc_count,
        max_sent=args.sent_count,
        max_tabs=args.tab_count,
        data_path=args.data_path,
    )

    # # Select specific cells in re-ranked tables as evidence
    cell_retrieval(
        input_path=os.path.join(
            args.data_path,
            "{}.combined.not_precomputed.p{}.s{}.t{}.jsonl".format(
                args.split, args.doc_count, args.sent_count, args.tab_count
            ),
        ),
        wiki_path=args.db_path,
        config_path=args.config_path_cell_retriever,
    )

    # Predict verdict based on retrieved evidence
    predict_verdict(
        input_path=os.path.join(
            args.data_path,
            "{}.combined.not_precomputed.p{}.s{}.t{}.cells.jsonl".format(
                args.split, args.doc_count, args.sent_count, args.tab_count
            ),
        ),
        wiki_path=args.db_path,
        config_path=args.config_path_verdict_predictor,
    )

    # Evaluate both retrieved evidence and predicted verdict on FEVEROUS score
    feverous_evaluation(
        input_path=os.path.join(
            args.data_path,
            "{}.combined.not_precomputed.p{}.s{}.t{}.cells.verdict.jsonl".format(
                args.split, args.doc_count, args.sent_count, args.tab_count
            ),
        ),
        use_gold_verdict=False,
    )
