"""Small CPU baselines adapted from the exploratory retrieval project.

Ranking ties preserve input order. Tokenization is deliberately simple; pass a
domain-specific tokenizer to BM25 for Chinese segmentation or technical terms.
"""

import math
import re
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass


def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def _count(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")


def _finite(values: Sequence[float]) -> list[float]:
    result = [float(v) for v in values]
    if not all(math.isfinite(v) for v in result):
        raise ValueError("scores must be finite")
    return result


def rank_scores(scores: Sequence[float], k: int | None = None) -> list[int]:
    """Descending score; equal scores use ascending original candidate index."""
    values = _finite(scores)
    if k is not None:
        _count(k, "k")
    return sorted(range(len(values)), key=lambda i: (-values[i], i))[:k]


class BM25:
    """Positive-IDF BM25, k1=1.5, b=0.75; query terms count once.

    Fit on the candidate collection only. Fitting on train/test together is an
    experimental choice and must be reported; this class cannot detect it.
    """

    def __init__(
        self,
        documents: Sequence[str],
        k1: float = 1.5,
        b: float = 0.75,
        tokenizer: Callable[[str], list[str]] = tokenize,
    ):
        if not math.isfinite(k1) or k1 <= 0:
            raise ValueError("k1 must be positive and finite")
        if not math.isfinite(b) or not 0 <= b <= 1:
            raise ValueError("b must be between 0 and 1")
        self.k1, self.b, self.tokenizer = k1, b, tokenizer
        self.counts = [Counter(tokenizer(s)) for s in documents]
        self.lengths = [sum(c.values()) for c in self.counts]
        self.average_length = sum(self.lengths) / len(self.lengths) if self.lengths else 0.0
        self.df = Counter(word for count in self.counts for word in count)

    def score(self, query: str) -> list[float]:
        words = sorted(set(self.tokenizer(query)))
        n = len(self.counts)
        if not self.average_length:
            return [0.0] * n
        scores = []
        for count, length in zip(self.counts, self.lengths):
            norm = self.k1 * (1 - self.b + self.b * length / self.average_length)
            scores.append(math.fsum(
                math.log1p((n - self.df[w] + 0.5) / (self.df[w] + 0.5))
                * count[w] * (self.k1 + 1) / (count[w] + norm)
                for w in words if count[w]
            ))
        return scores


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[str]], rank_constant: float = 60.0
) -> list[tuple[str, float]]:
    """Fuse possibly incomplete, unique-ID lists using one-based ranks.

    An absent ID contributes zero. Equal fused scores use first-seen order
    across input lists, so callers must freeze their input list order.
    """
    if not math.isfinite(rank_constant) or rank_constant < 0:
        raise ValueError("rank_constant must be finite and nonnegative")
    scores: dict[str, float] = {}
    for ranking in rankings:
        if len(set(ranking)) != len(ranking):
            raise ValueError("each input ranking must contain unique IDs")
        for rank, item in enumerate(ranking, 1):
            scores[item] = scores.get(item, 0.0) + 1 / (rank_constant + rank)
    return sorted(scores.items(), key=lambda pair: -pair[1])


@dataclass(frozen=True)
class SelectionStep:
    index: int
    relevance: float
    redundancy: float
    gain: float


def mmr_select(
    relevance: Sequence[float],
    similarity: Sequence[Sequence[float]],
    k: int = 10,
    weight: float = 0.7,
) -> list[SelectionStep]:
    """Greedy MMR over an already chosen candidate pool, with an audit trace.

    Similarity must be an n-by-n finite matrix, clipped here to [0, 1].
    Relevance is NOT normalized internally: callers choose its scale. Candidate
    order breaks ties; the returned index is relative to the supplied pool.
    This selector is a baseline, with no guaranteed improvement in recall.
    """
    _count(k, "k")
    if not math.isfinite(weight) or not 0 <= weight <= 1:
        raise ValueError("weight must be between 0 and 1")
    rel = _finite(relevance)
    n = len(rel)
    if len(similarity) != n or any(len(row) != n for row in similarity):
        raise ValueError("similarity must be n by n")
    sim = [[min(1.0, max(0.0, x)) for x in _finite(row)] for row in similarity]
    trace: list[SelectionStep] = []
    chosen: list[int] = []
    available = set(range(n))
    for _ in range(min(k, n)):
        redundancy = [max((sim[i][j] for j in chosen), default=0.0) for i in range(n)]
        gains = [weight * rel[i] - (1 - weight) * redundancy[i] for i in range(n)]
        best = max(available, key=lambda i: (gains[i], -i))
        trace.append(SelectionStep(best, rel[best], redundancy[best], gains[best]))
        chosen.append(best)
        available.remove(best)
    return trace
