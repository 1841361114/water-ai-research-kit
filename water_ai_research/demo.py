"""Synthetic, deterministic workflow example; not a physical hydrology model."""

import json
import math
from dataclasses import asdict
from pathlib import Path

from .audit import build_manifest, verify_manifest, write_json
from .metrics import regression_metrics, retrieval_metrics
from .retrieval import BM25, rank_scores, reciprocal_rank_fusion
from .splits import assert_disjoint_groups, temporal_windows


def run_demo(output: str | Path) -> dict:
    """Write a fixed synthetic station series, conservative split and baselines."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    names = ["series.json", "protocol.json", "report.json", "manifest.json"]
    if any((output / name).exists() for name in names):
        raise FileExistsError("choose a new output directory to preserve the previous run")
    # All observations are invented. The equation is a teaching signal only.
    series = [round(30 + 5 * math.sin(t / 9) + 0.02 * t + (t % 7) / 10, 6)
              for t in range(240)]
    config = {"n": len(series), "lookback": 12, "horizon": 1,
              "train_end": 144, "validation_end": 192, "gap": 2}
    windows = temporal_windows(**config)
    used = {name: sorted({i for w in items for i in range(w.input_start, w.target_stop)})
            for name, items in windows.items()}
    assert_disjoint_groups(used)
    write_json(output / "series.json", {"synthetic": True, "unit": "arbitrary", "values": series})
    write_json(output / "protocol.json", {
        "synthetic": True, "config": config, "raw_index_overlap": False,
        "windows": {name: [asdict(w) for w in items] for name, items in windows.items()},
        "baseline": "one-step persistence: last input observation",
        "fitting": "none", "threshold_selection": "none",
    })
    forecast = {}
    for name, items in windows.items():
        actual = [series[w.target_start] for w in items]
        predicted = [series[w.input_stop - 1] for w in items]
        forecast[name] = regression_metrics(actual, predicted)

    documents = [
        "rainfall runoff forecasting with upstream rainfall observations",
        "turbine vibration monitoring and fault diagnosis",
        "runoff forecast evaluation with chronological data splits",
        "river water quality sampling and laboratory measurements",
    ]
    ids = ["synthetic-note-1", "synthetic-note-2", "synthetic-note-3", "synthetic-note-4"]
    ranking = [ids[i] for i in rank_scores(BM25(documents).score("runoff forecasting rainfall"))]
    fused = reciprocal_rank_fusion([ranking, [ids[2], ids[0], ids[3], ids[1]]])
    report = {
        "synthetic": True, "scientific_validation": False, "forecast": forecast,
        "retrieval": {"bm25_ids": ranking, "rrf_ids": [item for item, _ in fused],
                      "invented_gold_metrics": retrieval_metrics(ranking, {ids[0], ids[2]}, k=2)},
        "limitations": "Synthetic pipeline check only; no learned model or real-world performance claim.",
    }
    write_json(output / "report.json", report)
    manifest = build_manifest(output, names[:-1])
    write_json(output / "manifest.json", manifest)
    verify_manifest(output, json.loads((output / "manifest.json").read_text(encoding="utf-8")))
    return report
