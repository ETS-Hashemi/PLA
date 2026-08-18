# Paper (Overleaf project)

This folder is a self-contained Overleaf project whose main document is a
**scientific journal manuscript** in Elsevier's `elsarticle` class — the
class used by the target journals in `research/GAP_STATEMENT.md`
(*Knowledge-Based Systems*, *Expert Systems with Applications*,
*Information Sciences*).

| File | What it is |
|---|---|
| `main.tex` | **Journal manuscript** root (`elsarticle`) — frontmatter with abstract and keywords, inputs `sections/*.tex`, numbered natbib references from `references.bib` |
| `sections/` | One file per section (introduction … conclusion, appendices) |
| `references.bib` | BibTeX for every citation (26 entries, all cited) |
| `workshop.tex` | Secondary: self-contained 4–6 page workshop/tool-track cut (page-gated in CI) |
| `paper_draft.md` | Markdown working draft; its generated benchmark table is byte-verified against `scripts/benchmark.py` |

## Compile

```bash
cd paper
pdflatex main && bibtex main && pdflatex main && pdflatex main   # journal manuscript
pdflatex workshop && pdflatex workshop                            # workshop cut
```

Requires `elsarticle` (TeX Live: `texlive-publishers`; Overleaf has it
preinstalled). CI compiles both on every push (job **paper**) and uploads
the PDFs as the `papers` artifact.

## Class options (`main.tex`, first line)

- `[review,12pt]` — double-spaced with line numbers: what you submit.
- `[preprint,12pt]` — single-spaced preprint (arXiv-style).
- `[final,3p,times]` — two-column journal-layout proof, for length checks.

Change `\journal{...}` to match the actual submission target.

## Use with Overleaf

Zip this folder and upload it as a project (Menu → New Project → Upload);
set `main.tex` as the main document. All packages (`elsarticle`,
`amsmath`, `amssymb`, `amsthm`, `booktabs`, `hyperref`, `natbib`) are in
Overleaf's standard TeX Live.

## Editing rules

- Numbers in the results tables come from generated artifacts
  (`results/*.csv`, `scripts/benchmark.py --paper-table`). If the engine
  or experiments change, **regenerate and re-copy — never hand-edit** the
  values; Appendix B maps each claim to its verifying artifact.
- Real-data results replace the synthetic development tables before any
  submission (`scripts/run_experiments.py --data data/creditcard.csv`);
  the manuscript's evaluation section grows with that study — the current
  text is the verified skeleton, not submission-length prose.
- Elsevier journals ask for Highlights (3–5 bullets, ≤85 characters each)
  and a CRediT statement at submission time; add them when the target
  journal is fixed.
