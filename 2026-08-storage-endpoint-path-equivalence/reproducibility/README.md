# Reproduction bundle

This bundle is the smallest sanitized set needed to inspect the published analysis:

- `protocol.json` records the workload and predeclared equivalence margins.
- `block-aggregates.csv` contains the 60 mode/variant block aggregates used for paired analysis.
- `equivalence-verdicts.json` contains all 36 confidence intervals and verdicts.
- `calibration-analysis.json` contains the positive-control result.
- `translator_benchmark.py`, `analyze_results.py`, and `analyze_calibration.py` document the request timing and statistical implementation.

The original analysis used 10,000 cluster-bootstrap resamples by block. The benchmark comprised ten interleaved blocks, 2,400 measured requests, and 1,200 warm-ups. Calibration used 800 measured requests plus 400 warm-ups.

Per-request captures, Azure resource inventories, transition outputs, credentials, live names, identifiers, and public addresses are deliberately not published. The aggregate files are sufficient to audit the reported headline metrics and confidence intervals without exposing the live environment.
