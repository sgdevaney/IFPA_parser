# IFPA_parser

IFPA parser and validator: a lightweight Python application for checking IFPA
reporting files against a YAML-driven schema catalog.

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
python -m src.cli input/20260109_163204_IFPA2235-3RD.txt
python -m src.cli input/20260109_163204_IFPA2235-3RD.txt --report output/report.xlsx
```

## Notes

The parser reads fixed-width IFPA records. The validator checks each record
against its YAML structure, requires a `0001` header and `9998` trailer in
the correct positions, checks file-wide reporting-year and reporting-type
consistency, and verifies the record count in the trailer.
Use `--report` to write validation errors to an Excel workbook with Line,
Record, Field, Code, Description, and Value columns.

Schema definitions are stored in YAML files under `data/structures/` and can be extended for additional IFPA record types.
