# Reference library

Local reference material for the manuscript's bibliography
(`paper/references.bib`). Populated by

```bash
export S2_API_KEY=...          # your Semantic Scholar key — never commit it
python scripts/check_references.py
```

which verifies every bibliography entry against the Semantic Scholar
Graph API (title, year, first author), writes
`verification_report.md`, and downloads open-access PDFs here as
`<bibkey>.pdf` where the API exposes one.

**Licensing rule for this folder:** `*.pdf` is gitignored. Downloaded
copies are for the authors' personal use; commit a PDF to this public
repository only if the report shows a redistribution-friendly license
(CC-BY, CC-BY-SA, CC0). For everything else, the report's DOI column
is the citable pointer.

The verification report should be re-run and reviewed once before each
submission; a `MISMATCH`/`CHECK`/`NOT_FOUND` row means the bib entry
deserves a manual look (books and older chapters are often `NOT_FOUND`
on Semantic Scholar — that alone is not an error).
