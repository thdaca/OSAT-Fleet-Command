"""Small deterministic descriptive and binary-classification metrics."""
from __future__ import annotations
import math
from typing import Sequence
import numpy as np
def _average_ranks(values: Sequence[float]) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    order = np.argsort(array, kind="mergesort")
    result = np.empty(len(array), dtype=np.float64)
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and array[order[end]] == array[order[start]]:
            end += 1
        result[order[start:end]] = (start + end - 1) / 2.0
        start = end
    return result


def _spearman(first: Sequence[float], second: Sequence[float]) -> float | None:
    if len(first) < 3 or len(first) != len(second):
        return None
    ranked_first = _average_ranks(first)
    ranked_second = _average_ranks(second)
    if float(np.std(ranked_first)) == 0.0 or float(np.std(ranked_second)) == 0.0:
        return None
    return float(np.corrcoef(ranked_first, ranked_second)[0, 1])


def _percentile(values: Sequence[float], percentile: float) -> float | None:
    if not values:
        return None
    return float(np.percentile(np.asarray(values, dtype=np.float64), percentile))
def _binary_threshold_metrics(
    labels: Sequence[int], scores: Sequence[float], threshold: float
) -> dict[str, int | float | None]:
    truth = np.asarray(labels, dtype=np.int8)
    predicted = np.asarray(scores, dtype=np.float64) >= threshold
    positive = truth == 1
    negative = ~positive
    tp = int(np.sum(predicted & positive))
    fp = int(np.sum(predicted & negative))
    tn = int(np.sum(~predicted & negative))
    fn = int(np.sum(~predicted & positive))
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    specificity = tn / (tn + fp) if tn + fp else None
    f1 = (
        2.0 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and precision + recall
        else None
    )
    balanced_accuracy = (
        (recall + specificity) / 2.0
        if recall is not None and specificity is not None
        else None
    )
    denominator = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    mcc = (tp * tn - fp * fn) / denominator if denominator else None
    return {
        "threshold": threshold,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "balanced_accuracy": balanced_accuracy,
        "mcc": mcc,
    }


def _continuous_binary_metrics(
    labels: Sequence[int], scores: Sequence[float]
) -> dict[str, float | None]:
    truth = np.asarray(labels, dtype=np.int8)
    values = np.asarray(scores, dtype=np.float64)
    positives = int(np.sum(truth == 1))
    negatives = int(np.sum(truth == 0))
    if positives == 0 or negatives == 0:
        return {"auroc": None, "average_precision": None}
    ranks = _average_ranks(values)
    rank_sum = float(np.sum(ranks[truth == 1]))
    auroc = (rank_sum - positives * (positives - 1) / 2.0) / (
        positives * negatives
    )
    order = np.argsort(-values, kind="mergesort")
    sorted_scores = values[order]
    sorted_truth = truth[order]
    cumulative_positive = 0
    average_precision = 0.0
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and sorted_scores[end] == sorted_scores[start]:
            end += 1
        group_positive = int(np.sum(sorted_truth[start:end] == 1))
        cumulative_positive += group_positive
        average_precision += (
            group_positive / positives * cumulative_positive / end
        )
        start = end
    return {"auroc": float(auroc), "average_precision": average_precision}


def _score_distribution(values: Sequence[float]) -> dict[str, int | float | None]:
    if not values:
        return {
            "count": 0,
            "minimum": None,
            "median": None,
            "p95": None,
            "maximum": None,
        }
    array = np.asarray(values, dtype=np.float64)
    return {
        "count": len(array),
        "minimum": float(np.min(array)),
        "median": float(np.median(array)),
        "p95": float(np.percentile(array, 95.0)),
        "maximum": float(np.max(array)),
    }
