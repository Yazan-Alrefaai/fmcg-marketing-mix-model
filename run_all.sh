#!/usr/bin/env bash
# Rebuild everything from the raw Excel file: analysis notebook, outputs, slides, then run the tests.
set -euo pipefail
cd "$(dirname "$0")"

.venv/bin/python src/build_notebook.py              # steps 01-07 -> outputs/, MMM_analysis.ipynb/.html
(cd src && ../.venv/bin/python 08_deck_data.py)     # numbers for the slides -> deck/deck_data.json
(cd deck && node build_deck.js)                     # -> MMM_presentation.pptx
.venv/bin/python -m pytest                          # data, model, results and deliverable checks
