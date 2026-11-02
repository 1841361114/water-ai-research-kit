"""Finite label-view sensitivity from the exploratory annotation audit."""

import math
from collections.abc import Mapping, Sequence


def grouped_view_bounds(
    group_sums: Mapping[str, Sequence[float]], query_count: int
) -> dict[str, float]:
    """Bounds of an additive mean gain under independent whole-group switches.

    Each group supplies one SUM of per-query method differences for each allowed
    label view, over exactly the same fixed queries. One whole view is selected
    per group. Bounds are not confidence intervals, significance or truth bounds.
    Fixed groups can supply one value. Nonadditive metrics such as corpus AUC
    cannot be passed as group sums. The caller must establish cohort consistency.
    """
    if isinstance(query_count, bool) or not isinstance(query_count, int) or query_count <= 0:
        raise ValueError("query_count must be a positive integer")
    if not group_sums:
        raise ValueError("at least one group is required")
    groups = [list(map(float, values)) for values in group_sums.values()]
    if any(not values or not all(math.isfinite(v) for v in values) for values in groups):
        raise ValueError("every group needs nonempty, finite view sums")
    return {
        "lower": math.fsum(min(values) for values in groups) / query_count,
        "upper": math.fsum(max(values) for values in groups) / query_count,
    }
