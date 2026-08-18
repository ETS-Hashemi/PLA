"""Fetch, verify, and summarize the credit-card fraud dataset.

Real data: the ULB machine-learning-group credit-card fraud dataset
(Dal Pozzolo et al. 2015, "Calibrating Probability with Undersampling for
Unbalanced Classification"), distributed via OpenML (dataset id 1597,
name "creditcard") under its source's public license — check the OpenML
dataset page for the current license text before redistribution.

Integrity is enforced two ways:
- published invariants: 284,807 rows, 492 fraud labels, 31 columns
  (Time, V1..V28, Amount, Class);
- a trust-on-first-use sha256 sidecar written on first successful load and
  verified on every later load.

Usage:
    python scripts/fetch_fraud_data.py                   # download + verify + stats
    python scripts/fetch_fraud_data.py --file cc.csv     # use a manual download
    python scripts/fetch_fraud_data.py --synthetic 5000  # labeled synthetic sample
    python scripts/fetch_fraud_data.py --stats           # stats of cached data

The development sandbox blocks dataset hosts; run the download on a
machine with open network access. --synthetic generates a clearly-labeled
sample with the same schema (planted logistic ground truth, seeded) so the
downstream pipeline can run end-to-end anywhere.
"""

import argparse
import csv
import hashlib
import json
import math
import pathlib
import random
import shutil
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
CACHE = DATA_DIR / "creditcard.csv"

OPENML_DATASET_ID = 1597
OPENML_DESCRIPTION_URL = (
    f"https://www.openml.org/api/v1/json/data/{OPENML_DATASET_ID}"
)

EXPECTED_COLUMNS = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount", "Class"]
EXPECTED_ROWS = 284_807
EXPECTED_FRAUDS = 492


def sha256_of(path, chunk_size=1 << 20):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def verify_or_record_checksum(path):
    """Trust-on-first-use: record sha256 beside the file, verify later."""
    sidecar = pathlib.Path(f"{path}.sha256")
    actual = sha256_of(path)
    if sidecar.exists():
        recorded = sidecar.read_text().strip()
        if recorded != actual:
            raise ValueError(
                f"checksum mismatch for {path}: recorded {recorded[:12]}…, "
                f"actual {actual[:12]}… — the file changed since first load."
            )
        return actual, "verified"
    sidecar.write_text(actual + "\n")
    return actual, "recorded"


def check_schema(path):
    with open(path, newline="") as handle:
        header = next(csv.reader(handle))
    header = [name.strip().strip('"') for name in header]
    if header != EXPECTED_COLUMNS:
        raise ValueError(
            f"unexpected columns in {path}: got {header[:5]}… "
            f"expected {EXPECTED_COLUMNS[:5]}… (31 columns total)"
        )


def dataset_stats(path):
    rows = 0
    frauds = 0
    amount_sum = 0.0
    amount_max = 0.0
    with open(path, newline="") as handle:
        reader = csv.DictReader(handle)
        for record in reader:
            rows += 1
            label = record["Class"].strip().strip('"').strip("'")
            frauds += 1 if label in ("1", "1.0") else 0
            amount = float(record["Amount"])
            amount_sum += amount
            amount_max = max(amount_max, amount)
    return {
        "rows": rows,
        "frauds": frauds,
        "fraud_rate": frauds / rows if rows else 0.0,
        "amount_mean": amount_sum / rows if rows else 0.0,
        "amount_max": amount_max,
    }


def check_invariants(stats):
    if stats["rows"] != EXPECTED_ROWS or stats["frauds"] != EXPECTED_FRAUDS:
        raise ValueError(
            f"invariant mismatch: {stats['rows']} rows / {stats['frauds']} frauds; "
            f"the published dataset has {EXPECTED_ROWS} rows / {EXPECTED_FRAUDS} frauds."
        )


def resolve_openml_url():
    with urllib.request.urlopen(OPENML_DESCRIPTION_URL, timeout=60) as response:
        description = json.load(response)["data_set_description"]
    if description.get("name") != "creditcard":
        raise ValueError(
            f"OpenML dataset {OPENML_DATASET_ID} is named "
            f"{description.get('name')!r}, expected 'creditcard'."
        )
    return description["url"]


def download(url, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = destination.with_suffix(".part")
    with urllib.request.urlopen(url, timeout=600) as response, open(tmp, "wb") as out:
        shutil.copyfileobj(response, out)
    tmp.rename(destination)


def generate_synthetic(n, seed, destination):
    """Same schema, planted logistic ground truth. Clearly labeled synthetic."""
    rng = random.Random(seed)
    true_weights = [rng.gauss(0.0, 0.8) for _ in range(28)]
    bias = -6.0  # rare positives, like the real data
    destination.parent.mkdir(parents=True, exist_ok=True)
    with open(destination, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(EXPECTED_COLUMNS)
        for i in range(n):
            features = [rng.gauss(0.0, 1.0) for _ in range(28)]
            z = bias + sum(w * x for w, x in zip(true_weights, features))
            label = 1 if rng.random() < 1.0 / (1.0 + math.exp(-z)) else 0
            amount = round(rng.lognormvariate(3.0, 1.2), 2)
            writer.writerow([i] + [round(x, 6) for x in features] + [amount, label])
    meta = {
        "synthetic": True,
        "seed": seed,
        "n": n,
        "generator": "planted logistic model, gaussian features",
        "note": "NOT real data — for pipeline development only.",
    }
    pathlib.Path(f"{destination}.meta.json").write_text(json.dumps(meta, indent=2))


def report(path, strict):
    check_schema(path)
    stats = dataset_stats(path)
    if strict:
        check_invariants(stats)
    digest, state = verify_or_record_checksum(path)
    print(f"file:        {path}")
    print(f"sha256:      {digest} ({state})")
    print(f"rows:        {stats['rows']}")
    print(f"frauds:      {stats['frauds']} (rate {stats['fraud_rate']:.5f})")
    print(f"amount mean: {stats['amount_mean']:.2f}  max: {stats['amount_max']:.2f}")
    return stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", help="use an already-downloaded CSV (copied to cache)")
    parser.add_argument("--synthetic", type=int, metavar="N",
                        help="generate an N-row labeled synthetic sample instead")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--stats", action="store_true",
                        help="just report on the cached dataset")
    args = parser.parse_args()

    if args.synthetic:
        destination = DATA_DIR / f"creditcard_synthetic_seed{args.seed}.csv"
        generate_synthetic(args.synthetic, args.seed, destination)
        print("SYNTHETIC DATA — planted ground truth, not real transactions.")
        report(destination, strict=False)
        return

    if args.stats:
        if not CACHE.exists():
            sys.exit(f"no cached dataset at {CACHE}; run without --stats first.")
        report(CACHE, strict=True)
        return

    if args.file:
        source = pathlib.Path(args.file)
        if not source.exists():
            sys.exit(f"{source} does not exist")
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, CACHE)
        report(CACHE, strict=True)
        return

    if CACHE.exists():
        print("using cached download")
        report(CACHE, strict=True)
        return

    print(f"resolving OpenML dataset {OPENML_DATASET_ID} (creditcard)…")
    url = resolve_openml_url()
    print(f"downloading {url}")
    download(url, CACHE)
    report(CACHE, strict=True)


if __name__ == "__main__":
    main()
