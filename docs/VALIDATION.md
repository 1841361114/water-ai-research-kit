# v0.1.0 validation record

## Completed locally

- 28 standard-library unit/integration tests passed on Python 3.12.14.
- Tests cover hand-calculated BM25 and regression scores, ranking ties, RRF
  one-based ranks, MMR endpoints and trace, missing/empty gold semantics,
  Unicode duplicate identities, transitive groups, raw-observation isolation,
  manifest tampering/path escapes, JSON float round trips, and repeatable demo
  outputs.
- Finite grouped-view bounds were checked against a separate exhaustive
  enumeration of allowed group-view combinations on a constructed fixture.
- The offline CLI demo and output-manifest verification completed successfully.
- A wheel was built locally without downloading runtime dependencies.
- That wheel was installed into a fresh virtual environment; the installed
  `water-ai` command ran the demo and verified its output outside the source tree.
- All Python sources parsed with the Python 3.10 grammar. This is a syntax
  compatibility check, not a Python 3.10 runtime test.

## Not established

- No real hydrological dataset evaluation, learned forecasting model, physical
  simulation, or downstream scientific result is included.
- No claim of performance improvement, novel algorithm, independent scientific
  replication or peer review is made.
- Python 3.10 is the minimum target; this local validation used Python 3.12.
- The GitHub Actions workflow is included. Its hosted status must be checked
  after publication; a local pass does not imply hosted CI has already run.

Run the checks again with:

```bash
python3 -m unittest discover -s tests -v
python3 -m water_ai_research demo --output outputs/validation-run
python3 -m water_ai_research verify outputs/validation-run
```
