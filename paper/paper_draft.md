# Superseded working draft

This Markdown draft was the manuscript's working skeleton during the
rebuild. It is **superseded by the LaTeX manuscript** and is kept only as
a pointer so stale numbers cannot circulate from here:

- **The manuscript** is `paper/main.tex` (+ `paper/sections/*.tex`) —
  elsarticle, compiled and page-gated in CI, packaged for Overleaf and
  submission by `scripts/build_paper_package.sh`.
- **The claim-provenance table** (each substantive claim → the test,
  script, or generated file that verifies it) is Appendix B of the
  manuscript (`paper/sections/appendix.tex`).
- **Results tables** are generated: `python scripts/make_paper_tables.py`
  prints the LaTeX bodies from `results/*.csv`; figures come from
  `python scripts/make_figures.py`.
- **The scenario-suite benchmark table** (34 scenarios; used by the
  workshop cut) regenerates with `python scripts/benchmark.py
  --paper-table`.
- **The referee rounds** that shaped the final text are in
  `paper/INTERNAL_REVIEW.md`.

Nothing else from the old draft is authoritative; if a number here ever
disagrees with `results/` or the manuscript, the generated artifact wins.
