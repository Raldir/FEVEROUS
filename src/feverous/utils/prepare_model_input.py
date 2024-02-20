from typing import Dict, List
import random

from feverous.database.feverous_db import FeverousDB
from feverous.utils.log_helper import LogHelper
from feverous.utils.util import (
    get_evidence_by_page,
    get_evidence_by_table,
    get_evidence_text_by_id,
    get_wikipage_by_id,
)

LogHelper.setup()
logger = LogHelper.get_logger(__name__)


def group_evidence_by_header(table: List[str], db: FeverousDB):
    """
    Groups evidence into a dict with a key being the cell header and the values the cells associated with the header. Also returns whether the content of a cell header is a string or number.
    @param table: Content of table
    """

    def calculate_header_type(header_content):
        real_count = 0
        text_count = 0
        for ele in header_content:
            if ele.replace(".", "", 1).isdigit():
                real_count += 1
            else:
                text_count += 1
        if real_count >= text_count:
            return "real"
        else:
            return "text"

    cell_headers = {}
    for ele in table:
        if "header_cell_" in ele:
            continue  # Ignore evidence header cells for now, probably an exception anyways
        else:
            wiki_page, _ = get_wikipage_by_id(ele, db)
            cell_header_ele = [
                ele.split("_")[0] + "_" + el.get_id().replace("hc_", "header_cell_")
                for el in wiki_page.get_context("_".join(ele.split("_")[1:]))
                if "header_cell_" in el.get_id()
            ]
            for head in cell_header_ele:
                if head in cell_headers:
                    cell_headers[head].append(get_evidence_text_by_id(ele, wiki_page))
                else:
                    cell_headers[head] = [get_evidence_text_by_id(ele, wiki_page)]
    cell_headers_type = {}
    for ele, value in cell_headers.items():
        cell_headers[ele] = set(value)

    for key, item in cell_headers.items():
        cell_headers_type[key] = calculate_header_type(item)

    return cell_headers, cell_headers_type


def prepare_input_schlichtkrull(annotation: Dict[str, any], has_gold: bool, db: FeverousDB) -> str:
    """
    Formats the input of textual and tabular data by linearzing tabular data and concatentating it to sentence evidence.
    @param annotation: Annotation json object, containing fields for claim and evidence
    @param has_gold: Whether to consider gold evidence annotations of the input annotation object
    """
    sequence = [annotation.claim]
    if has_gold:
        evidence_gold = annotation.flat_evidence
        evidence_pred = annotation.predicted_evidence
        evidence_pred = [x for x in evidence_pred if x not in evidence_gold][:3]

        # Adding noise to gold data to make model more robust
        adding_noise_prob = 0.125
        evidence_combined = []
        count = 0
        for i, evidence in enumerate(evidence_gold):
            rand_ceil = adding_noise_prob * ((i + 1))  # Adding more noise the larger index
            rand = random.uniform(0, 1)
            if rand < rand_ceil and count < len(evidence_pred):
                evidence_combined.append(evidence_pred[count])
                count += 1
            evidence_combined.append(evidence)

        evidence_by_page = get_evidence_by_page(evidence_combined)
    else:
        evidence_by_page = get_evidence_by_page(annotation.predicted_evidence)
    for ele in evidence_by_page:
        for evid in ele:
            wiki_page, _ = get_wikipage_by_id(evid, db)
            if "_sentence_" in evid:
                sequence.append(
                    ". ".join([str(context) for context in wiki_page.get_context(evid)[1:]])
                    + " "
                    + get_evidence_text_by_id(evid, wiki_page)
                )
        tables = get_evidence_by_table(ele)

        for table in tables:
            sequence += linearize_cell_evidence(table, db)

    return " </s> ".join(sequence)


def linearize_cell_evidence(table: List[str], db: FeverousDB) -> List[str]:
    """
    @param table: All evidence elements in a given table
    @return: A list of evidence elements (cells and captions), linearized into a human readable string representation in teh format [Header1] is [Content] ; [Header1] is [Content]. [Header2] ...
    """
    context = []
    caption_id = [ele for ele in table if "_caption_" in ele]
    context.append(table[0].split("_")[0])
    if len(caption_id) > 0:
        wiki_page, _ = get_wikipage_by_id(caption_id[0], db)
        context.append(get_evidence_text_by_id(caption_id[0], wiki_page))

    cell_headers, cell_headers_type = group_evidence_by_header(table, db)

    # Iterate over each header, and linearize header and all of its cells
    for key, values in cell_headers.items():
        wiki_page, _ = get_wikipage_by_id(key, db)
        lin = ""
        key_text = get_evidence_text_by_id(key, wiki_page)
        for i, value in enumerate(values):
            lin += key_text.split("[H] ")[1].strip() + " is " + value
            if i + 1 < len(values):
                lin += " ; "
            else:
                lin += "."

        context.append(lin)
    return context


def prepare_input(annotation, model_name, db, gold=False):
    assert model_name in [
        "schlichtkrull"
    ], "Input formatting strategy not supported. Requested {}, but available options are {}.".fomrat(
        model_name, " ".join(["schlichtkrull"])
    )

    if model_name == "schlichtkrull":
        return prepare_input_schlichtkrull(annotation, gold, db)
