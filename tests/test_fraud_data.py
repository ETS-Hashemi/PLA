"""Machinery tests for the fraud-data loader.

The real download needs hosts this sandbox blocks; these tests verify
every moving part — schema check, stats, invariants, trust-on-first-use
checksums, synthetic generation, and the download function itself against
an allowed host (PyPI).
"""

import json
import pathlib
import sys
import urllib.error
import urllib.request

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import fetch_fraud_data as ffd  # noqa: E402


def test_synthetic_generation_is_deterministic_and_well_formed(tmp_path):
    a = tmp_path / "a.csv"
    b = tmp_path / "b.csv"
    ffd.generate_synthetic(500, seed=7, destination=a)
    ffd.generate_synthetic(500, seed=7, destination=b)

    assert ffd.sha256_of(a) == ffd.sha256_of(b)  # deterministic
    ffd.check_schema(a)
    stats = ffd.dataset_stats(a)
    assert stats["rows"] == 500
    assert 0 < stats["frauds"] < 100  # rare positives, but present
    meta = json.loads((tmp_path / "a.csv.meta.json").read_text())
    assert meta["synthetic"] is True and meta["seed"] == 7


def test_schema_check_rejects_wrong_columns(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("foo,bar\n1,2\n")
    with pytest.raises(ValueError):
        ffd.check_schema(bad)


def test_invariants_reject_wrong_counts(tmp_path):
    sample = tmp_path / "s.csv"
    ffd.generate_synthetic(100, seed=0, destination=sample)
    with pytest.raises(ValueError):
        ffd.check_invariants(ffd.dataset_stats(sample))


def test_checksum_trust_on_first_use_and_tamper_detection(tmp_path):
    sample = tmp_path / "s.csv"
    ffd.generate_synthetic(50, seed=1, destination=sample)

    digest1, state1 = ffd.verify_or_record_checksum(sample)
    assert state1 == "recorded"
    digest2, state2 = ffd.verify_or_record_checksum(sample)
    assert state2 == "verified" and digest1 == digest2

    sample.write_text(sample.read_text() + "tampered\n")
    with pytest.raises(ValueError):
        ffd.verify_or_record_checksum(sample)


def test_report_prints_stats(tmp_path, capsys):
    sample = tmp_path / "s.csv"
    ffd.generate_synthetic(200, seed=2, destination=sample)
    stats = ffd.report(sample, strict=False)
    out = capsys.readouterr().out
    assert "sha256:" in out and "rows:        200" in out
    assert stats["rows"] == 200


def test_download_machinery_against_allowed_host(tmp_path):
    """End-to-end download + checksum using PyPI (allowed by the proxy)."""
    try:
        with urllib.request.urlopen("https://pypi.org/pypi/six/json", timeout=20) as r:
            info = json.load(r)
    except (urllib.error.URLError, OSError):
        pytest.skip("network unavailable for PyPI")

    release = info["urls"][0]
    destination = tmp_path / "artifact.bin"
    ffd.download(release["url"], destination)
    assert ffd.sha256_of(destination) == release["digests"]["sha256"]
