# IFPA Validator Project - Handover Document

## Project Goal

Build a metadata-driven Python validator for Danish SKAT IFPA reporting files.

The validator should:

- Parse IFPA fixed-width files
- Validate record layouts
- Validate field lengths and datatypes
- Validate mandatory fields
- Validate business rules
- Map errors to official SKAT error/advisory codes
- Generate Excel and CSV validation reports
- Remain year-independent by using metadata files instead of hard-coded logic

Target environment:

- Windows 11
- VS Code
- Python 3.11+
- Git-compatible project structure

---

# Documentation Collected

## IFPA Structure Documents

Available:

- Individ 2237
  - Køb / salg / likvidation
  - Version 01
  - Applies from tax year 2025 and forward

- Individ 4821
  - Error return record

## Error Documentation

Available:

- Bilag 5
  - Fejl- og advisnumre med rettelsesvejledning

Contains:

- Error codes
- Advisory codes
- Descriptions
- Correction guidance

Examples identified:

- 024
- 057
- 072
- 133
- 328
- 599
- 801-806

---

# Sample Data

Sample file:

20260109_163204_IFPA2235-3RD.txt

Characteristics:

- Fixed-width file
- Header record 0001
- Data records 2235
- Trailer record 9998

Contents:

- 1 header
- 35 data records
- 1 trailer

Total:

37 records

Trailer count appears consistent with file content.

---

# Design Decisions

## Principle

Use metadata rather than hard-coded validation logic.

Avoid:

```python
if len(isin) != 12:
    ...
```

Prefer:

```yaml
- name: ISIN
  length: 12
  pattern: "^[A-Z0-9]{12}$"
```

This permits future SKAT updates without rewriting code.

---

# Proposed Project Structure

```text
ifpa-validator/
│
├── data/
│   ├── structures/
│   │   ├── 0001.yaml
│   │   ├── 2235.yaml
│   │   ├── 2237.yaml
│   │   ├── 2238.yaml
│   │   └── 4821.yaml
│   │
│   └── errors/
│       └── bilag5.yaml
│
├── input/
│
├── output/
│
├── src/
│   ├── cli.py
│   ├── metadata.py
│   ├── parser.py
│   ├── validator.py
│   └── report.py
│
├── tests/
│
├── requirements.txt
│
└── PROJECT_HANDOVER.md
```

---

# Current Status

Implementation completed:

## metadata.py

Loads YAML structure definitions.

## parser.py

Reads fixed-width records.

Determines record type from:

```python
line[:4]
```

## validator.py

Currently validates:

- Record lengths
- Required fields
- Numeric fields
- Regular-expression patterns

## report.py

Excel export placeholder implemented.

## cli.py

Working.

Successful execution:

```text
Validation complete. 0 errors found.
```

---

# Installed Packages

requirements.txt

```text
pandas>=2.2.0
openpyxl>=3.1.2
pyyaml>=6.0.2
```

---

# Recommended Error Model

Replace dictionary-based error handling with dataclasses.

```python
from dataclasses import dataclass

@dataclass
class ValidationError:
    line_no: int
    record_type: str
    field_name: str
    error_code: str
    description: str
    value: str
```

---

# Metadata Format

Example:

2235.yaml

```yaml
record_type: 2235

record_length: 1346

fields:

  - name: INDVNR
    start: 1
    length: 4
    datatype: numeric
    required: true

  - name: OPSENR
    start: 5
    length: 8
    datatype: numeric
    required: true
```

---

# Error Catalogue Format

bilag5.yaml

```yaml
errors:

  "024":
    severity: error
    message: "Fejl i rettekode"

  "057":
    severity: error
    message: "Fejl i CPR/CVR/SENR"

  "072":
    severity: error
    message: "Negativt beløb mangler rettekode"

  "599":
    severity: ok
    message: "Ingen fejl"

  "801":
    severity: advisory
    message: "Advis"
```

---

# Planned Validation Levels

## Level 1

Structural validation

Checks:

- Known record type
- Record length
- Trailer exists
- Header exists

## Level 2

Field-level validation

Checks:

- Required fields
- Datatypes
- Regex
- Allowed values

Metadata-driven.

## Level 3

Business rules

Derived from Bilag 5.

Examples:

- CPR validation
- CVR validation
- ISIN validation
- Negative amount rules
- Correction code dependencies

## Level 4

Cross-record validation

Examples:

- Duplicate records
- Balancing checks
- Trailer count validation
- Reconciliation checks

---

# Immediate Next Tasks

## Task 1 — Completed

Implemented trailer validation. The `9998` schema defines the count field,
sender number, and record type. File validation compares the trailer count
with records including the header and trailer, excluding record types listed
in the trailer schema's `record_count_excluded_types`.

The current sample has no filler records. The official 9998 source says filler
individuals must not be counted. No filler record type is identified in the
available source pages, so the exclusion list is currently empty.

The final period in the sample is an intentional marker that protects trailing
spaces from truncation. It is allowed in the final filler field; other 2235
filler regions are required to be blank.

## Task 2 — Completed

Created the 2235 YAML definition from the official 2025 SKAT Bilag 2 and
Bilag 3 layouts. It contains all 83 fields and filler regions; field widths
cover all 1,346 positions.

## Task 3 — Completed

Created the Bilag 5 catalogue from the official 2025 SKAT page: 109 error
codes, code 599, and advisories 801–806, including correction guidance where
provided.

## Task 4 — Completed

The CLI accepts `--report` to write an Excel workbook with the requested
columns:

| Line | Record | Field | Code | Description | Value |
|--------|--------|--------|--------|--------|--------|

---

# Future Enhancements

## Excel Formatting

- Auto filter
- Frozen header row
- Conditional colouring

## Command Line

```bash
python src/cli.py input/sample.txt
```

or

```bash
python src/cli.py input/sample.txt --report output/report.xlsx
```

## Unit Testing

Pytest-based tests:

```text
tests/
├── test_parser.py
├── test_validator.py
├── test_trailer.py
└── test_metadata.py
```

---

# Important Observation

Current sample file contains:

```text
0001
2235
9998
```

No 2237 records were present.

A future sample containing 2237 and 2238 records should be added to the test suite so those layouts can be verified against real data.

---

# Recommended Strategy

Do NOT manually encode business logic into Python.

Always prefer:

Documentation
→ Metadata (YAML)
→ Generic Validation Engine

This will minimise maintenance effort when SKAT publishes future IFPA revisions.