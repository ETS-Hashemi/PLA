#!/bin/bash
# Build every paper PDF and assemble the Overleaf and submission packages.
#
# Outputs (dist/, gitignored):
#   overleaf_package.zip   — LaTeX sources with main.tex at the zip root;
#                            upload to Overleaf as-is (main document: main.tex).
#   submission_package.zip — Elsevier submission set: manuscript.pdf,
#                            highlights.pdf, cover_letter.pdf, and source.zip
#                            (the same Overleaf tree).
#
# The Overleaf zip is verified by unpacking it into a clean directory and
# compiling there — exactly what Overleaf will do.
set -euo pipefail
cd "$(dirname "$0")/.."

latex() { pdflatex -interaction=nonstopmode -halt-on-error "$@" > /dev/null; }
bib() { bibtex "$1" > /dev/null || [ $? -lt 2 ]; }  # bibtex exits 1 on warnings

(cd paper
 latex main.tex && bib main && latex main.tex && latex main.tex
 latex workshop.tex && latex workshop.tex
 latex highlights.tex
 latex cover_letter.tex
 latex supplementary.tex && latex supplementary.tex)

mkdir -p dist
rm -f dist/overleaf_package.zip dist/submission_package.zip

(cd paper && zip -q -r ../dist/overleaf_package.zip \
    main.tex workshop.tex highlights.tex cover_letter.tex \
    supplementary.tex \
    sections figures references.bib README.md)

staging=$(mktemp -d)
cp paper/main.pdf "$staging/manuscript.pdf"
cp paper/highlights.pdf "$staging/highlights.pdf"
cp paper/cover_letter.pdf "$staging/cover_letter.pdf"
cp paper/supplementary.pdf "$staging/supplementary.pdf"
cp dist/overleaf_package.zip "$staging/source.zip"
(cd "$staging" && zip -q -r submission_package.zip \
    manuscript.pdf highlights.pdf cover_letter.pdf supplementary.pdf \
    source.zip)
mv "$staging/submission_package.zip" dist/
rm -rf "$staging"

verify=$(mktemp -d)
unzip -q dist/overleaf_package.zip -d "$verify"
(cd "$verify" && latex main.tex && bib main && latex main.tex && latex main.tex)
pages=$(pdfinfo "$verify/main.pdf" | awk '/^Pages:/ {print $2}')
rm -rf "$verify"

echo "overleaf_package.zip compiles standalone: main.pdf, ${pages} pages"
echo "built: dist/overleaf_package.zip, dist/submission_package.zip"
