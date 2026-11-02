"""Explicit metrics; unlabelled queries and undefined scores stay visible."""

import math
from collections.abc import Sequence


def retrieval_metrics(
    ranking: Sequence[str], gold: set[str], k: int = 10
) -> dict[str, float | int] | None:
    """Recall/Hit/All-gold@k and full-list reciprocal rank.

    Empty gold returns None (unscored), not a verified negative. Missing gold
    IDs remain in the recall denominator. Duplicate predicted IDs are rejected.
    """
    if isinstance(k, bool) or not isinstance(k, int) or k <= 0:
        raise ValueError("k must be a positive integer")
    if len(set(ranking)) != len(ranking):
        raise ValueError("ranking must have unique IDs")
    if not gold:
        return None
    selected = set(ranking[:k])
    hits = len(selected & gold)
    first = next((rank for rank, item in enumerate(ranking, 1) if item in gold), None)
    return {
        "gold_count": len(gold), "hits_at_k": hits,
        "recall_at_k": hits / len(gold), "hit_at_k": int(hits > 0),
        "all_gold_at_k": int(gold <= selected),
        "reciprocal_rank": 1 / first if first is not None else 0.0,
    }


def regression_metrics(
    observed: Sequence[float], predicted: Sequence[float]
) -> dict[str, float | int | None]:
    """MAE, RMSE and Nash-Sutcliffe efficiency on finite paired observations.

    No silent NaN dropping. NSE is None for constant observations, whose
    variance denominator is zero. No clipping of negative NSE values.
    """
    if not observed or len(observed) != len(predicted):
        raise ValueError("observed and predicted must have equal, nonzero length")
    obs, pred = list(map(float, observed)), list(map(float, predicted))
    if not all(math.isfinite(v) for v in obs + pred):
        raise ValueError("observations and predictions must be finite")
    errors = [p - o for o, p in zip(obs, pred)]
    n = len(obs)
    mean = math.fsum(obs) / n
    squared_error = math.fsum(e * e for e in errors)
    variance = math.fsum((o - mean) ** 2 for o in obs)
    return {
        "n": n, "mae": math.fsum(abs(e) for e in errors) / n,
        "rmse": math.sqrt(squared_error / n),
        "nse": 1 - squared_error / variance if variance else None,
    }
