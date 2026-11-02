"""Transparent multilabel metrics and article-cluster bootstrap intervals."""
from collections import Counter, defaultdict
import math
import random


def ratio(a, b):
    return a / b if b else 0.0


def classification(gold, predicted, label_ids):
    if not gold or len(gold) != len(predicted):
        raise ValueError("Equal nonempty gold and prediction lists required")
    allowed = set(label_ids)
    if any((set(x) - allowed) for x in gold + predicted):
        raise ValueError("Unknown label in metric input")
    by_label = {}
    tp_total = fp_total = fn_total = 0
    for label in sorted(label_ids):
        tp = sum(label in g and label in p for g, p in zip(gold, predicted))
        fp = sum(label not in g and label in p for g, p in zip(gold, predicted))
        fn = sum(label in g and label not in p for g, p in zip(gold, predicted))
        precision, recall = ratio(tp, tp + fp), ratio(tp, tp + fn)
        f1 = ratio(2 * tp, 2 * tp + fp + fn)
        by_label[label] = {"precision": precision, "recall": recall, "f1": f1, "support": tp + fn, "tp": tp, "fp": fp, "fn": fn}
        tp_total += tp
        fp_total += fp
        fn_total += fn
    present = [x["f1"] for x in by_label.values() if x["support"] > 0]
    instance_f1 = [ratio(2 * len(set(g) & set(p)), len(set(g)) + len(set(p))) for g, p in zip(gold, predicted)]
    return {"n": len(gold), "macro_f1_all_labels": sum(x["f1"] for x in by_label.values()) / len(by_label),
            "macro_f1_present_gold": sum(present) / len(present) if present else 0.0,
            "micro_f1": ratio(2 * tp_total, 2 * tp_total + fp_total + fn_total),
            "micro_precision": ratio(tp_total, tp_total + fp_total), "micro_recall": ratio(tp_total, tp_total + fn_total),
            "sample_f1_empty_empty_zero": sum(instance_f1) / len(instance_f1),
            "exact_match": sum(set(g) == set(p) for g, p in zip(gold, predicted)) / len(gold),
            "gold_negative_records": sum(not g for g in gold), "by_label": by_label}


def percentile(values, q):
    ordered = sorted(values)
    if not ordered:
        return None
    index = (len(ordered) - 1) * q
    lo, hi = math.floor(index), math.ceil(index)
    return ordered[lo] * (hi - index) + ordered[hi] * (index - lo) if lo != hi else ordered[lo]


def cluster_bootstrap(rows, predictions, labels, iterations=500, seed=42):
    groups = defaultdict(list)
    for i, r in enumerate(rows):
        groups[r["article_id"]].append(i)
    if len(groups) < 2 or iterations < 1:
        return {"interval": None, "reason": "At least two independent articles and one iteration required"}
    keys, rng, scores = sorted(groups), random.Random(seed), []
    for _ in range(iterations):
        idx = [i for key in rng.choices(keys, k=len(keys)) for i in groups[key]]
        scores.append(classification([rows[i]["labels"] for i in idx], [predictions[i] for i in idx], labels)["macro_f1_all_labels"])
    return {"metric": "macro_f1_all_labels", "interval": [percentile(scores, .025), percentile(scores, .975)],
            "iterations": iterations, "seed": seed, "unit": "article", "articles": len(keys),
            "caution": "Exploratory percentile interval; rare-label absence affects macro-F1 in resamples"}


def agreement(rows_a, rows_b, label_ids):
    """Per-label binary Cohen kappa and set agreement before adjudication."""
    if set(rows_a) != set(rows_b) or not rows_a:
        raise ValueError("Annotators must label exactly the same nonempty ID set")
    ids = sorted(rows_a)
    for table in (rows_a, rows_b):
        if any(set(table[i]) - set(label_ids) for i in ids):
            raise ValueError("Unknown annotation label")
    kappas = {}
    for label in sorted(label_ids):
        a = [int(label in rows_a[i]) for i in ids]
        b = [int(label in rows_b[i]) for i in ids]
        observed = sum(x == y for x, y in zip(a, b)) / len(ids)
        pa, pb = sum(a) / len(ids), sum(b) / len(ids)
        expected = pa * pb + (1 - pa) * (1 - pb)
        kappas[label] = None if math.isclose(expected, 1.0) else (observed - expected) / (1 - expected)
    jaccard = [ratio(len(set(rows_a[i]) & set(rows_b[i])), len(set(rows_a[i]) | set(rows_b[i]))) if (rows_a[i] or rows_b[i]) else 1.0 for i in ids]
    return {"n": len(ids), "per_label_binary_cohen_kappa": kappas,
            "set_exact_agreement": sum(set(rows_a[i]) == set(rows_b[i]) for i in ids) / len(ids),
            "mean_set_jaccard_empty_empty_one": sum(jaccard) / len(ids),
            "note": "Binary per-label kappa is not directly comparable with published Krippendorff alpha"}
