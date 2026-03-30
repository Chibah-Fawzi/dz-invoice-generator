# devis-gen

Generate a quotation PDF (`devis.pdf`) from `template.json`.

## Usage

1. Edit `template.json` (company, client, line items, VAT/totals settings).
2. Install dependencies:
   - `python3 -m venv .venv`
   - `.venv/bin/pip install reportlab`
3. Run:
   - `.venv/bin/python index.py`

The output file is written as `devis.pdf` in the project directory.

