"""Split audit helpers. Basin/station grouping and time describe different tests."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass


def connected_components(identities: Sequence[Sequence[str]]) -> list[int]:
    """Connect rows sharing any identity, including transitive links.

    Supply basin IDs, source-work IDs or normalized text hashes as appropriate.
    Empty identity lists remain separate components. Labels use first-row order.
    """
    parent = list(range(len(identities)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    seen: dict[str, int] = {}
    for i, values in enumerate(identities):
        for value in values:
            if not isinstance(value, str) or not value:
                raise ValueError("identity values must be nonempty strings")
            if value in seen:
                a, b = find(i), find(seen[value])
                parent[max(a, b)] = min(a, b)
            else:
                seen[value] = i
    labels: dict[int, int] = {}
    return [labels.setdefault(find(i), len(labels)) for i in range(len(parent))]


def assert_disjoint_groups(partitions: Mapping[str, Sequence[str | int]]) -> None:
    """Raise when a supplied station, basin or component ID spans splits."""
    owner = {}
    for split, groups in partitions.items():
        for group in set(groups):
            if group in owner and owner[group] != split:
                raise ValueError(f"group {group!r} occurs in {owner[group]!r} and {split!r}")
            owner[group] = split


@dataclass(frozen=True)
class Window:
    input_start: int
    input_stop: int
    target_start: int
    target_stop: int


def temporal_windows(
    n: int, lookback: int, horizon: int, train_end: int, validation_end: int, gap: int = 0
) -> dict[str, list[Window]]:
    """Split a single ordered regular series BEFORE constructing windows.

    All intervals are half-open. Training owns [0, train_end), validation owns
    [train_end+gap, validation_end), test owns [validation_end+gap, n).
    Input AND target must fit in one interval: no shared raw observations across
    splits. This deliberately conservative policy discards boundary windows.
    gap counts observations, not time. Call separately per continuous station;
    validate order, missing timesteps and sampling frequency before this call.
    """
    for name, value in {"n": n, "lookback": lookback, "horizon": horizon,
                        "train_end": train_end, "validation_end": validation_end,
                        "gap": gap}.items():
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name} must be an integer")
    if not (n > 0 and lookback > 0 and horizon > 0 and gap >= 0
            and 0 < train_end < validation_end < n):
        raise ValueError("invalid series length, window length or boundaries")
    if train_end + gap > validation_end or validation_end + gap > n:
        raise ValueError("gap exceeds a split interval")
    intervals = {"train": (0, train_end), "validation": (train_end + gap, validation_end),
                 "test": (validation_end + gap, n)}
    return {
        name: [Window(end - lookback, end, end, end + horizon)
               for end in range(start + lookback, stop - horizon + 1)]
        for name, (start, stop) in intervals.items()
    }
