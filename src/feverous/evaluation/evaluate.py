import argparse
import os
import sys
import unicodedata
from typing import List
from urllib.parse import unquote

import jsonlines
from cleantext import clean

from feverous.evaluation.feverous_scorer import feverous_score


def feverous_evaluation(input_path: str, use_gold_verdict: bool = False) -> List[str]:
    """
    FEVEROUS evaluation, using prediction file.

    @param input_path: path to prediction file. The prediction file consists of fields 'predicted_label' and 'predicted_evidence', in addition to the gold fields 'evidence' and 'label.
    @param use_gold_verdict: Whether to use the gold labels for evaluation, resulting in Label Accuracy of 1.0. Use this flag if you only want to evaluate retrieval.

    @return: List of computed metrics [feverous score, label accuracy, evidence precision, evidence recall, evidence F1]
    """
    predictions = []

    with jsonlines.open(os.path.join(input_path)) as f:
        for i, line in enumerate(f.iter()):
            if i == 0:
                continue
            if use_gold_verdict:
                line["predicted_label"] = line["label"]
            line["evidence"] = [el["content"] for el in line["evidence"]]
            for j in range(len(line["evidence"])):
                line["evidence"][j] = [
                    [
                        el.split("_")[0],
                        el.split("_")[1]
                        if "table_caption" not in el and "header_cell" not in el
                        else "_".join(el.split("_")[1:3]),
                        "_".join(el.split("_")[2:])
                        if "table_caption" not in el and "header_cell" not in el
                        else "_".join(el.split("_")[3:]),
                    ]
                    for el in line["evidence"][j]
                ]

            line["predicted_evidence"] = [
                [
                    el.split("_")[0],
                    el.split("_")[1]
                    if "table_caption" not in el and "header_cell" not in el
                    else "_".join(el.split("_")[1:3]),
                    "_".join(el.split("_")[2:])
                    if "table_caption" not in el and "header_cell" not in el
                    else "_".join(el.split("_")[3:]),
                ]
                for el in line["predicted_evidence"]
            ]
            predictions.append(line)

    strict_score, label_accuracy, precision, recall, f1 = feverous_score(predictions)

    print("Feverous scores...")
    print("Strict score: ", strict_score)
    print("Label Accuracy: ", label_accuracy)
    print("Retrieval Precision: ", precision)
    print("Retrieval Recall: ", recall)
    print("Retrieval F1: ", f1)

    return [strict_score, label_accuracy, precision, recall, f1]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_path", type=str)
    parser.add_argument("--use_gold_verdict", action="store_true", default=False)

    args = parser.parse_args()

    feverous_evaluation(args.input_path, args.use_gold_verdict)
