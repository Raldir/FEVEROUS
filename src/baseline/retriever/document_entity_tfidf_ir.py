import argparse
import json
from tqdm import tqdm
from baseline.drqa import retriever
from baseline.drqa.retriever import DocDB
from utils.annotation_processor import AnnotationProcessor
from utils.wiki_processor import WikiDataProcessor
from baseline.drqa.retriever.doc_db import DocDB

def process(ranker, query, k=1):
    doc_names, doc_scores = ranker.closest_docs(query, k)

    return zip(doc_names, doc_scores)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--split',type=str)
    parser.add_argument('--count',type=int, default=1)
    parser.add_argument('--db',type=str)
    parser.add_argument('--data_path',type=str)
    parser.add_argument('--model', type=str, default=None)
    args = parser.parse_args()

    k = args.count
    split = args.split
    ranker = retriever.get_class('tfidf')(tfidf_path=args.model)
    annotation_processor = AnnotationProcessor("{}/{}.jsonl".format(args.data_path, args.split))
    db = DocDB(args.db)
    document_titles = set(db.get_doc_ids())

    with open("{0}/{1}.pages.p{2}.jsonl".format(args.data_path, args.split, k),"w+") as f2:
        annotations = [annotation for annotation in annotation_processor]
        for i, annotation in enumerate(tqdm(annotations)):
            js = {}
            # js['id'] = annotation.get_id()
            js['claim'] = annotation.get_claim()
            entities = [el[0] for el in annotation.get_claim_entities()]
            entities = [ele for ele in entities if ele in document_titles]
            if len(entities) < args.count:
                pages = list(process(ranker,annotation.get_claim(),k= args.count))

            pages = [ele for ele in pages if ele[0] not in entities]
            pages_names = [ele[0] for ele in pages]

            entity_matches = [(el,2000) if el in pages_names else (el, 500) for el in entities]
            # pages = process(ranker,annotation.get_claim(),k=k)
            js["predicted_pages"] = entity_matches + pages[:(args.count -len(entity_matches))]
            f2.write(json.dumps(js)+"\n")

    # with open("data/fever-data/{0}.jsonl".format(split),"r") as f:
    #     with open("data/ir/{0}.pages.p{1}.jsonl".format(split,k),"w+") as f2:
    #         for line in tqdm(f.readlines()):
    #             js = json.loads(line)
    #             pages = process(ranker,js['claim'],k=k)
    #             js["predicted_pages"] = list(pages)
    #             f2.write(json.dumps(js)+"\n")
