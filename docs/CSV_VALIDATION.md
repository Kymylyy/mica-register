# CSV Validation Tool

This document describes the CSV validation tooling for ESMA CASP register CSV files.

## Overview

The validation tool checks CSV files before import, detecting issues with:
- CSV structure and parsing integrity
- Schema/header validation
- LEI format and duplicates
- Date formats
- Service codes
- Country codes
- Multiline fields
- Encoding issues

The tool produces structured JSON reports and exit codes suitable for CI/pre-commit hooks.

## Usage

### Basic Validation

```bash
python scripts/validate_csv.py casp-register.csv
```

This will:
- Validate the CSV file
- Print a human-readable summary to stdout
- Return an appropriate exit code

### Save JSON Report

```bash
python scripts/validate_csv.py casp-register.csv --report report.json
```

The JSON report will be saved to `report.json` with detailed information about all issues found.

### Strict Mode

```bash
python scripts/validate_csv.py casp-register.csv --strict
```

In strict mode, warnings are treated as errors (exit code 2).

### Limit Examples

```bash
python scripts/validate_csv.py casp-register.csv --max-examples 3
```

Limit the number of examples shown per issue in the report (default: 5).

## Exit Codes

The tool uses the following exit codes:

- **0**: No errors and no warnings - CSV is valid
- **1**: No errors but at least one warning - CSV has issues but is importable
- **2**: At least one error - CSV has blocking issues that should be fixed

With `--strict` flag, warnings are treated as errors, so exit code 2 is returned if any warnings are found.

## JSON Report Structure

The JSON report has the following structure:

```json
{
  "version": 1,
  "generated_at": "2025-12-08T10:30:00Z",
  "input_file": "casp-register.csv",
  "encoding": {
    "detected": "utf-8-sig",
    "confidence": 0.95,
    "notes": "Detected using charset-normalizer"
  },
  "stats": {
    "rows_total": 109,
    "rows_parsed": 109,
    "columns": 15,
    "header": ["ae_competentAuthority", "ae_homeMemberState", ...]
  },
  "issues": [
    {
      "severity": "ERROR",
      "code": "LEI_INVALID_FORMAT",
      "message": "Found 2 LEI(s) with invalid format (must be 20 alphanumeric characters)",
      "column": "ae_lei",
      "rows": [5, 12],
      "examples": ["INVALID123", "SHORT"]
    },
    {
      "severity": "WARNING",
      "code": "DATE_NEEDS_NORMALIZATION",
      "message": "Column 'ac_authorisationNotificationDate': 1 date(s) need normalization (e.g., dot before year)",
      "column": "ac_authorisationNotificationDate",
      "rows": [7],
      "examples": ["01/12/.2025 → 01/12/2025"]
    }
  ]
}
```

### Report Fields

- **version**: Report format version (currently 1)
- **generated_at**: ISO8601 timestamp of report generation
- **input_file**: Path to the validated CSV file
- **encoding**: Encoding detection information
  - **detected**: Detected encoding (e.g., "utf-8-sig", "latin-1")
  - **confidence**: Confidence score (0.0-1.0)
  - **notes**: Additional notes about encoding detection
- **stats**: CSV statistics
  - **rows_total**: Total number of rows (including header)
  - **rows_parsed**: Number of rows with correct column count
  - **columns**: Number of columns
  - **header**: List of column names
- **issues**: List of validation issues
  - **severity**: "ERROR" or "WARNING"
  - **code**: Issue code (see Issue Codes below)
  - **message**: Human-readable message
  - **column**: Column name (if applicable)
  - **rows**: List of 1-based row numbers where issue occurs
  - **examples**: Example values (capped by --max-examples)

## Issue Codes

### Errors (Severity: ERROR)

- **SCHEMA_MISSING_COLUMN**: Required column is missing
- **SCHEMA_DUPLICATE_COLUMN**: Duplicate column names in header
- **ROW_COLUMN_COUNT_MISMATCH**: Row has incorrect number of columns
- **LEI_INVALID_FORMAT**: LEI does not match required format (20 alphanumeric characters)
- **DATE_UNPARSABLE**: Date cannot be parsed
- **SERVICE_CODE_INVALID**: No valid service codes (a-j) found in service code field
- **COUNTRY_CODE_INVALID**: Invalid country code found
- **MULTILINE_FIELD**: Multiline field found in non-website column

### Warnings (Severity: WARNING)

- **SCHEMA_HEADER_WHITESPACE**: Column header has leading/trailing whitespace
- **LEI_DUPLICATE**: Same LEI appears in multiple rows
- **DATE_NEEDS_NORMALIZATION**: Date has repairable format issue (e.g., dot before year)
- **SERVICE_CODE_SUSPICIOUS_FORMAT**: Service code contains suspicious patterns
- **MULTILINE_WEBSITE**: Website field contains newlines
- **ENCODING_SUSPECT**: Potential encoding issues detected
- **COUNTRY_CODE_VALIDATION_PARTIAL**: Country code validation is partial (pycountry not available)

## Required Columns

The following columns are required in the CSV:

- `ae_lei`: Legal Entity Identifier
- `ac_serviceCode`: Service codes (pipe-separated)
- `ac_serviceCode_cou`: Country codes (pipe-separated)
- `ac_authorisationNotificationDate`: Authorisation notification date
- `ac_lastupdate`: Last update date

## Date Formats

Accepted date formats:

- `DD/MM/YYYY` (e.g., "01/12/2025")
- `YYYY-MM-DD` (e.g., "2025-12-01")

The tool detects repairable ESMA glitches such as `01/12/.2025` (dot before year) and reports them as warnings.

## Service Codes

Service codes must be letters a-j. The tool accepts various formats:

- Single code: `a`
- Code with description: `a. providing custody and administration...`
- Multiple codes: `a | b | c` or `a; b; c`

## Country Codes

Country codes must be valid 2-letter ISO codes. The tool validates against:

- Full country database (if `pycountry` is installed)
- Static EU+EEA+UK+CH set (if `pycountry` is not available)

If `pycountry` is not available, a warning is issued indicating partial validation.

## Integration with CI/Pre-commit

### Pre-commit Hook Example

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: validate-csv
        name: Validate CSV files
        entry: python scripts/validate_csv.py
        language: system
        files: \.csv$
        pass_filenames: true
        args: ['--strict']
```

### CI Pipeline Example

```yaml
# GitHub Actions example
- name: Validate CSV
  run: |
    python scripts/validate_csv.py casp-register.csv --report validation-report.json
    if [ $? -ne 0 ]; then
      echo "CSV validation failed"
      exit 1
    fi
```

## Dependencies

The tool has optional dependencies that provide enhanced functionality:

- **pycountry**: Full country code validation (falls back to static set if not available)
- **charset-normalizer**: Better encoding detection (falls back to utf-8-sig if not available)

Both dependencies degrade gracefully - the tool will work without them but with reduced functionality.

## Module Usage

The validation module can also be imported and used programmatically:

```python
from pathlib import Path
from app.csv_validate import validate_csv

report = validate_csv(Path("casp-register.csv"), max_examples=5)
print(f"Found {len(report['issues'])} issues")
```

## Related Tools

- **CSV Cleaning**: After validation, use `scripts/clean_csv.py` to automatically fix issues. See [CSV_CLEANING.md](CSV_CLEANING.md) for details.
- **CSV Import**: Once validated and cleaned, use `backend/import_data.py` or the API endpoint to import to database.

## Examples

### Valid CSV

```bash
$ python scripts/validate_csv.py valid.csv
============================================================
CSV Validation Report
============================================================
Input file: valid.csv
Encoding: utf-8-sig (confidence: 0.95)

Statistics:
  Total rows: 10
  Parsed rows: 10
  Columns: 15

Issues found:
  Errors: 0
  Warnings: 0

✅ No issues found - CSV is valid!
============================================================
```

Exit code: 0

### CSV with Warnings

```bash
$ python scripts/validate_csv.py warnings.csv
...
Issues found:
  Errors: 0
  Warnings: 2
...
```

Exit code: 1

### CSV with Errors

```bash
$ python scripts/validate_csv.py errors.csv
...
Issues found:
  Errors: 3
  Warnings: 1
...
```

Exit code: 2
