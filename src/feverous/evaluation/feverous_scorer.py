def check_predicted_evidence_format(instance):
    if "predicted_evidence" in instance.keys() and len(instance["predicted_evidence"]):
        assert all(
            isinstance(prediction, list) for prediction in instance["predicted_evidence"]
        ), "Predicted evidence must be a list of (page,type,position) lists \
            \n e.g. ['Wolfgang Niedecken', 'sentence', '1'] or ['Korean Air', 'cell', '1_19_0']"

        assert all(
            len(prediction) == 3 for prediction in instance["predicted_evidence"]
        ), "Predicted evidence must be a list of (page,type,position) lists \
            \n e.g. ['Wolfgang Niedecken', 'sentence', '1'] or ['Korean Air', 'cell', '1_19_0']"

        assert all(
            isinstance(prediction[0], str) for prediction in instance["predicted_evidence"]
        ), "Predicted evidence must be a list of (page<string>,type<string>,position<string>) lists \
            \n e.g. ['Wolfgang Niedecken', 'sentence', '1'] or ['Korean Air', 'cell', '1_19_0']"

        assert all(
            isinstance(prediction[1], str) for prediction in instance["predicted_evidence"]
        ), "Predicted evidence must be a list of (page<string>,type<string>,position<string>) lists \
            \n e.g. ['Wolfgang Niedecken', 'sentence', '1'] or ['Korean Air', 'cell', '1_19_0']"

        assert all(
            isinstance(prediction[2], str) for prediction in instance["predicted_evidence"]
        ), "Predicted evidence must be a list of (page<string>,type<string>,position<string>) lists \
            \n e.g. ['Wolfgang Niedecken', 'sentence', '1'] or ['Korean Air', 'cell', '1_19_0']"


def truncate_evidence(instance, max_evidence=None, max_evidence_cell=None):
    # Remove evidence of predictions that exceeds maximum number of evidence
    remove_index = set([])
    evidence_cell_count = 0
    evidence_count = 0
    for i, ele in enumerate(instance["predicted_evidence"]):
        if ele[1] in ["cell", "item", "table_caption", "header_cell"]:
            if max_evidence_cell is None:
                continue
            else:
                if evidence_cell_count < max_evidence_cell:
                    evidence_cell_count += 1
                else:
                    remove_index.add(i)
        else:
            if max_evidence is None:
                continue
            else:
                if evidence_count < max_evidence:
                    evidence_count += 1
                else:
                    remove_index.add(i)

    for ele in sorted(remove_index, reverse=True):  # Iterate in reverse order to not throw off subsequent indices
        instance["predicted_evidence"].pop(ele)
    return instance


def is_correct_label(instance):
    return instance["label"].upper() == instance["predicted_label"].upper()


def is_strictly_correct(instance):
    # Strict evidence matching is only for NEI class
    check_predicted_evidence_format(instance)

    if is_correct_label(instance):
        assert "predicted_evidence" in instance, "Predicted evidence must be provided for strict scoring"

        for evience_group in instance["evidence"]:
            # Filter out the annotation ids. We just want the evidence page and line number
            actual_sentences = [[e[0], e[1], e[2]] for e in evience_group]
            # Only return true if an entire group of actual sentences is in the predicted sentences

            if all([actual_sent in instance["predicted_evidence"] for actual_sent in actual_sentences]):
                return True

    return False


def evidence_macro_precision(instance):
    this_precision = 0.0
    this_precision_hits = 0.0

    all_evi = [[e[0], e[1], e[2]] for eg in instance["evidence"] for e in eg if e[0] is not None]

    predicted_evidence = instance["predicted_evidence"]

    for prediction in predicted_evidence:
        if prediction in all_evi:
            this_precision += 1.0
        this_precision_hits += 1.0

    return (this_precision / this_precision_hits) if this_precision_hits > 0 else 1.0, 1.0


def evidence_macro_recall(instance):
    # We only want to score F1/Precision/Recall of recalled evidence for NEI claims
    # If there's no evidence to predict, return 1
    if len(instance["evidence"]) == 0 or all([len(eg) == 0 for eg in instance]):
        return 1.0, 1.0

    predicted_evidence = instance["predicted_evidence"]

    for evidence_group in instance["evidence"]:
        evidence = [[e[0], e[1], e[2]] for e in evidence_group]
        if all([item in predicted_evidence for item in evidence]):
            # We only want to score complete groups of evidence. Incomplete groups are worthless.
            return 1.0, 1.0
    return 0.0, 1.0


# Micro is not used. This code is just included to demostrate our model of macro/micro
def evidence_micro_precision(instance):
    this_precision = 0
    this_precision_hits = 0

    # We only want to score Macro F1/Precision/Recall of recalled evidence for NEI claims
    all_evi = [[e[0], e[1], e[2]] for eg in instance["evidence"] for e in eg if e[0] is not None]

    for prediction in instance["predicted_evidence"]:
        if prediction in all_evi:
            this_precision += 1.0
        this_precision_hits += 1.0

    return this_precision, this_precision_hits


def feverous_score(predictions, actual=None, max_evidence=5, max_evidence_cell=25):
    correct = 0
    strict = 0

    macro_precision = 0
    macro_precision_hits = 0

    macro_recall = 0
    macro_recall_hits = 0

    for idx, instance in enumerate(predictions):
        assert "predicted_evidence" in instance.keys(), "evidence must be provided for the prediction"

        # If it's a blind test set, we need to copy in the values from the actual data
        if "evidence" not in instance or "label" not in instance:
            assert actual is not None, "in blind evaluation mode, actual data must be provided"
            assert len(actual) == len(predictions), "actual data and predicted data length must match"
            assert "evidence" in actual[idx].keys(), "evidence must be provided for the actual evidence"
            instance["evidence"] = actual[idx]["evidence"]
            instance["label"] = actual[idx]["label"]

        assert "evidence" in instance.keys(), "gold evidence must be provided"

        instance = truncate_evidence(instance, max_evidence, max_evidence_cell)

        if is_correct_label(instance):
            correct += 1.0

            if is_strictly_correct(instance):
                strict += 1.0

        macro_prec = evidence_macro_precision(instance)
        macro_precision += macro_prec[0]
        macro_precision_hits += macro_prec[1]

        macro_rec = evidence_macro_recall(instance)
        macro_recall += macro_rec[0]
        macro_recall_hits += macro_rec[1]

    total = len(predictions)

    strict_score = strict / total
    acc_score = correct / total

    pr = (macro_precision / macro_precision_hits) if macro_precision_hits > 0 else 1.0
    rec = (macro_recall / macro_recall_hits) if macro_recall_hits > 0 else 0.0

    f1 = 2.0 * pr * rec / (pr + rec)

    return strict_score, acc_score, pr, rec, f1
