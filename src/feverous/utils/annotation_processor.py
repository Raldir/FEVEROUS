"""
Simple Annotation Wrapper that converts each annotation into an object with corresponding attributes.
"""

import json
import sys
import os
import jsonlines
import traceback
import logging
from tqdm import tqdm
import pickle
import itertools
import linecache
import html
import re
from enum import Enum

from utils.util import *
from baseline.drqa.tokenizers.spacy_tokenizer import SpacyTokenizer
TOKENIZER = SpacyTokenizer(annotators=set(['ner']))

from utils.log_helper import LogHelper

LogHelper.setup()
logger = LogHelper.get_logger(__name__)



class AnnotationProcessor:
    """
    Args:
        annotators: input_path to the annotation .jsonl
    """
    def __init__(self, input_path, has_content=False):
        self.input_path = input_path
        self.has_content = has_content
        self.annotations = self.process_annotations()

    def __iter__(self):
        return self.annotations

    def __next__(self):
        return next(self.annotations)

    def process_annotations(self):
        with jsonlines.open(self.input_path) as f:
             for i,line in enumerate(f.iter()):
                 if i == 0: continue # skip header line
                 # if len(line['evidence'][0]['content']) == 0: continue
                 if i == 1:
                     if 'evidence' not in line:
                         logger.info('No gold evidence found in the input.')
                 try:
                     yield Annotation(line, self.has_content)
                 except:
                     traceback.print_exc()
                     logger.error('Error while processing Annotation {}'.format(line['id']))
                     continue

class EvidenceType(Enum):
    SENTENCE = 0
    TABLE = 1
    LIST = 2
    JOINT = 3

class Annotation:
    def __init__(self, annotation_json, has_content):
        self.annotation_json = annotation_json
        self.has_content = has_content
        self.convert_json_to_object(annotation_json)

    def convert_json_to_object(self, annotation_json):
        self.claim = annotation_json['claim']
        if 'evidence' in annotation_json:
            self.verdict = annotation_json['label'] if 'label' in annotation_json else None
            self.evidence = [el['content'] for el in annotation_json['evidence']]
            self.flat_evidence = list(itertools.chain.from_iterable(self.evidence))
            self.titles = [[el.split('_')[0] for el in set] for set in self.evidence]
            self.flat_titles =  [el.split('_')[0] for el in self.flat_evidence]
            # self.flat_evidence = list(map(process_id, list(itertools.chain.from_iterable(self.evidence))))
            self.context = [el['context'] for el in annotation_json['evidence']]
            self.flat_context = {}
            for ele in self.context:
                self.flat_context.update(ele)
            # self.flat_context = [set(list(map(process_id, el))) for el in self.flat_context]
            self.num_evidence = len(self.evidence)
            self.operations = annotation_json['annotator_operations']
        else:
            self.verdict = 'SUPPORTS' #dummy label
        if 'id' in annotation_json:
            self.id = annotation_json['id']
        # else:
        #     print('No gold evidence found in the input.')
            # self.claim = annotation_json['claim']
        if 'predicted_evidence' in annotation_json:
            self.predicted_evidence = annotation_json['predicted_evidence']
        if 'predicted_verdict' in annotation_json:
            self.predicted_vertdict = annotation_json['predicted_verdict']
        # self.source = annotation_json['source']
        if self.has_content:
            # print(annotation_json['evidence'])
            try:
                self.evidence_content = [el['text'] for el in annotation_json['evidence']]
                self.flat_evidence_content = list(itertools.chain.from_iterable(self.evidence_content))
            except Exception:
                self.flat_evidence_content = []
            # print(self.evidence_content)
            if len(self.flat_evidence) != len(self.flat_evidence_content):
                self.flat_evidence_content = None
                return
            self.flat_evidence_content_map = {ele: self.flat_evidence_content[i] for i,ele in enumerate(self.flat_evidence)}
            self.context_content  = [el['context_text'] for el in annotation_json['evidence']]
            self.flat_context_content = {}
            for ele in self.context_content:
                self.flat_context_content.update(ele)
            self.flat_context_content_inverse = {}
            for key, values in self.flat_context.items():
                for i,value in enumerate(values):
                    self.flat_context_content_inverse[value] = self.flat_context_content[key][i]


    def get_evidence_text_by_id(self, id):
        return self.flat_evidence_content_map[id]

    def get_context_text_by_id(self, id):
        return self.flat_context_content[id]

    def get_context_text_by_context_id(self, id):
        return self.flat_context_content_inverse[id]

    def get_evidence_content(self):
        return self.evidence_content

    def get_context_content(self):
        return self.context_content

    def get_annotation_json(self):
        return self.annotation_json

    def get_tokenized_claim(self):
        return TOKENIZER.tokenize(self.claim)

    def get_claim_entities(self):
        return TOKENIZER.tokenize(self.claim).entity_groups()

    def get_claim(self):
        return self.claim

    def get_evidence(self,flat=False):
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
        types = []
        for evid_set in self.evidence:
            type_set = set([])
            for ev in evid_set:
                if '_cell_' in ev:
                    type_set.add('TABLE')
                elif '_sentence_' in ev:
                    type_set.add('SENTENCE')
                elif '_item_' in ev:
                    type_set.add('LIST')
                elif '_caption_' in ev:
                    type_set.add('TABLE')
            if len(type_set) > 1:
                types.append(EvidenceType['JOINT'])
            else:
                types.append(EvidenceType[type_set.pop()])
        if not flat:
            return types
        else:
            if len(types) > 1:
                return EvidenceType['JOINT']
            else:
                return types[0]

def get_annotation_evidence(input_path):
    annotations = AnnotationProcessor(os.path.join(input_path, 'annotations', 'annotations_230421.jsonl'))
    cell_evidence = set([])
    annotation_titles = set([])
    annotations = [anno for anno in annotations]
    anno_evidence = list(itertools.chain.from_iterable([anno.flat_evidence for anno in annotations]))
    annotation_titles =  list(itertools.chain.from_iterable([anno.flat_titles for anno in annotations]))
    anno_context = list(itertools.chain.from_iterable([anno.flat_context for anno in annotations]))
    return anno_evidence, annotation_titles, anno_context

def get_annotation_claims(input_path):
    annotations = AnnotationProcessor(os.path.join(input_path, 'annotations', 'annotations_230421.jsonl'))
    annotations = [anno for anno in annotations]
    anno_claims = [anno.get_tokenized_claim() for anno in annotations]
    print([list(zip(tok.words(), tok.entities())) for tok in anno_claims])

def main():
    input_path = sys.argv[1]
    annotations = AnnotationProcessor(os.path.join(input_path, 'annotations', 'annotations_230421.jsonl'))
    get_annotation_claims(input_path)

if __name__ == "__main__":
    main()
