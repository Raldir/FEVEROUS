import argparse
import json

from tqdm import tqdm

from feverous.baseline.drqa import retriever
from feverous.baseline.drqa.retriever import DocDB
from feverous.utils.annotation_processor import AnnotationProcessor
from feverous.utils.wiki_processor import WikiDataProcessor


def process(ranker, query, k=1):
    doc_names, doc_scores = ranker.closest_docs(query, k)

    return zip(doc_names, doc_scores)


def document_entity_tfidf_retrieval(split: str, count: str, db: str, data_path: str, model: str) -> None:
    ranker = retriever.get_class("tfidf")(tfidf_path=model)
    annotation_processor = AnnotationProcessor("{}/{}.jsonl".format(data_path, split))
    db = DocDB(db)
    document_titles = set(db.get_doc_ids())

    with open("{0}/{1}.pages.p{2}.jsonl".format(data_path, split, count), "w+") as f2:
        annotations = [annotation for annotation in annotation_processor]
        for i, annotation in enumerate(tqdm(annotations)):
            js = {}
            js["claim"] = annotation.get_claim()
            entities = [el[0] for el in annotation.get_claim_entities()]
            entities = [ele for ele in entities if ele in document_titles]
            if len(entities) < count:
                pages = list(process(ranker, annotation.get_claim(), k=count))

            pages = [ele for ele in pages if ele[0] not in entities]
            pages_names = [ele[0] for ele in pages]

            entity_matches = [(el, 2000) if el in pages_names else (el, 500) for el in entities]
            js["predicted_pages"] = entity_matches + pages[: (count - len(entity_matches))]
            f2.write(json.dumps(js) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", type=str)
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--db", type=str)
    parser.add_argument("--data_path", type=str)
    parser.add_argument("--model", type=str, default=None)
    args = parser.parse_args()

    document_entity_tfidf_retrieval(args.split, args.count, args.db, args.data_path, args.model)
