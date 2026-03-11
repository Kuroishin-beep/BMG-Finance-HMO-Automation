# Billing Processor

A stateless, in-memory Streamlit app that processes, compares, and segregates
Excel financial billing files. Nothing is written to disk.

## Reference File Workflow

The app reads `data/reference.xlsx` automatically on startup — no upload needed.

After each billing run, download the **Updated Reference** from Step 5 and
replace `data/reference.xlsx` with it. That keeps your master list current
(new hires in, departed employees out) for the next cycle.

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Input File Expectations

| File | Required Columns |
|------|-----------------|
| Master Reference | ID Number, Name, Entity |
| Raw Billing | Any subject/description column + ID + Name columns |

Column names are detected case-insensitively. See `config/constants.py` for
the full list of accepted aliases.

## Processing Rules

1. **Sanity Check** — keeps only rows whose subject contains `MONTHLY` or `Additional billing`
2. **Sync** — auto-adds new employees to reference; auto-removes missing ones
3. **Advances sheet** — any row whose Entity contains "advance" is extracted into a
   single "Advances" sheet; the Entity cell is replaced with the employee's name
4. **Company sheets** — all remaining rows are grouped by Entity into separate sheets