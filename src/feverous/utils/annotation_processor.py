"""
Simple Annotation Wrapper that converts each annotation into an object with corresponding attributes.
"""
import html
import itertools
import json
import linecache
import logging
import os
import pickle
import re
import sys
import traceback
from enum import Enum
from typing import Any, Dict, List

import jsonlines

from feverous.baseline.drqa.tokenizers.spacy_tokenizer import SpacyTokenizer
from feverous.utils.log_helper import LogHelper
from feverous.utils.util import *

LogHelper.setup()
logger = LogHelper.get_logger(__name__)


TOKENIZER = SpacyTokenizer(annotators=set(["ner"]))


class AnnotationProcessor:
    """
    Iterable to process the annotation files to yield annotation objects.
    """

    def __init__(self, input_path: str, with_content: bool = False, limit: int = None):
        """
        @param input_path: input path to annotation file
        @param with_content: Whether the annotation object contains the content (i.e. text) for each annotation.
        @param limit: Maximum number of annotations to consider. Useful for debugging purposes.
        """
        self.input_path = input_path
        self.with_content = with_content
        self.annotations = self.process_annotations()
        self.limit = limit

    def __iter__(self):
        return self.annotations

    def __next__(self):
        return next(self.annotations)

    def process_annotations(self):
        with jsonlines.open(self.input_path) as f:
            for i, line in enumerate(f.iter()):
                if self.limit and i >= self.limit:  # Stop if a limit is set
                    break
                if i == 0:
                    continue  # skip header line
                if i == 1:
                    if "evidence" not in line:
                        logger.info("No gold evidence found in the input.")
                try:
                    yield Annotation(line, self.with_content)
                except:
                    traceback.print_exc()
                    logger.error("Error while processing Annotation {}".format(line["id"]))
                    continue


class EvidenceType(Enum):
    """
    Simple Enum for various modality types.
    """

    SENTENCE = 0
    TABLE = 1
    LIST = 2
    JOINT = 3


class Annotation:
    def __init__(self, annotation_json: Dict[str, Any], with_content: bool):
        """
        @param annotation_json: A json of an annotation
        @param with_content: Whether the annotation object contains the evidence content (default is only IDs) for each annotation.
        """
        self.annotation_json = annotation_json
        self.with_content = with_content
        self.convert_json_to_object(annotation_json)

    def convert_json_to_object(self, annotation_json: Dict[str, Any]) -> None:
        self.claim = annotation_json["claim"]
        if "evidence" in annotation_json:
            self.verdict = annotation_json["label"] if "label" in annotation_json else None
            self.evidence = [el["content"] for el in annotation_json["evidence"]]
            self.flat_evidence = list(itertools.chain.from_iterable(self.evidence))
            self.titles = [[el.split("_")[0] for el in set] for set in self.evidence]
            self.flat_titles = [el.split("_")[0] for el in self.flat_evidence]
            self.context = [el["context"] for el in annotation_json["evidence"]]
            self.flat_context = {}
            for ele in self.context:
                self.flat_context.update(ele)
            self.num_evidence = len(self.evidence)
            self.operations = annotation_json["annotator_operations"]
        else:
            self.verdict = "SUPPORTS"  # dummy label
        if "id" in annotation_json:
            self.id = annotation_json["id"]
        if "predicted_evidence" in annotation_json:
            self.predicted_evidence = annotation_json["predicted_evidence"]
        if "predicted_verdict" in annotation_json:
            self.predicted_vertdict = annotation_json["predicted_verdict"]
        if self.with_content:
            try:
                self.evidence_content = [el["text"] for el in annotation_json["evidence"]]
                self.flat_evidence_content = list(itertools.chain.from_iterable(self.evidence_content))
            except Exception:
                self.flat_evidence_content = []
            if len(self.flat_evidence) != len(self.flat_evidence_content):
                self.flat_evidence_content = None
                return
            self.flat_evidence_content_map = {
                ele: self.flat_evidence_content[i] for i, ele in enumerate(self.flat_evidence)
            }
            self.context_content = [el["context_text"] for el in annotation_json["evidence"]]
            self.flat_context_content = {}
            for ele in self.context_content:
                self.flat_context_content.update(ele)
            self.flat_context_content_inverse = {}
            for key, values in self.flat_context.items():
                for i, value in enumerate(values):
                    self.flat_context_content_inverse[value] = self.flat_context_content[key][i]

    def get_annotation_json(self) -> Dict[str, Any]:
        """
        @return: The entire annotation in json format.
        """
        return self.annotation_json

    def get_tokenized_claim(self):
        """
        @return: Claim tokenized via SpaCy.
        """
        return TOKENIZER.tokenize(self.claim)

    def get_claim_entities(self):
        """
        @return: Entity mentions in the claim, identified via SpaCy.
        """
        return TOKENIZER.tokenize(self.claim).entity_groups()

    def get_claim(self):
        return self.claim

    def get_evidence(self, flat=False):
        """
        @param flat: Whether to return a single combined list of all evidence pieces across evidence sets.
        """
        return self.evidence if not flat else self.flat_evidence

    def get_context(self, flat=False):
        return self.context if not flat else self.flat_context

    def get_challenge(self):
        return self.challenge

    def get_operations(self):
        return self.operations

    def get_id(self):
        return self.id

    def get_verdict(self):
        return self.verdict

    def get_titles(self, flat=False):
        return self.titles if not flat else self.flat_titles

    def get_source(self):
        return self.source

    def has_evidence(self):
        return len(self.flat_evidence) > 0

    def get_evidence_type(self, flat=False):
        """
        @param flat: Whether to consider all evidence sets as a single set of evidence (i.e. one set contains only sentences, the other also cells, returns JOINT)
        @return: EvidenceType, i.e. the modality of the evidence.
        """
        types = []
        for evid_set in self.evidence:
            type_set = set([])
            for ev in evid_set:
                if "_cell_" in ev:
                    type_set.add("TABLE")
                elif "_sentence_" in ev:
                    type_set.add("SENTENCE")
                elif "_item_" in ev:
                    type_set.add("LIST")
                elif "_caption_" in ev:
                    type_set.add("TABLE")
            if len(type_set) > 1:
                types.append(EvidenceType["JOINT"])
            else:
                types.append(EvidenceType[type_set.pop()])
        if not flat:
            return types
        else:
            if len(types) > 1:
                return EvidenceType["JOINT"]
            else:
                return types[0]

    def get_evidence_text_by_id(self, id: str) -> str:
        """
        @param id: evidence id
        @return: content (i.e. text) of the evidence element
        """
        return self.flat_evidence_content_map[id]

    def get_context_text_by_id(self, id: str) -> List[str]:
        """
        @param id: evidence id
        @return: List of context content (i.e. text) of the evidence element
        """
        return self.flat_context_content[id]

    def get_context_text_by_context_id(self, id: str) -> str:
        """
        @param id: context id
        @return: content (i.e. text) of the context element
        """
        return self.flat_context_content_inverse[id]

    def get_evidence_content(self) -> List[str]:
        return self.evidence_content

    def get_context_content(self) -> List[str]:
        return self.context_content


def main():
    input_path = sys.argv[1]
    annotations = AnnotationProcessor(os.path.join(input_path, "dev.jsonl"))

    for anno in annotations:
        claim = anno.get_claim()
        claim_entities = anno.get_claim_entities()
        verdict = anno.get_verdict()
        evidence = anno.get_evidence()
        context = anno.get_context()
        print(claim)
        print(claim_entities)
        print(verdict)
        print(evidence)
        print(context)


if __name__ == "__main__":
    main()
