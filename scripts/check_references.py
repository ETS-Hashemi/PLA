"""Verify references.bib against Semantic Scholar, and fetch open-access
PDFs into paper/references/.

Every bibliography entry is looked up by title on the Semantic Scholar
Graph API; the best match is compared on title similarity, year, and
first-author surname, and the result is written to
paper/references/verification_report.md. Where Semantic Scholar exposes
an open-access PDF, it is downloaded to paper/references/<bibkey>.pdf
with its license recorded.

Run this OUTSIDE restricted networks (api.semanticscholar.org must be
reachable). The API key is read from the S2_API_KEY environment
variable and is never written to any file:

    export S2_API_KEY=...        # your key; do not commit it anywhere
    python scripts/check_references.py            # verify + fetch PDFs
    python scripts/check_references.py --no-pdf   # verify only

Redistribution note: paper/references/*.pdf is gitignored. Before
committing any downloaded PDF to the public repository, check its
"license" line in the report; only clearly redistributable licenses
(CC-BY, CC-BY-SA, CC0) belong in a public repo. Everything else stays
local; the report records the open-access URL either way.

Rate limit: one request per second (the key's limit), enforced here.
"""

import argparse
import difflib
import json
import os
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
BIB = ROOT / "paper" / "references.bib"
OUT_DIR = ROOT / "paper" / "references"
API = "https://api.semanticscholar.org/graph/v1/paper/search"
FIELDS = "title,year,venue,authors,externalIds,openAccessPdf"
RATE_SECONDS = 1.1


def parse_bib(path):
    """Minimal parser for this repository's references.bib (one field per
    line, braces around values)."""
    entries = []
    current = None
    for line in path.read_text().splitlines():
        start = re.match(r"@\w+\{([^,]+),", line.strip())
        if start:
            current = {"key": start.group(1)}
            entries.append(current)
            continue
        if current is None:
            continue
        field = re.match(r"\s*(\w+)\s*=\s*\{(.*)\},?\s*$", line)
        if field:
            current[field.group(1).lower()] = field.group(2)
    return [e for e in entries if "title" in e]


def clean(latex):
    text = re.sub(r"\\['`^\"~=.uvHtcdb]\s*\{?(\w)\}?", r"\1", latex)
    text = re.sub(r"\\[a-zA-Z]+", " ", text)
    return re.sub(r"[{}$\\]", "", text).strip()


def first_surname(author_field):
    first = clean(author_field).split(" and ")[0]
    return (first.split(",")[0] if "," in first
            else first.split()[-1]).lower()


def s2_search(title, key):
    query = urllib.parse.quote(clean(title))
    url = f"{API}?query={query}&fields={FIELDS}&limit=3"
    request = urllib.request.Request(url, headers={"x-api-key": key})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read()).get("data", [])


def similarity(a, b):
    normalize = lambda s: re.sub(r"[^a-z0-9 ]", "", s.lower())
    return difflib.SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def verify(entry, candidates):
    """Return (status, note, best_candidate)."""
    title = clean(entry["title"])
    if not candidates:
        return "NOT_FOUND", "no search results", None
    best = max(candidates, key=lambda c: similarity(title, c.get("title", "")))
    score = similarity(title, best.get("title", ""))
    if score < 0.75:
        return ("CHECK", f"best match only {score:.2f} similar: "
                f"\"{best.get('title', '')}\"", best)
    notes = []
    year = entry.get("year")
    if year and best.get("year") and abs(int(year) - best["year"]) > 1:
        notes.append(f"year: bib {year} vs S2 {best['year']}")
    if entry.get("author"):
        surname = first_surname(entry["author"])
        s2_authors = [a["name"].split()[-1].lower()
                      for a in best.get("authors", [])]
        if s2_authors and surname not in s2_authors:
            notes.append(f"first author '{surname}' not in S2 author list")
    if notes:
        return "MISMATCH", "; ".join(notes), best
    return "OK", f"title match {score:.2f}", best


def fetch_pdf(best, bibkey, key):
    info = best.get("openAccessPdf") or {}
    url = info.get("url")
    if not url:
        return None, None
    target = OUT_DIR / f"{bibkey}.pdf"
    request = urllib.request.Request(
        url, headers={"User-Agent": "reference-fetcher (author use)"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = response.read()
        if not data.startswith(b"%PDF"):
            return None, info.get("license")
        target.write_bytes(data)
        return target.name, info.get("license")
    except Exception as error:  # noqa: BLE001 — record and continue
        return None, f"download failed: {error}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-pdf", action="store_true",
                        help="verify metadata only, download nothing")
    args = parser.parse_args()

    key = os.environ.get("S2_API_KEY")
    if not key:
        sys.exit("set S2_API_KEY in the environment (never commit it)")

    entries = parse_bib(BIB)
    OUT_DIR.mkdir(exist_ok=True)
    lines = [
        "# Reference verification report",
        "",
        "Generated by `python scripts/check_references.py` against the",
        "Semantic Scholar Graph API — regenerate, never hand-edit. PDF",
        "column: downloaded open-access copies land in this folder and",
        "are gitignored; commit one only if its license permits",
        "redistribution (CC-BY, CC-BY-SA, CC0).",
        "",
        "| Bib key | Status | Note | S2 year | DOI | PDF (license) |",
        "|---|---|---|---|---|---|",
    ]
    counts = {}
    for entry in entries:
        time.sleep(RATE_SECONDS)
        try:
            candidates = s2_search(entry["title"], key)
        except Exception as error:  # noqa: BLE001 — keep the sweep going
            status, note, best = "ERROR", str(error), None
        else:
            status, note, best = verify(entry, candidates)
        counts[status] = counts.get(status, 0) + 1

        doi = ""
        pdf_cell = ""
        year = ""
        if best:
            year = best.get("year") or ""
            doi = (best.get("externalIds") or {}).get("DOI", "") or ""
            if not args.no_pdf and status in ("OK", "MISMATCH"):
                time.sleep(RATE_SECONDS)
                name, license_ = fetch_pdf(best, entry["key"], key)
                if name:
                    pdf_cell = f"{name} ({license_ or 'license unknown'})"
                elif license_:
                    pdf_cell = f"— ({license_})"
        lines.append(f"| {entry['key']} | {status} | {note} | {year} "
                     f"| {doi} | {pdf_cell} |")
        print(f"{entry['key']:>18}  {status}  {note}")

    summary = ", ".join(f"{k}: {v}" for k, v in sorted(counts.items()))
    lines.insert(2, f"Entries: {len(entries)} — {summary}.")
    (OUT_DIR / "verification_report.md").write_text("\n".join(lines) + "\n")
    print(f"\nreport: {OUT_DIR / 'verification_report.md'}  ({summary})")


if __name__ == "__main__":
    main()
