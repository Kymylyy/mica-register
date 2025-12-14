# CSV Cleaning Tool

This document describes the CSV cleaning tool for ESMA CASP register CSV files.

## Overview

The cleaning tool automatically fixes detected validation issues in CSV files and produces a clean CSV file ready for import. It is separate from the validation and import processes, allowing you to review changes before importing.

## Workflow

```
Original CSV (with errors)
    ↓
validate_csv.py (detects issues)
    ↓
clean_csv.py (fixes all issues)
    ↓
Clean CSV (ready for import)
    ↓
import_csv.py (imports to database)
```

## Usage

### Basic Cleaning

```bash
python scripts/clean_csv.py --input CASP20251208.csv
```

This will:
- Load the CSV file
- Apply all automatic fixes
- Create a new file: `CASP20251208_clean.csv`
- Print a summary of changes

### Specify Output File

```bash
python scripts/clean_csv.py --input CASP20251208.csv --output clean.csv
```

### Dry Run

```bash
python scripts/clean_csv.py --input CASP20251208.csv --dry-run
```

Shows what would be changed without creating a new file.

### Save Cleaning Report

```bash
python scripts/clean_csv.py --input CASP20251208.csv --output clean.csv --report cleaning_report.json
```

## What Gets Fixed Automatically

### 1. Global Whitespace Cleanup
- **Issue**: NBSP (`\xa0`), trailing spaces, multiple spaces
- **Fix**: Replaces NBSP with regular space, strips trailing spaces, collapses multiple spaces
- **Type**: `WHITESPACE_FIXED`
- **Applied to**: All columns (except date columns and LEI)

### 2. Encoding Data Loss Detection and Fix
- **Issue**: Replacement characters (`\ufffd`, `\xef\xbf\xbd`) indicating data loss
- **Fix**: Attempts to fix using known patterns (e.g., `Stra\ufffde` → `Straße`)
- **Type**: `ENCODING_DATA_LOSS_FIXED` (if successful) or `ENCODING_DATA_LOSS_WARNING` (if cannot fix)
- **Columns**: `ae_address`, `ae_commercial_name`, `ae_lei_name`, `ac_competentAuthority`, `ac_comments`, `ae_website`

### 3. Encoding Issues
- **Issue**: Broken encoding (e.g., `Strae`, `Lw`, replacement characters)
- **Fix**: `Strae` → `Straße`, `Lw` → `Löw`
- **Type**: `ENCODING_FIXED`
- **Columns**: `ae_address`, `ae_commercial_name`, `ae_lei_name`, `ac_competentAuthority`, `ac_comments`

### 4. Dates
- **Issue**: Dates in various formats or with errors (e.g., `01/12/.2025`, `2025-12-01`)
- **Fix**: Uses `parse_date()` function to parse and normalize to `DD/MM/YYYY` format
- **Type**: `DATE_FIXED` (if successfully parsed) or `DATE_WARNING` (if cannot parse - left as-is)
- **Note**: Unparseable dates are left as-is with a warning - `import_csv.py` will attempt to fix during import

### 5. Multiline Fields
- **Website**: Fields containing newlines with URLs
  - **Fix**: Splits URLs, deduplicates, normalizes (adds `https://` if missing), joins with `|`
  - **Example**: `www.skrill.com\nwww.neteller.com` → `https://www.skrill.com|https://www.neteller.com`
  - **Type**: `MULTILINE_WEBSITE_FIXED`
- **Other fields** (address, comments): Replaces newlines with spaces
  - **Type**: `MULTILINE_FIXED`
- **Columns**: `ae_website`, `ae_address`, `ac_comments`

### 6. Country Code Normalization
- **Issue**: Country codes with spaces, wrong case, or `EL` (EU-speak for Greece)
- **Fix**: Strips spaces, converts to uppercase, maps `EL` → `GR` (but keeps both `EL` and `GR`), deduplicates, sorts, joins with `|`
- **Example**: `" EL|Fi|DE"` → `DE|EL|FI|GR`
- **Type**: `COUNTRY_CODE_NORMALIZED`
- **Column**: `ac_serviceCode_cou`

### 7. LEI Format Issues
- **Trailing dot**: `89450036UW3ID72T1M84.` → `89450036UW3ID72T1M84`
- **Type**: `LEI_TRAILING_DOT_REMOVED`
- **Excel scientific notation**: Attempts to convert (e.g., `9.60E+19` → tries to recover 20-char LEI)
  - **Type**: `LEI_EXCEL_NOTATION_FIXED` (if successful) or `LEI_WARNING` (if cannot recover)
- **Non-alphanumeric characters**: Removes all non-alphanumeric characters
  - **Type**: `LEI_CLEANED`
- **Invalid format**: If all attempts fail, left as-is with warning
  - **Type**: `LEI_WARNING` (non-blocking - import may skip the row)

### 8. Duplicate LEI
- **Issue**: Multiple rows with the same LEI
- **Fix**: Merged into single row with combined services, countries, websites
- **Type**: `DUPLICATE_LEI_MERGED`

### 9. Address/Website Parsing
- **Issue**: Address incorrectly split into website column
- **Fix**: Merged back into address field
- **Type**: `ADDRESS_PARSING_FIXED`, `WEBSITE_PARSING_FIXED`

### 10. Service Codes
- **Issue**: Service codes in various formats
- **Fix**: Normalized to standard format with descriptions
- **Type**: `SERVICE_CODE_NORMALIZED`

### 11. Commercial Names
- **Issue**: Known errors in commercial names (e.g., "e Toro")
- **Fix**: `e Toro` → `eToro`
- **Type**: `COMMERCIAL_NAME_NORMALIZED`

## Warnings (Non-Blocking)

The cleaning tool now minimizes manual intervention. Issues that cannot be automatically fixed are reported as **warnings** (not errors) and do not block the cleaning process:

1. **Unparseable dates** (`DATE_WARNING`)
   - Date cannot be parsed by `parse_date()` function
   - Left as-is in cleaned CSV
   - `import_csv.py` will attempt to fix during import

2. **Encoding data loss** (`ENCODING_DATA_LOSS_WARNING`)
   - Replacement character detected but cannot be auto-fixed
   - Left as-is in cleaned CSV
   - May require manual review if data is critical

3. **LEI issues** (`LEI_WARNING`)
   - LEI format invalid after all fix attempts
   - Left as-is in cleaned CSV
   - `import_csv.py` may skip the row during import

**Result**: The cleaning tool always produces a cleaned CSV file, even if some warnings remain. This enables fully automated cron jobs.

## Cleaning Report Format

The cleaning report (JSON) contains:

```json
{
  "version": 1,
  "generated_at": "2025-12-08T10:30:00Z",
  "input_file": "CASP20251208.csv",
  "output_file": "CASP20251208_clean.csv",
  "encoding": {
    "detected": "utf-8-sig",
    "confidence": 0.95,
    "notes": "..."
  },
  "stats": {
    "rows_before": 112,
    "rows_after": 110,
    "columns": 15
  },
  "changes": [
    {
      "type": "DATE_FIXED",
      "row": 70,
      "column": "ac_authorisationNotificationDate",
      "old_value": "01/12/.2025",
      "new_value": "01/12/2025"
    },
    {
      "type": "MULTILINE_FIXED",
      "row": 70,
      "column": "ae_website",
      "old_value": "www.skrill.com\nwww.neteller.com",
      "new_value": "www.skrill.com www.neteller.com"
    }
  ],
  "summary": {
    "total_changes": 15,
    "changes_by_type": {
      "DATE_FIXED": 1,
      "MULTILINE_FIXED": 1,
      "ENCODING_FIXED": 3,
      "DUPLICATE_LEI_MERGED": 1,
      ...
    }
  }
}
```

## Complete Workflow Example

### Step 1: Validate CSV

```bash
python scripts/validate_csv.py CASP20251208.csv
```

Check for issues.

### Step 2: Clean CSV

```bash
python scripts/clean_csv.py --input CASP20251208.csv --output CASP20251208_clean.csv --report cleaning_report.json
```

This creates:
- `CASP20251208_clean.csv` - cleaned file ready for import
- `cleaning_report.json` - detailed report of all changes

### Step 3: Review Changes

Check the cleaning report to see what was fixed. Pay attention to warnings (`DATE_WARNING`, `ENCODING_DATA_LOSS_WARNING`, `LEI_WARNING`) if any, but these are non-blocking.

### Step 4: Optional Manual Fixes

If there are warnings in the report that you want to fix manually:
1. Open the cleaned CSV
2. Find the rows marked in the report
3. Fix the values manually
4. Save the file

**Note**: Warnings are non-blocking - the cleaned CSV is ready for import even with warnings. `import_csv.py` will handle edge cases during import.

### Step 5: Validate Cleaned CSV

```bash
python scripts/validate_csv.py CASP20251208_clean.csv
```

Should show fewer or no issues.

### Step 6: Import to Database

```bash
# Use the cleaned CSV for import
python backend/import_data.py
# Or use the API endpoint with cleaned CSV
```

## Integration with CI/Pre-commit

### Pre-commit Hook Example

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
      
      - id: clean-csv
        name: Clean CSV files
        entry: python scripts/clean_csv.py
        language: system
        files: \.csv$
        pass_filenames: true
        args: ['--input']
        # Note: This would need custom logic to handle filenames
```

### CI Pipeline Example

```yaml
# GitHub Actions example
- name: Validate CSV
  run: |
    python scripts/validate_csv.py CASP20251208.csv --report validation.json
    
- name: Clean CSV
  run: |
    python scripts/clean_csv.py --input CASP20251208.csv --output clean.csv --report cleaning.json
    
- name: Validate Cleaned CSV
  run: |
    python scripts/validate_csv.py clean.csv --strict
    if [ $? -ne 0 ]; then
      echo "Cleaned CSV still has issues"
      exit 1
    fi
```

## Module Usage

The cleaning module can also be imported and used programmatically:

```python
from pathlib import Path
from app.csv_clean import CSVCleaner

cleaner = CSVCleaner(Path("CASP20251208.csv"))
cleaner.load_csv()
cleaner.fix_all_issues()

# Save cleaned CSV
cleaner.save_clean_csv(Path("clean.csv"))

# Generate report
report = cleaner.generate_report()
print(f"Made {report['summary']['total_changes']} changes")
```

## Exit Codes

- **0**: Success - cleaning completed
- **1**: Error during cleaning process
- **2**: Input file not found

## Notes

- The original CSV file is **never modified** - always creates a new file
- All changes are tracked and reported
- Warnings are clearly marked in the report but are non-blocking
- The cleaned CSV is ready for import without additional processing
- Designed for automation - cron jobs can run cleaning without manual intervention
- Fixes are applied in a specific order to ensure optimal results:
  1. Global whitespace cleanup (first)
  2. Encoding data loss detection and fix
  3. Encoding issues (known patterns)
  4. Dates
  5. Multiline fields
  6. Country codes
  7. LEI format
  8. Duplicate LEI merging
  9. Address/website parsing
  10. Service codes
  11. Commercial names
