# Water AI Research Kit

Small, auditable building blocks extracted from an exploratory AI retrieval project, with a new synthetic time-series example for future water-engineering research.

Python 3.10+; no third-party runtime dependencies; CPU and offline execution.
This is research infrastructure and established baselines, with no new-algorithm claim and no real-world hydrological validation.

## Run

From the project root:

```bash
python3 -m unittest discover -s tests -v
python3 -m water_ai_research demo --output outputs/first-run
python3 -m water_ai_research verify outputs/first-run
```

Use a fresh output directory for each run. Installation is optional:

```bash
python3 -m pip install -e .
water-ai demo --output outputs/installed-run
```

Installing may download build tools. Direct module execution needs only Python.
The distribution is not published on PyPI.

## Included

- BM25, reciprocal rank fusion, and MMR with an auditable greedy trace.
- Retrieval metrics with explicit handling of empty and missing gold IDs.
- MAE, RMSE, and Nash–Sutcliffe efficiency; undefined NSE stays `None`.
- Streaming SHA-256 manifests and normalized cross-split text duplicate checks.
- Transitive identity components and group-disjointness checks.
- Conservative temporal windows whose complete input/target support stays inside one split.
- Finite, whole-group label-view sensitivity for additive mean differences.
- Deterministic synthetic series, one-step persistence baseline, and artifact verification.

Scores tied in ranking use original input order. RRF uses one-based ranks and
first-seen ID order for ties. Empty gold queries are unscored, not verified
negatives. Gold IDs missing from the candidate pool remain in recall denominators.
Reciprocal rank uses the full supplied list; other retrieval metrics use top-k.
The default text tokenizer does not perform Chinese word segmentation.

## Scope

No datasets, pretrained weights, upstream author code, private documents or
personal information are redistributed. The water example and forecasting
metrics were added during packaging and have only synthetic validation. This is
not a calibrated hydrological model or a physical simulator. Group and temporal
checks detect only the identities and ordering explicitly supplied by the caller.
Label-view ranges are not confidence intervals or bounds on true labels.

Code was developed with AI assistance and should be inspected and validated for
each downstream experiment. See [provenance and references](docs/PROVENANCE.md),
[water-data integration guide](docs/WATER_AI_GUIDE.md), and the
[experiment template](docs/EXPERIMENT_TEMPLATE.md). The primary documentation is
[in Chinese](README.md). Original code and documentation use the [MIT license](LICENSE).
