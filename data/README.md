# Data directory

Datasets are cached here and are **not committed** (see `.gitignore`);
only this README is tracked.

## Provenance of the copies used for the committed real-data results

Both real datasets were obtained via anonymous git reads of public GitHub
repositories and verified before use:

- **`creditcard.csv`** — ULB credit-card fraud dataset, from the public
  mirror `github.com/nsethi31/Kaggle-Data-Credit-Card-Fraud-Detection`,
  ingested through `scripts/fetch_fraud_data.py --file`, which verified
  the **published invariants** (284,807 rows; 492 frauds, rate 0.00173;
  31 columns; amount statistics matching the literature) and recorded
  sha256 `33a178be6517…` in the sidecar. Provenance paper: Dal Pozzolo
  et al. (2015). License: per the source dataset's page (ODbL-style
  public distribution); do not commit or redistribute from this repo.
- **`bao2020.csv`** — the authors' official replication data for Bao, Ke,
  Li, Yu & Zhang (2020, *Journal of Accounting Research* 58(1)),
  `data_FraudDetection_JAR2020.csv` from
  `github.com/JarFraud/FraudDetection`: 146,045 firm-years (fiscal
  1990–2014), 964 AAER fraud labels (0.66%), 46 columns (Compustat raw
  items + the paper's 14 financial ratios; 19,562 rows have missing
  ratio values and are dropped complete-case by the pipeline). The
  authors request citation of the paper when the data are used — the
  manuscript cites it (`bao2020`).

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
