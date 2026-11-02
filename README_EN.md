# Water AI Research Kit

Python experiment utilities for water-engineering and AI research: check dataset splits, run small retrieval baselines, evaluate predictions, and track the files used in a run.

For example, given an ordered station series, the toolkit can return train,
validation and test window indices whose complete raw-observation support stays
inside one split. Given your own model's observations and predictions, it can
calculate errors. Data loading, cleaning and model training are supplied by you.

Python 3.10+; no third-party runtime dependencies; CPU and offline execution.
This is research infrastructure and established baselines, with no new-algorithm claim and no real-world hydrological validation.

## Run

From the project root:

```bash
git clone https://github.com/1841361114/water-ai-research-kit.git
cd water-ai-research-kit
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

The demo creates 240 invented observations, produces 132/34/34 one-step
train/validation/test samples, evaluates a last-observation persistence baseline,
and ranks four invented water-related notes. It writes `series.json` (data),
`protocol.json` (split/window settings), `report.json` (metrics and rankings), and
`manifest.json` (file sizes and hashes). These outputs demonstrate the workflow;
they are not real-world forecasting evidence.

## Inputs and outputs

| Task | Input | Output |
|---|---|---|
| Check group leakage | Split names and station/basin/source IDs | Pass or an overlap error |
| Construct time windows | Series length, split boundaries, lookback, horizon, gap | Input/target slice indices by split |
| Evaluate predictions | Aligned observed and predicted values | MAE, RMSE, NSE and sample count |
| Retrieve or fuse evidence | Candidate text and query, or existing ID rankings | Scores, ordered IDs, or MMR selection traces |
| Evaluate retrieval | Ranked IDs and annotated correct IDs | Recall, hit, all-gold and reciprocal rank |
| Track file changes | An explicit file allowlist | Hash manifest and subsequent verification |
| Check annotation-view sensitivity | Fixed-cohort group/view gain sums | Finite lower/upper average gains |

Detailed examples and edge cases are explained in the
[Chinese function guide](docs/FUNCTIONS_zh.md).

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
