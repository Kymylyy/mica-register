"""
CSV Validation Module for ESMA CASP Register

Validates CSV files before import, detecting issues with structure, schema,
data formats, and encoding. Produces structured JSON reports.
"""

import csv
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import json

# Optional dependencies with graceful degradation
try:
    import charset_normalizer
    HAS_CHARSET_NORMALIZER = True
except ImportError:
    HAS_CHARSET_NORMALIZER = False

try:
    import pycountry
    HAS_PYCOUNTRY = True
except ImportError:
    HAS_PYCOUNTRY = False

# Required columns based on importer usage
REQUIRED_COLUMNS = [
    "ae_lei",
    "ac_serviceCode",
    "ac_serviceCode_cou",
    "ac_authorisationNotificationDate",
    "ac_lastupdate",
]

# Date columns used by importer
DATE_COLUMNS = [
    "ac_authorisationNotificationDate",
    "ac_authorisationEndDate",
    "ac_lastupdate",
]

# Static EU+EEA+UK+CH country codes (fallback if pycountry not available)
STATIC_COUNTRY_CODES = {
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR", "GR",
    "HR", "HU", "IE", "IS", "IT", "LI", "LT", "LU", "LV", "MT", "NL", "NO",
    "PL", "PT", "RO", "SE", "SI", "SK", "EL",  # EU + EEA
    "GB", "UK",  # UK
    "CH",  # Switzerland
}


class Severity(Enum):
    """Issue severity levels"""
    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass
class Issue:
    """Represents a validation issue found in the CSV"""
    severity: Severity
    code: str
    message: str
    column: Optional[str] = None
    rows: List[int] = field(default_factory=list)  # 1-based row numbers
    examples: List[str] = field(default_factory=list)

    def to_dict(self, max_examples: int = 5) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "severity": self.severity.value,
            "code": self.code,
            "message": self.message,
            "column": self.column,
            "rows": self.rows[:max_examples] if max_examples else self.rows,
            "examples": self.examples[:max_examples] if max_examples else self.examples,
        }


@dataclass
class EncodingInfo:
    """Encoding detection result"""
    detected: str
    confidence: float = 1.0
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "detected": self.detected,
            "confidence": self.confidence,
            "notes": self.notes,
        }


def detect_encoding(file_path: Path) -> EncodingInfo:
    """
    Detect CSV file encoding.
    Uses charset-normalizer if available, otherwise falls back to utf-8-sig.
    """
    if HAS_CHARSET_NORMALIZER:
        try:
            with open(file_path, "rb") as f:
                result = charset_normalizer.detect(f.read())
                if result and result.get("encoding"):
                    encoding = result["encoding"]
                    confidence = result.get("confidence", 1.0)
                    return EncodingInfo(
                        detected=encoding,
                        confidence=confidence,
                        notes="Detected using charset-normalizer"
                    )
        except Exception:
            pass

    # Fallback: try utf-8-sig first, then latin-1
    try:
        with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
            f.read(1024)  # Try reading a bit
        return EncodingInfo(
            detected="utf-8-sig",
            confidence=0.8,
            notes="Fallback: utf-8-sig (charset-normalizer not available)"
        )
    except UnicodeDecodeError:
        return EncodingInfo(
            detected="latin-1",
            confidence=0.5,
            notes="Fallback: latin-1 (charset-normalizer not available, utf-8 failed)"
        )


def classify_date(value: str) -> Dict[str, Any]:
    """
    Classify a date value.
    Returns: {"ok": bool, "repairable": bool, "normalized_hint": str|None}
    """
    if not value or not value.strip():
        return {"ok": False, "repairable": False, "normalized_hint": None}

    value = value.strip()

    # Check for repairable ESMA glitch: dot before year (e.g., "01/12/.2025")
    # Pattern: DD/MM/.YYYY or DD/MM/ .YYYY or DD/MM/. YYYY
    # Note: there's a slash before the dot, so pattern is DD/MM/\.YYYY
    repairable_pattern = re.compile(r'(\d{2}/\d{2})/\.\s*(\d{4})')
    match = repairable_pattern.search(value)
    if match:
        normalized = repairable_pattern.sub(r'\1/\2', value)
        return {
            "ok": False,
            "repairable": True,
            "normalized_hint": normalized
        }

    # Try DD/MM/YYYY format
    try:
        datetime.strptime(value, "%d/%m/%Y")
        return {"ok": True, "repairable": False, "normalized_hint": None}
    except ValueError:
        pass

    # Try YYYY-MM-DD format
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return {"ok": True, "repairable": False, "normalized_hint": None}
    except ValueError:
        pass

    return {"ok": False, "repairable": False, "normalized_hint": None}


def extract_service_codes(service_text: str) -> Tuple[List[str], bool]:
    """
    Extract service codes (a-j) from service text.
    Returns: (list of valid codes, has_suspicious_format)
    """
    if not service_text or not service_text.strip():
        return [], False

    # Split by common separators: |, ;, comma
    parts = re.split(r'[|;,]', service_text)
    valid_codes = []
    has_suspicious = False

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Look for letter a-j at start (with optional period and space)
        match = re.match(r'^([a-j])\.?\s*', part, re.IGNORECASE)
        if match:
            code = match.group(1).lower()
            if code not in valid_codes:
                valid_codes.append(code)
        elif len(part) == 1 and part.lower() in 'abcdefghij':
            code = part.lower()
            if code not in valid_codes:
                valid_codes.append(code)
        else:
            # Check if there are letters outside a-j range
            if re.search(r'[k-z]', part, re.IGNORECASE):
                has_suspicious = True

    return valid_codes, has_suspicious


def validate_country_code(code: str) -> bool:
    """
    Validate a 2-letter country code.
    Uses pycountry if available, otherwise static set.
    EL is accepted as valid (EU-speak for Greece).
    """
    code = code.strip().upper()
    if not re.match(r'^[A-Z]{2}$', code):
        return False

    # EL is valid (EU-speak for Greece, but not ISO 3166-1 alpha-2)
    if code == 'EL':
        return True

    if HAS_PYCOUNTRY:
        try:
            pycountry.countries.get(alpha_2=code)
            return True
        except (KeyError, AttributeError):
            return False
    else:
        return code in STATIC_COUNTRY_CODES


def read_csv_with_encoding(file_path: Path, encoding: str) -> Tuple[List[List[str]], List[str], int, int]:
    """
    Read CSV file and return (rows, header, rows_total, rows_parsed).
    Uses csv module with newline='' for proper handling.
    """
    rows = []
    header = []
    rows_total = 0
    rows_parsed = 0

    try:
        with open(file_path, "r", encoding=encoding, newline="") as f:
            reader = csv.reader(f)
            header = next(reader, [])
            header_len = len(header)
            rows_total = 1  # Header row

            for row in reader:
                rows_total += 1
                if len(row) == header_len:
                    rows_parsed += 1
                    rows.append(row)
                # If mismatch, we still track it but don't add to rows list
                # The validation will catch this separately

    except UnicodeDecodeError:
        # If encoding fails, try latin-1 as last resort
        if encoding != "latin-1":
            return read_csv_with_encoding(file_path, "latin-1")
        raise

    return rows, header, rows_total, rows_parsed


def validate_csv_structure(
    file_path: Path,
    encoding: str,
    issues: List[Issue]
) -> Tuple[List[List[str]], List[str], int, int]:
    """
    Validate CSV structure and parse integrity.
    Returns: (rows, header, rows_total, rows_parsed)
    """
    rows = []
    header = []
    rows_total = 0
    rows_parsed = 0
    mismatched_rows = []

    try:
        with open(file_path, "r", encoding=encoding, newline="") as f:
            reader = csv.reader(f)
            header = next(reader, [])
            header_len = len(header)
            rows_total = 1  # Header row

            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                rows_total += 1
                if len(row) == header_len:
                    rows_parsed += 1
                    rows.append(row)
                else:
                    mismatched_rows.append(row_num)
                    # Still try to add row for other validations, but truncated/padded
                    if len(row) < header_len:
                        row.extend([""] * (header_len - len(row)))
                    else:
                        row = row[:header_len]
                    rows.append(row)

    except UnicodeDecodeError:
        if encoding != "latin-1":
            # Try latin-1 as fallback
            return validate_csv_structure(file_path, "latin-1", issues)
        raise

    if mismatched_rows:
        examples = []
        for row_num in mismatched_rows[:3]:
            try:
                with open(file_path, "r", encoding=encoding, newline="") as f:
                    reader = csv.reader(f)
                    for i, row in enumerate(reader):
                        if i + 1 == row_num:
                            row_preview = " ".join(row[:3])[:120]
                            examples.append(f"Row {row_num}: {row_preview}...")
                            break
            except Exception:
                pass

        issues.append(Issue(
            severity=Severity.ERROR,
            code="ROW_COLUMN_COUNT_MISMATCH",
            message=f"Found {len(mismatched_rows)} row(s) with column count mismatch",
            rows=mismatched_rows,
            examples=examples
        ))

    return rows, header, rows_total, rows_parsed


def validate_schema(header: List[str], issues: List[Issue]) -> None:
    """Validate CSV schema/header"""
    # Check for required columns
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in header]
    if missing_columns:
        issues.append(Issue(
            severity=Severity.ERROR,
            code="SCHEMA_MISSING_COLUMN",
            message=f"Missing required columns: {', '.join(missing_columns)}",
            examples=missing_columns
        ))

    # Check for duplicate columns
    seen = {}
    duplicates = []
    for idx, col in enumerate(header):
        col_stripped = col.strip()
        if col_stripped in seen:
            duplicates.append(col_stripped)
        else:
            seen[col_stripped] = idx

    if duplicates:
        issues.append(Issue(
            severity=Severity.ERROR,
            code="SCHEMA_DUPLICATE_COLUMN",
            message=f"Duplicate column names found: {', '.join(duplicates)}",
            examples=duplicates
        ))

    # Check for whitespace in headers
    whitespace_cols = []
    for col in header:
        if col != col.strip():
            whitespace_cols.append(col)

    if whitespace_cols:
        issues.append(Issue(
            severity=Severity.WARNING,
            code="SCHEMA_HEADER_WHITESPACE",
            message=f"Columns with leading/trailing whitespace: {len(whitespace_cols)}",
            examples=whitespace_cols[:5]
        ))


def validate_lei_format(rows: List[List[str]], header: List[str], issues: List[Issue]) -> None:
    """Validate LEI format"""
    if "ae_lei" not in header:
        return

    lei_idx = header.index("ae_lei")
    lei_pattern = re.compile(r'^[A-Z0-9]{20}$')
    invalid_rows = []
    examples = []

    for row_num, row in enumerate(rows, start=2):  # Start at 2 (header is row 1)
        if lei_idx >= len(row):
            continue
        lei = row[lei_idx].strip()
        if lei and not lei_pattern.match(lei):
            invalid_rows.append(row_num)
            if len(examples) < 5:
                examples.append(lei[:50])

    if invalid_rows:
        issues.append(Issue(
            severity=Severity.ERROR,
            code="LEI_INVALID_FORMAT",
            message=f"Found {len(invalid_rows)} LEI(s) with invalid format (must be 20 alphanumeric characters)",
            column="ae_lei",
            rows=invalid_rows,
            examples=examples
        ))


def validate_duplicate_lei(rows: List[List[str]], header: List[str], issues: List[Issue]) -> None:
    """Detect duplicate LEI codes"""
    if "ae_lei" not in header:
        return

    lei_idx = header.index("ae_lei")
    lei_counts: Dict[str, List[int]] = {}

    for row_num, row in enumerate(rows, start=2):
        if lei_idx >= len(row):
            continue
        lei = row[lei_idx].strip()
        if lei:
            if lei not in lei_counts:
                lei_counts[lei] = []
            lei_counts[lei].append(row_num)

    duplicates = {lei: rows_list for lei, rows_list in lei_counts.items() if len(rows_list) > 1}
    if duplicates:
        example_leis = list(duplicates.keys())[:5]
        all_duplicate_rows = []
        for rows_list in duplicates.values():
            all_duplicate_rows.extend(rows_list)

        issues.append(Issue(
            severity=Severity.WARNING,
            code="LEI_DUPLICATE",
            message=f"Found {len(duplicates)} duplicate LEI(s) across {len(all_duplicate_rows)} rows",
            column="ae_lei",
            rows=all_duplicate_rows[:20],  # Limit rows shown
            examples=example_leis
        ))


def validate_dates(rows: List[List[str]], header: List[str], issues: List[Issue]) -> None:
    """Validate date columns"""
    date_issues_unparsable = []
    date_issues_repairable = []

    for date_col in DATE_COLUMNS:
        if date_col not in header:
            continue

        col_idx = header.index(date_col)
        unparsable_rows = []
        repairable_rows = []
        unparsable_examples = []
        repairable_examples = []

        for row_num, row in enumerate(rows, start=2):
            if col_idx >= len(row):
                continue
            value = row[col_idx].strip()
            if not value:
                continue

            date_info = classify_date(value)
            if not date_info["ok"]:
                if date_info["repairable"]:
                    repairable_rows.append(row_num)
                    if len(repairable_examples) < 3:
                        repairable_examples.append(f"{value} → {date_info['normalized_hint']}")
                else:
                    unparsable_rows.append(row_num)
                    if len(unparsable_examples) < 3:
                        unparsable_examples.append(value)

        if repairable_rows:
            date_issues_repairable.append({
                "column": date_col,
                "rows": repairable_rows,
                "examples": repairable_examples
            })

        if unparsable_rows:
            date_issues_unparsable.append({
                "column": date_col,
                "rows": unparsable_rows,
                "examples": unparsable_examples
            })

    # Report repairable dates as warnings
    for issue_data in date_issues_repairable:
        issues.append(Issue(
            severity=Severity.WARNING,
            code="DATE_NEEDS_NORMALIZATION",
            message=f"Column '{issue_data['column']}': {len(issue_data['rows'])} date(s) need normalization (e.g., dot before year)",
            column=issue_data["column"],
            rows=issue_data["rows"],
            examples=issue_data["examples"]
        ))

    # Report unparsable dates as errors
    for issue_data in date_issues_unparsable:
        issues.append(Issue(
            severity=Severity.ERROR,
            code="DATE_UNPARSABLE",
            message=f"Column '{issue_data['column']}': {len(issue_data['rows'])} unparsable date(s)",
            column=issue_data["column"],
            rows=issue_data["rows"],
            examples=issue_data["examples"]
        ))


def validate_service_codes(rows: List[List[str]], header: List[str], issues: List[Issue]) -> None:
    """Validate service codes"""
    if "ac_serviceCode" not in header:
        return

    col_idx = header.index("ac_serviceCode")
    invalid_rows = []
    suspicious_rows = []
    invalid_examples = []
    suspicious_examples = []

    for row_num, row in enumerate(rows, start=2):
        if col_idx >= len(row):
            continue
        value = row[col_idx].strip()
        if not value:
            continue

        codes, has_suspicious = extract_service_codes(value)
        if not codes:
            invalid_rows.append(row_num)
            if len(invalid_examples) < 3:
                invalid_examples.append(value[:100])
        elif has_suspicious:
            suspicious_rows.append(row_num)
            if len(suspicious_examples) < 3:
                suspicious_examples.append(value[:100])

    if invalid_rows:
        issues.append(Issue(
            severity=Severity.ERROR,
            code="SERVICE_CODE_INVALID",
            message=f"Found {len(invalid_rows)} row(s) with invalid service codes (no valid codes a-j found)",
            column="ac_serviceCode",
            rows=invalid_rows,
            examples=invalid_examples
        ))

    if suspicious_rows:
        issues.append(Issue(
            severity=Severity.WARNING,
            code="SERVICE_CODE_SUSPICIOUS_FORMAT",
            message=f"Found {len(suspicious_rows)} row(s) with suspicious service code format (contains letters outside a-j)",
            column="ac_serviceCode",
            rows=suspicious_rows,
            examples=suspicious_examples
        ))


def validate_country_codes(rows: List[List[str]], header: List[str], issues: List[Issue]) -> None:
    """Validate country codes"""
    if "ac_serviceCode_cou" not in header:
        return

    col_idx = header.index("ac_serviceCode_cou")
    invalid_rows = []
    invalid_examples = []

    for row_num, row in enumerate(rows, start=2):
        if col_idx >= len(row):
            continue
        value = row[col_idx].strip()
        if not value:
            continue

        # Split by pipe, semicolon, or comma
        codes = re.split(r'[|;,]', value)
        for code in codes:
            code = code.strip()
            if not code:
                continue
            if not validate_country_code(code):
                invalid_rows.append(row_num)
                if len(invalid_examples) < 5:
                    invalid_examples.append(code)
                break  # Only report once per row

    if invalid_rows:
        issues.append(Issue(
            severity=Severity.ERROR,
            code="COUNTRY_CODE_INVALID",
            message=f"Found {len(invalid_rows)} row(s) with invalid country codes",
            column="ac_serviceCode_cou",
            rows=invalid_rows,
            examples=invalid_examples
        ))

    # Warn if pycountry not available
    if not HAS_PYCOUNTRY:
        issues.append(Issue(
            severity=Severity.WARNING,
            code="COUNTRY_CODE_VALIDATION_PARTIAL",
            message="Country code validation is partial (pycountry not available, using static EU+EEA+UK+CH set)",
            examples=[]
        ))


def validate_multiline_fields(rows: List[List[str]], header: List[str], issues: List[Issue]) -> None:
    """Detect multiline fields"""
    website_col = "ae_website" if "ae_website" in header else None
    multiline_website_rows = []
    multiline_other_rows = []
    multiline_website_examples = []
    multiline_other_examples = []

    for col_idx, col_name in enumerate(header):
        for row_num, row in enumerate(rows, start=2):
            if col_idx >= len(row):
                continue
            value = row[col_idx]
            if '\n' in value or '\r' in value:
                if col_name == website_col:
                    multiline_website_rows.append((row_num, col_name))
                    if len(multiline_website_examples) < 3:
                        preview = value.replace('\n', '\\n').replace('\r', '\\r')[:80]
                        multiline_website_examples.append(f"Row {row_num}: {preview}...")
                else:
                    multiline_other_rows.append((row_num, col_name))
                    if len(multiline_other_examples) < 3:
                        preview = value.replace('\n', '\\n').replace('\r', '\\r')[:80]
                        multiline_other_examples.append(f"Row {row_num}, {col_name}: {preview}...")

    if multiline_website_rows:
        issues.append(Issue(
            severity=Severity.WARNING,
            code="MULTILINE_WEBSITE",
            message=f"Found {len(multiline_website_rows)} row(s) with multiline website fields",
            column="ae_website",
            rows=[r[0] for r in multiline_website_rows[:20]],
            examples=multiline_website_examples
        ))

    if multiline_other_rows:
        issues.append(Issue(
            severity=Severity.ERROR,
            code="MULTILINE_FIELD",
            message=f"Found {len(multiline_other_rows)} row(s) with multiline fields in non-website columns",
            rows=[r[0] for r in multiline_other_rows[:20]],
            examples=multiline_other_examples
        ))


def validate_encoding(rows: List[List[str]], header: List[str], issues: List[Issue]) -> None:
    """Detect encoding symptoms (mojibake)"""
    suspect_rows = []
    suspect_examples = []

    for col_idx, col_name in enumerate(header):
        for row_num, row in enumerate(rows, start=2):
            if col_idx >= len(row):
                continue
            value = row[col_idx]
            if not isinstance(value, str):
                continue

            # Check for replacement character
            if '\ufffd' in value or '\xef\xbf\xbd' in value:
                suspect_rows.append((row_num, col_name))
                if len(suspect_examples) < 5:
                    # Find the problematic substring
                    idx = value.find('\ufffd')
                    if idx == -1:
                        idx = value.find('\xef\xbf\xbd')
                    context = value[max(0, idx-10):idx+10]
                    suspect_examples.append(f"Row {row_num}, {col_name}: ...{context}...")
                    break  # Only one example per row

            # Check for UTF-8 mis-decoded patterns
            if 'Ã' in value or 'Â' in value:
                suspect_rows.append((row_num, col_name))
                if len(suspect_examples) < 5:
                    # Find pattern
                    for pattern in ['Ã¤', 'Ã¶', 'Ã¼', 'Ã', 'Â']:
                        if pattern in value:
                            idx = value.find(pattern)
                            context = value[max(0, idx-10):idx+20]
                            suspect_examples.append(f"Row {row_num}, {col_name}: ...{context}...")
                            break
                    break  # Only one example per row

    if suspect_rows:
        issues.append(Issue(
            severity=Severity.WARNING,
            code="ENCODING_SUSPECT",
            message=f"Found {len(suspect_rows)} row(s) with potential encoding issues (replacement characters or UTF-8 mis-decoding)",
            rows=[r[0] for r in suspect_rows[:20]],
            examples=suspect_examples
        ))


def validate_csv(file_path: Path, max_examples: int = 5) -> Dict[str, Any]:
    """
    Main validation function.
    Returns a dictionary suitable for JSON serialization.
    """
    issues: List[Issue] = []
    encoding_info = detect_encoding(file_path)

    # Read CSV with structure validation
    rows, header, rows_total, rows_parsed = validate_csv_structure(
        file_path, encoding_info.detected, issues
    )

    # Run all validations
    validate_schema(header, issues)
    validate_lei_format(rows, header, issues)
    validate_duplicate_lei(rows, header, issues)
    validate_dates(rows, header, issues)
    validate_service_codes(rows, header, issues)
    validate_country_codes(rows, header, issues)
    validate_multiline_fields(rows, header, issues)
    validate_encoding(rows, header, issues)

    # Count issues by severity
    error_count = sum(1 for issue in issues if issue.severity == Severity.ERROR)
    warning_count = sum(1 for issue in issues if issue.severity == Severity.WARNING)
    
    # Build report
    report = {
        "version": 1,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "input_file": str(file_path),
        "encoding": encoding_info.to_dict(),
        "stats": {
            "rows_total": rows_total,
            "rows_parsed": rows_parsed,
            "columns": len(header),
            "header": header,
            "errors": error_count,
            "warnings": warning_count,
            # Aliases with capital letters for grep compatibility
            "Errors": error_count,
            "Warnings": warning_count,
        },
        "issues": [issue.to_dict(max_examples) for issue in issues],
    }

    return report
