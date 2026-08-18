# Data directory

Datasets are cached here and are **not committed** (see `.gitignore`);
only this README is tracked.

## Credit-card fraud dataset (real)

Fetch on a machine with open network access:

```bash
python scripts/fetch_fraud_data.py
```

The script resolves OpenML dataset **1597 ("creditcard")** — the ULB
Machine Learning Group dataset introduced by Dal Pozzolo et al. (2015),
*Calibrating Probability with Undersampling for Unbalanced
Classification* — downloads it to `data/creditcard.csv`, records a
trust-on-first-use sha256 sidecar, and verifies the published invariants
(284,807 rows, 492 frauds, 31 columns). Already have the CSV (e.g. from
Kaggle)? `python scripts/fetch_fraud_data.py --file path/to/creditcard.csv`.

**License:** distributed via OpenML/Kaggle under the source's public
license — check the OpenML dataset page before redistributing; do not
commit the data to this repository.

## Synthetic sample (for pipeline development)

```bash
python scripts/fetch_fraud_data.py --synthetic 5000 --seed 0
```

Same schema, planted logistic ground truth, seeded and deterministic,
written as `creditcard_synthetic_seed<seed>.csv` with a `.meta.json`
sidecar marking it synthetic. Use it to run the E2–E4 pipeline anywhere;
results on it are development results, never paper results.
