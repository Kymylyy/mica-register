"""
CSV Cleaning Module for ESMA MiCA Registers

Automatically fixes detected validation issues in CSV files and produces
a clean CSV file ready for import. Tracks all changes made for reporting.

Supports all 5 ESMA MiCA registers: CASP, OTHER, ART, EMT, NCASP
"""

import pandas as pd
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field

# Import fix functions from import_csv.py
from .import_csv import (
    parse_date,
    fix_encoding_issues as fix_text_encoding,  # Rename to avoid conflict
    normalize_commercial_name,
    fix_address_website_parsing,
    normalize_service_code,
    is_url,
    parse_pipe_separated,
)
from .config.constants import MICA_SERVICE_DESCRIPTIONS

# Import register configuration
from .config.registers import RegisterType, get_register_config

# Import encoding detection from csv_validate
from .csv_validate import detect_encoding, EncodingInfo


@dataclass
class Change:
    """Represents a single change made during cleaning"""
    type: str
    row: int  # 1-based row number
    column: str
    old_value: str
    new_value: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "row": self.row,
            "column": self.column,
            "old_value": self.old_value,
            "new_value": self.new_value,
        }


class CSVCleaner:
    """Cleans CSV files by fixing validation issues for a specific register type"""

    def __init__(self, csv_path: Path, register_type: RegisterType = RegisterType.CASP):
        self.csv_path = csv_path
        self.register_type = register_type
        self.config = get_register_config(register_type)
        self.df: Optional[pd.DataFrame] = None
        self.changes: List[Change] = []
        self.encoding_info: Optional[EncodingInfo] = None
        self.rows_before = 0
        self.rows_after = 0

    def load_csv(self) -> bool:
        """Load CSV with encoding detection"""
        try:
            # Detect encoding
            self.encoding_info = detect_encoding(self.csv_path)

            # Try multiple encodings
            encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'windows-1252']
            encoding_used = self.encoding_info.detected

            if encoding_used not in encodings:
                encoding_used = 'utf-8-sig'

            try:
                self.df = pd.read_csv(
                    self.csv_path,
                    encoding=encoding_used,
                    encoding_errors='replace',
                    dtype=str,  # Force string type
                    keep_default_na=False,  # Don't interpret as NaN
                    na_filter=False  # Don't filter NA values
                )
            except (UnicodeDecodeError, UnicodeError):
                # Fallback to latin-1
                self.df = pd.read_csv(
                    self.csv_path,
                    encoding='latin-1',
                    encoding_errors='replace',
                    dtype=str,  # Force string type
                    keep_default_na=False,  # Don't interpret as NaN
                    na_filter=False  # Don't filter NA values
                )

            self.rows_before = len(self.df)
            return True
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return False

    def fix_whitespace_globally(self) -> None:
        """Fix NBSP, trailing spaces, and normalize whitespace globally"""
        # Get date columns dynamically based on register type
        date_columns = []
        for csv_col in self.config.column_mapping.keys():
            if 'date' in csv_col.lower() or 'lastupdate' in csv_col.lower():
                date_columns.append(csv_col)

        for col in self.df.columns:
            for idx, row in self.df.iterrows():
                value = row.get(col)
                if pd.notna(value):
                    original = str(value)
                    # Replace NBSP with regular space
                    fixed = original.replace('\xa0', ' ')
                    # Strip leading/trailing whitespace
                    fixed = fixed.strip()
                    # For text columns (not dates/numbers), collapse multiple spaces
                    if col not in date_columns and col != 'ae_lei':
                        fixed = re.sub(r'\s+', ' ', fixed)
                    
                    if fixed != original:
                        self.df.at[idx, col] = fixed
                        self.changes.append(Change(
                            type="WHITESPACE_FIXED",
                            row=idx + 2,
                            column=col,
                            old_value=original[:100],
                            new_value=fixed[:100]
                        ))

    def fix_encoding_issues(self) -> None:
        """Fix encoding issues in text columns"""
        # Get text columns dynamically - address, names, comments, etc.
        text_columns = []
        for csv_col in self.config.column_mapping.keys():
            if any(keyword in csv_col.lower() for keyword in ['address', 'name', 'authority', 'comments', 'reason', 'infringement']):
                text_columns.append(csv_col)

        for col in text_columns:
            if col not in self.df.columns:
                continue

            for idx, row in self.df.iterrows():
                value = row.get(col)
                if pd.notna(value):
                    original = str(value)
                    fixed = fix_text_encoding(original)
                    if fixed != original:
                        self.df.at[idx, col] = fixed
                        self.changes.append(Change(
                            type="ENCODING_FIXED",
                            row=idx + 2,  # +2 because header is row 1, data starts at row 2
                            column=col,
                            old_value=original[:100],  # Limit length
                            new_value=fixed[:100]
                        ))

    def detect_and_fix_encoding_data_loss(self) -> None:
        """Detect encoding data loss and attempt to fix before reporting"""
        # Get text columns dynamically
        text_columns = []
        for csv_col in self.config.column_mapping.keys():
            if any(keyword in csv_col.lower() for keyword in ['address', 'name', 'authority', 'comments', 'website', 'url', 'reason', 'infringement']):
                text_columns.append(csv_col)

        for col in text_columns:
            if col not in self.df.columns:
                continue
            
            for idx, row in self.df.iterrows():
                value = row.get(col)
                if pd.notna(value):
                    text = str(value)
                    # Check for replacement character
                    if '\ufffd' in text or '\xef\xbf\xbd' in text:
                        # First, try to fix using existing fix_text_encoding function
                        fixed = fix_text_encoding(text)
                        
                        # Check if fix removed replacement char
                        if '\ufffd' not in fixed and '\xef\xbf\xbd' not in fixed:
                            # Successfully fixed!
                            self.df.at[idx, col] = fixed
                            self.changes.append(Change(
                                type="ENCODING_DATA_LOSS_FIXED",
                                row=idx + 2,
                                column=col,
                                old_value=text[:100],
                                new_value=fixed[:100]
                            ))
                        else:
                            # Could not fix - report as warning (does not block)
                            pos = text.find('\ufffd')
                            if pos == -1:
                                pos = text.find('\xef\xbf\xbd')
                            context = text[max(0, pos-10):pos+10]
                            
                            self.changes.append(Change(
                                type="ENCODING_DATA_LOSS_WARNING",
                                row=idx + 2,
                                column=col,
                                old_value=context,
                                new_value="[WARNING: Replacement character detected - could not auto-fix, left as-is]"
                            ))
                            # Leave original value - don't modify

    def normalize_country_codes(self) -> None:
        """Normalize country codes: strip, upper, map EL->GR, dedup (CASP only)"""
        # Only for CASP register
        if self.register_type != RegisterType.CASP:
            return

        if 'ac_serviceCode_cou' not in self.df.columns:
            return

        for idx, row in self.df.iterrows():
            value = row.get('ac_serviceCode_cou')
            if pd.notna(value) and str(value).strip():
                original = str(value).strip()
                # Split by |, ;, comma, or whitespace
                codes = re.split(r'[|;,\s]+', original)
                normalized_codes = set()
                
                for code in codes:
                    code = code.strip().upper()
                    if not code:
                        continue
                    
                    # Map EL to GR (but keep EL in set if it appears)
                    if code == 'EL':
                        normalized_codes.add('GR')  # Add GR
                        normalized_codes.add('EL')  # Also keep EL (both valid)
                    else:
                        normalized_codes.add(code)
                
                if normalized_codes:
                    # Sort and join with |
                    fixed = '|'.join(sorted(normalized_codes))
                    if fixed != original:
                        self.df.at[idx, 'ac_serviceCode_cou'] = fixed
                        self.changes.append(Change(
                            type="COUNTRY_CODE_NORMALIZED",
                            row=idx + 2,
                            column="ac_serviceCode_cou",
                            old_value=original,
                            new_value=fixed
                        ))

    def fix_dates(self) -> None:
        """Fix date format issues using parse_date() function"""
        # Get date columns dynamically based on register config
        date_columns = []
        for csv_col in self.config.column_mapping.keys():
            if 'date' in csv_col.lower() or 'lastupdate' in csv_col.lower():
                date_columns.append(csv_col)

        for col in date_columns:
            if col not in self.df.columns:
                continue
            
            for idx, row in self.df.iterrows():
                date_str = row.get(col)
                if pd.notna(date_str) and str(date_str).strip():
                    original = str(date_str).strip()

                    # Try to parse using existing parse_date() function with register-specific format
                    parsed_date = parse_date(original, self.config.date_format)

                    if parsed_date:
                        # Format back to register-specific format
                        formatted = parsed_date.strftime(self.config.date_format)
                        if formatted != original:
                            self.df.at[idx, col] = formatted
                            self.changes.append(Change(
                                type="DATE_FIXED",
                                row=idx + 2,
                                column=col,
                                old_value=original,
                                new_value=formatted
                            ))
                    else:
                        # Cannot parse - leave original value, let import_csv.py handle it
                        # Only report as warning (does not block cron job)
                        self.changes.append(Change(
                            type="DATE_WARNING",
                            row=idx + 2,
                            column=col,
                            old_value=original,
                            new_value="[WARNING: Could not parse date - left as-is, import_csv.py will attempt to fix]"
                        ))
                        # Keep original value - don't modify

    def fix_multiline_fields(self) -> None:
        """Fix multiline fields with better handling for websites"""
        # Handle website separately with URL deduplication
        # Find website column dynamically
        website_col = None
        for col in self.df.columns:
            if 'website' in col.lower() or 'url' in col.lower():
                website_col = col
                break

        if website_col and website_col in self.df.columns:
            for idx, row in self.df.iterrows():
                value = row.get(website_col)
                if pd.notna(value):
                    original = str(value)
                    if '\n' in original or '\r' in original:
                        # Split by whitespace/newline
                        parts = re.split(r'[\s\n\r]+', original)
                        # Filter and deduplicate URLs
                        urls = []
                        seen = set()
                        for part in parts:
                            part = part.strip()
                            if part and (is_url(part) or part.startswith('www.') or '.' in part):
                                # Normalize URL (add https:// if missing)
                                if not part.startswith(('http://', 'https://')):
                                    if part.startswith('www.'):
                                        part = 'https://' + part
                                    elif '.' in part:
                                        part = 'https://' + part
                                if part not in seen:
                                    seen.add(part)
                                    urls.append(part)

                        fixed = '|'.join(urls) if urls else ' '.join(parts)
                        if fixed != original:
                            self.df.at[idx, website_col] = fixed
                            self.changes.append(Change(
                                type="MULTILINE_WEBSITE_FIXED",
                                row=idx + 2,
                                column=website_col,
                                old_value=original[:100],
                                new_value=fixed[:100]
                            ))

        # Handle other multiline fields (address, comments) with space replacement
        # Find dynamically based on column names
        text_columns = []
        for col in self.df.columns:
            if any(keyword in col.lower() for keyword in ['address', 'comments', 'reason']):
                text_columns.append(col)

        for col in text_columns:
            if col not in self.df.columns:
                continue

            for idx, row in self.df.iterrows():
                value = row.get(col)
                if pd.notna(value):
                    original = str(value)
                    if '\n' in original or '\r' in original:
                        fixed = original.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
                        # Clean up multiple spaces
                        fixed = re.sub(r'\s+', ' ', fixed).strip()
                        if fixed != original:
                            self.df.at[idx, col] = fixed
                            self.changes.append(Change(
                                type="MULTILINE_FIXED",
                                row=idx + 2,
                                column=col,
                                old_value=original[:100],
                                new_value=fixed[:100]
                            ))

    def fix_lei_format(self) -> None:
        """Fix LEI format issues - attempt aggressive fixes before giving up"""
        if 'ae_lei' not in self.df.columns:
            return

        lei_pattern = re.compile(r'^[A-Z0-9]{20}$')
        warnings = []

        for idx, row in self.df.iterrows():
            lei = str(row.get('ae_lei', '')).strip()
            if not lei or pd.isna(row.get('ae_lei')):
                continue

            original = lei
            fixed = lei

            # Remove trailing dot
            if lei.endswith('.'):
                fixed = lei.rstrip('.')
                if fixed != original:
                    self.df.at[idx, 'ae_lei'] = fixed
                    self.changes.append(Change(
                        type="LEI_TRAILING_DOT_REMOVED",
                        row=idx + 2,
                        column="ae_lei",
                        old_value=original,
                        new_value=fixed
                    ))
                    lei = fixed
                    if lei_pattern.match(fixed):
                        continue

            # Check for Excel scientific notation (e.g., 9.60E+19)
            if 'E+' in lei.upper() or 'E-' in lei.upper():
                # Try to recover: convert scientific notation to integer, then to string
                try:
                    num = float(lei)
                    recovered = str(int(num)).upper()
                    # Pad or truncate to 20 characters
                    if len(recovered) == 20:
                        fixed = recovered
                        self.df.at[idx, 'ae_lei'] = fixed
                        self.changes.append(Change(
                            type="LEI_EXCEL_NOTATION_FIXED",
                            row=idx + 2,
                            column="ae_lei",
                            old_value=original,
                            new_value=fixed
                        ))
                        if lei_pattern.match(fixed):
                            continue
                    else:
                        warnings.append({
                            "row": idx + 2,
                            "lei": lei,
                            "reason": f"Excel scientific notation - recovered length {len(recovered)}, expected 20"
                        })
                except (ValueError, OverflowError):
                    warnings.append({
                        "row": idx + 2,
                        "lei": lei,
                        "reason": "Excel scientific notation - cannot convert"
                    })
                continue

            # Try removing all non-alphanumeric characters
            cleaned = re.sub(r'[^A-Z0-9]', '', lei.upper())
            if len(cleaned) == 20 and cleaned != lei:
                fixed = cleaned
                self.df.at[idx, 'ae_lei'] = fixed
                self.changes.append(Change(
                    type="LEI_CLEANED",
                    row=idx + 2,
                    column="ae_lei",
                    old_value=original,
                    new_value=fixed
                ))
                if lei_pattern.match(fixed):
                    continue

            # Check if still invalid after all fixes
            if not lei_pattern.match(fixed):
                warnings.append({
                    "row": idx + 2,
                    "lei": fixed,
                    "reason": f"Invalid format (length: {len(fixed)}, expected: 20)"
                })

        # Store warnings (not blocking errors) for report
        if warnings:
            for item in warnings:
                self.changes.append(Change(
                    type="LEI_WARNING",
                    row=item["row"],
                    column="ae_lei",
                    old_value=item["lei"],
                    new_value=f"[WARNING: {item['reason']} - left as-is, import may skip this row]"
                ))
                # Leave original value - don't modify (import_csv.py will handle)

    def fix_address_website_parsing(self) -> None:
        """Fix address/website parsing issues"""
        if 'ae_address' not in self.df.columns or 'ae_website' not in self.df.columns:
            return

        for idx, row in self.df.iterrows():
            fixed_address, fixed_website = fix_address_website_parsing(row)

            original_address = str(row.get('ae_address', '')).strip() if pd.notna(row.get('ae_address')) else ''
            original_website = str(row.get('ae_website', '')).strip() if pd.notna(row.get('ae_website')) else ''

            if fixed_address and fixed_address != original_address:
                self.df.at[idx, 'ae_address'] = fixed_address
                self.changes.append(Change(
                    type="ADDRESS_PARSING_FIXED",
                    row=idx + 2,
                    column="ae_address",
                    old_value=original_address[:100],
                    new_value=fixed_address[:100]
                ))

            if fixed_website is not None and str(fixed_website) != original_website:
                self.df.at[idx, 'ae_website'] = fixed_website if fixed_website else ''
                self.changes.append(Change(
                    type="WEBSITE_PARSING_FIXED",
                    row=idx + 2,
                    column="ae_website",
                    old_value=original_website[:100],
                    new_value=str(fixed_website)[:100] if fixed_website else ""
                ))

    def normalize_service_codes(self) -> None:
        """Normalize service codes to standard format (CASP only)"""
        # Only for CASP register
        if self.register_type != RegisterType.CASP:
            return

        if 'ac_serviceCode' not in self.df.columns:
            return

        for idx, row in self.df.iterrows():
            service_texts = parse_pipe_separated(row.get('ac_serviceCode'))
            normalized_codes = set()

            for service_text in service_texts:
                normalized = normalize_service_code(service_text)
                if normalized:
                    normalized_codes.add(normalized)

            if normalized_codes:
                # Convert back to pipe-separated format with descriptions
                normalized_services = ' | '.join([
                    f"{code}. {MICA_SERVICE_DESCRIPTIONS.get(code, '')}"
                    for code in sorted(normalized_codes)
                ])

                original = str(row.get('ac_serviceCode', ''))
                if normalized_services != original:
                    self.df.at[idx, 'ac_serviceCode'] = normalized_services
                    self.changes.append(Change(
                        type="SERVICE_CODE_NORMALIZED",
                        row=idx + 2,
                        column="ac_serviceCode",
                        old_value=original[:100],
                        new_value=normalized_services[:100]
                    ))

    def normalize_commercial_names(self) -> None:
        """Normalize commercial names"""
        if 'ae_commercial_name' not in self.df.columns:
            return

        for idx, row in self.df.iterrows():
            name = row.get('ae_commercial_name')
            if pd.notna(name):
                original = str(name)
                fixed = normalize_commercial_name(original)
                if fixed and fixed != original:
                    self.df.at[idx, 'ae_commercial_name'] = fixed
                    self.changes.append(Change(
                        type="COMMERCIAL_NAME_NORMALIZED",
                        row=idx + 2,
                        column="ae_commercial_name",
                        old_value=original,
                        new_value=fixed
                    ))

    def fix_all_issues(self) -> pd.DataFrame:
        """Apply all fixes in correct order"""
        if self.df is None:
            raise ValueError("CSV not loaded. Call load_csv() first.")

        # 1. Global whitespace cleanup FIRST (before other fixes)
        print("Fixing whitespace globally...")
        self.fix_whitespace_globally()
        
        # 2. Detect and attempt to fix encoding data loss
        print("Detecting and fixing encoding data loss...")
        self.detect_and_fix_encoding_data_loss()
        
        # 3. Fix encoding issues (known patterns)
        print("Fixing encoding issues...")
        self.fix_encoding_issues()
        
        # 4. Fix dates (using parse_date)
        print("Fixing dates...")
        self.fix_dates()
        
        # 5. Fix multiline fields (improved website handling)
        print("Fixing multiline fields...")
        self.fix_multiline_fields()
        
        # 6. Normalize country codes
        print("Normalizing country codes...")
        self.normalize_country_codes()
        
        # 7. Fix LEI format (aggressive attempts)
        print("Fixing LEI format...")
        self.fix_lei_format()
        
        # 8. [REMOVED] Merge duplicate LEI - preserving all rows
        # Duplicate LEI codes are now allowed (e.g., OTHER: one LEI, many white papers)
        print("Skipping duplicate LEI merge (preserving all rows)...")
        
        # 9. Fix address/website parsing
        print("Fixing address/website parsing...")
        self.fix_address_website_parsing()
        
        # 10. Normalize service codes
        print("Normalizing service codes...")
        self.normalize_service_codes()
        
        # 11. Normalize commercial names
        print("Normalizing commercial names...")
        self.normalize_commercial_names()

        self.rows_after = len(self.df)
        return self.df

    def save_clean_csv(self, output_path: Path) -> bool:
        """Save cleaned CSV to new file"""
        if self.df is None:
            return False

        try:
            # Save with UTF-8 encoding (standard)
            self.df.to_csv(output_path, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"Error saving CSV: {e}")
            return False

    def generate_report(self) -> Dict[str, Any]:
        """Generate cleaning report"""
        changes_by_type: Dict[str, int] = {}
        for change in self.changes:
            changes_by_type[change.type] = changes_by_type.get(change.type, 0) + 1

        return {
            "version": 1,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "input_file": str(self.csv_path),
            "encoding": self.encoding_info.to_dict() if self.encoding_info else {},
            "stats": {
                "rows_before": self.rows_before,
                "rows_after": self.rows_after,
                "columns": len(self.df.columns) if self.df is not None else 0,
            },
            "changes": [change.to_dict() for change in self.changes],
            "summary": {
                "total_changes": len(self.changes),
                "changes_by_type": changes_by_type
            }
        }
