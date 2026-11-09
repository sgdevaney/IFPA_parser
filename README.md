# IFPA Validator

A lightweight Python application for checking IFPA reporting files against a YAML-driven schema catalog.

## Directory structure

- `data/structures/` contains the record definitions used by the validator
- `data/errors/` contains validation error metadata
- `input/sample_ifpa.txt` is a sample IFPA file
- `output/` stores generated validation reports
- `src/` contains the implementation

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run validation

```bash
python -m src.cli input/sample_ifpa.txt --output-dir output --format both
```

## Notes

The parser uses simple pipe-delimited records of the form:

```text
0001|report_id=IFPA-2026-Q1|report_year=2026|created_by=OPS
```

Schema definitions are stored in YAML files under `data/structures/` and can be extended for additional IFPA record types.
