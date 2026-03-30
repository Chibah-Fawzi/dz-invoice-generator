# Algerian invoice generator

Generate a quotation PDF (`devis.pdf`) from `template.json`.

## Algerian invoice references

The generated document includes typical invoicing fields (seller/buyer details, invoice number/date, itemized services, VAT/totals, etc.) inspired by Algerian invoicing requirements and common best practices. Reference: [Ministère du Commerce (Algérie) - Questions fréquentes: Facture](https://www.commerce.gov.dz/fr/questions-frequentes/themes/facture).

This project is a practical generator/template; please verify wording and mandatory mentions for your specific activity with a qualified accountant/legal advisor.

## Usage

1. Edit `template.json` (company, client, line items, VAT/totals settings).
2. Install dependencies:
   - `python3 -m venv .venv`
   - `.venv/bin/pip install reportlab`
3. Run:
   - `.venv/bin/python index.py`

The output file is written as `devis.pdf` in the project directory.
