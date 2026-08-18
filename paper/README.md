# Paper (Overleaf project)

This folder is a self-contained Overleaf-style LaTeX project.

| File | What it is |
|---|---|
| `main.tex` | **Full paper** root — inputs `sections/*.tex`, bibliography from `references.bib` |
| `sections/` | One file per section (introduction … conclusion, appendix) |
| `references.bib` | BibTeX for every citation |
| `workshop.tex` | Self-contained **4–6 page workshop/tool-track cut** (compiled and page-gated in CI) |
| `paper_draft.md` | Markdown working draft; its generated benchmark table is byte-verified against `scripts/benchmark.py` |

## Compile

```bash
cd paper
pdflatex main && bibtex main && pdflatex main && pdflatex main   # full paper
pdflatex workshop && pdflatex workshop                            # workshop cut
```

CI does both on every push (job **paper**) and uploads the PDFs as the
`papers` artifact; the workshop cut must stay within 4–6 pages.

## Use with Overleaf

Zip this folder and upload it as a project (Menu → New Project → Upload);
set `main.tex` as the main document. No packages beyond a standard TeX
Live are required (`geometry`, `amsmath`, `amssymb`, `amsthm`,
`booktabs`, `hyperref`).

## Editing rules

- Numbers in the results tables come from generated artifacts
  (`results/*.csv`, `scripts/benchmark.py --paper-table`). If the engine
  or experiments change, **regenerate and re-copy — never hand-edit** the
  values; Appendix B maps each claim to its verifying artifact.
- Real-data results replace the synthetic development tables before any
  submission (`scripts/run_experiments.py --data data/creditcard.csv`).
