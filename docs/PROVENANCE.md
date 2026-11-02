# Code provenance and research boundaries

This repository is a curated refactor, not a release of the entire exploratory
archive. No third-party source implementation has been copied into this package.
Algorithm ideas remain credited to their original publications.

## Extraction map

| Original exploratory file | SHA-256 of archived source | Public adaptation |
|---|---|---|
| `round16_trove_provenance/retrieve.py` | `446e9b4c7e15062c9bc3c0af7c96fbc4fac64235813856dc22d05d5366858d3c` | BM25 and retrieval-metric conventions, separated from dataset/model paths |
| `round17_coverage_controls/controls.py` | `913ec51d751ee968e23a16997f54d11f430904b09e0e8fb79ba757300d0fc6dc` | RRF and MMR with reusable interfaces and explicit tie rules |
| `round19_topic_review/audit.py` | `32cf4dc3d79962da98c8fd1a808c3ea006cc2c0cce9d98312ca9084b0a8c26aa` | Generic grouped, finite label-view sensitivity |

These hashes identify source files in the retained private working archive;
they are provenance notes, not proof of ownership or an external peer review.
The archive itself is not redistributed here.

## Refactor changes

- Standard-library implementations replace NumPy/Pandas dependencies. Floating
  summation can differ in low bits; this is not a promise of bit-identical
  reproduction of all prior experiment tables.
- BM25 retains positive IDF, k1=1.5, b=0.75, and distinct query terms. Empty inputs
  and invalid parameters now have explicit behavior.
- RRF now accepts ID rankings, including incomplete lists. Default constant is
  60 and ranks start at one. Ties follow first appearance, explicitly documented.
- MMR receives a supplied pool as its input, and its indices refer to that pool.
  Similarities are clipped to [0,1]. Ties use pool order. To retain original
  candidate-index tie behavior, supply the pool in original candidate order.
  Relevance normalization is the caller's responsibility.
- Text identity checks newly use NFC + Unicode casefold + whitespace collapse.
  They are not the old experimental corpus's complete cleaning pipeline.
- Generic connected components, temporal windows, regression metrics, JSON CLI,
  synthetic station example, packaging, and tests were added during extraction.
  They have not been evaluated on real water-engineering datasets.

The exploratory work found no established novel algorithmic contribution.
Known-method gains and failed reranker configurations are not advertised as
new discoveries. The tests here validate implementation behavior; they do not
replace independent scientific evaluation.

## Algorithm references

- BM25: Robertson and Zaragoza, *The Probabilistic Relevance Framework: BM25 and
  Beyond* (2009), [publisher DOI](https://doi.org/10.1561/1500000019).
- RRF: Cormack, Clarke and Buettcher, *Reciprocal Rank Fusion Outperforms Condorcet
  and Individual Rank Learning Methods* (SIGIR 2009),
  [author-hosted paper](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf).
- MMR: Carbonell and Goldstein, *The Use of MMR, Diversity-Based Reranking for
  Reordering Documents and Producing Summaries* (SIGIR 1998),
  [author-hosted paper](https://www.cs.cmu.edu/afs/cs/Web/People/jgc/publication/MMR_DiversityBased_Reranking_SIGIR_1998.pdf).
- NSE: Nash and Sutcliffe, *River Flow Forecasting Through Conceptual Models
  Part I — A Discussion of Principles* (1970),
  [publisher DOI](https://doi.org/10.1016/0022-1694(70)90255-6).

The finite grouped-view bound is an elementary min/max calculation for an
additive objective, not a proposed new estimator or statistical inference method.

## Not redistributed

TROVE, PAN, PlagBench, PAWS, pretrained encoders, external author alignment
implementations, and original exploratory result files are excluded. Anyone
adding them must separately check each upstream license and data permission.
The MIT license here does not grant rights to outside datasets or publications.
