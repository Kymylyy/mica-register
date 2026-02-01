#!/usr/bin/env python3
"""
CLI script for cleaning ESMA CASP register CSV files.

Automatically fixes validation issues and produces a clean CSV file.

Usage:
    python scripts/clean_csv.py --input <file> [--output <file>] [--dry-run] [--report <file>]

Examples:
    # Basic cleaning (creates input_clean.csv)
    python scripts/clean_csv.py --input CASP20251208.csv

    # Specify output file
    python scripts/clean_csv.py --input CASP20251208.csv --output clean.csv

    # Dry run (show what would be changed)
    python scripts/clean_csv.py --input CASP20251208.csv --dry-run

    # Save cleaning report
    python scripts/clean_csv.py --input CASP20251208.csv --output clean.csv --report report.json
"""

import sys
import argparse
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.csv_clean import CSVCleaner
from app.models import RegisterType
from app.config.registers import get_register_config
from app.utils.file_utils import get_base_data_dir
from typing import Optional


def detect_register_type(filename: str) -> Optional[RegisterType]:
    """Detect register type from CSV filename.

    Examples:
        CASP20260130.csv → RegisterType.CASP
        ART20260129_clean.csv → RegisterType.ART

    Args:
        filename: CSV filename to detect from

    Returns:
        RegisterType if detected, None otherwise
    """
    filename_upper = filename.upper()
    for register_type in RegisterType:
        prefix = get_register_config(register_type).csv_prefix
        if filename_upper.startswith(prefix):
            return register_type
    return None


def print_summary(report: dict, dry_run: bool = False) -> None:
    """Print human-readable summary"""
    stats = report["stats"]
    summary = report["summary"]
    changes = report["changes"]

    print("=" * 60)
    print("CSV Cleaning Report")
    if dry_run:
        print("🔍 DRY RUN MODE - No files will be modified")
    print("=" * 60)
    print(f"Input file: {report['input_file']}")
    if report.get("encoding"):
        enc = report["encoding"]
        print(f"Encoding: {enc.get('detected', 'unknown')} (confidence: {enc.get('confidence', 0):.2f})")
    print()
    print(f"Statistics:")
    print(f"  Rows before: {stats['rows_before']}")
    print(f"  Rows after: {stats['rows_after']}")
    print(f"  Columns: {stats['columns']}")
    print()

    print(f"Changes made:")
    print(f"  Total changes: {summary['total_changes']}")
    print()

    if summary.get("changes_by_type"):
        print("Changes by type:")
        for change_type, count in sorted(summary["changes_by_type"].items(), key=lambda x: x[1], reverse=True):
            print(f"  {change_type}: {count}")

    print()

    # Show sample changes
    if changes:
        print("Sample changes:")
        for change in changes[:10]:
            print(f"  • Row {change['row']}, {change['column']}: {change['type']}")
            if change.get('old_value') and change.get('new_value'):
                old_val = str(change['old_value'])[:50]
                new_val = str(change['new_value'])[:50]
                print(f"    '{old_val}' → '{new_val}'")
        if len(changes) > 10:
            print(f"  ... and {len(changes) - 10} more changes")
    else:
        print("✅ No changes needed - CSV is already clean!")

    print("=" * 60)


def main() -> int:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Clean ESMA CASP register CSV file by fixing validation issues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic cleaning (creates input_clean.csv)
  python scripts/clean_csv.py --input CASP20251208.csv

  # Specify output file
  python scripts/clean_csv.py --input CASP20251208.csv --output clean.csv

  # Dry run (show what would be changed)
  python scripts/clean_csv.py --input CASP20251208.csv --dry-run

  # Save cleaning report
  python scripts/clean_csv.py --input CASP20251208.csv --output clean.csv --report report.json
        """
    )

    parser.add_argument(
        "--input", "-i",
        type=Path,
        required=True,
        help="Input CSV file to clean"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output clean CSV file (default: {input}_clean.csv)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without creating file"
    )
    parser.add_argument(
        "--report", "-r",
        type=Path,
        help="Save cleaning report to JSON file"
    )

    args = parser.parse_args()

    # Validate input file
    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        return 2

    # Detect register type (with fallback to CASP)
    register_type = detect_register_type(args.input.name)
    if register_type:
        print(f"Detected register: {register_type.value.upper()}")
    else:
        print("⚠️  Warning: Could not detect register type, falling back to CASP")
        register_type = RegisterType.CASP  # Fallback

    # Determine output file
    if args.output:
        output_path = args.output
    else:
        input_path = args.input
        register_name = register_type.value if register_type else "unknown"

        # Check if in raw/ subdir, if so output to cleaned/ subdir
        if "raw" in input_path.parts:
            base_dir = get_base_data_dir() / "cleaned" / register_name
            base_dir.mkdir(parents=True, exist_ok=True)
            output_name = input_path.stem + "_clean" + input_path.suffix
            output_path = base_dir / output_name
        else:
            # Fallback: same dir with _clean suffix
            output_path = input_path.parent / (input_path.stem + "_clean" + input_path.suffix)

        print(f"Auto-detected output path: {output_path}")

    # Create cleaner with register type
    cleaner = CSVCleaner(args.input, register_type=register_type)

    # Load CSV
    if not cleaner.load_csv():
        print("Error: Failed to load CSV file", file=sys.stderr)
        return 1

    # Apply fixes
    try:
        cleaner.fix_all_issues()
    except Exception as e:
        print(f"Error during cleaning: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

    # Generate report
    report = cleaner.generate_report()
    report["output_file"] = str(output_path) if not args.dry_run else "[DRY RUN - not created]"

    # Print summary
    print_summary(report, dry_run=args.dry_run)

    # Save cleaned CSV if not dry run
    if not args.dry_run:
        if not cleaner.save_clean_csv(output_path):
            print(f"Error: Failed to save cleaned CSV to {output_path}", file=sys.stderr)
            return 1
        print(f"\n✅ Cleaned CSV saved to: {output_path}")
    else:
        print("\n🔍 Dry run completed. Use without --dry-run to create cleaned file.")

    # Save report if requested
    # Save cleaning report
    if args.report:
        report_path = args.report
    else:
        # Auto-save to reports/cleaning/
        report_dir = Path("reports/cleaning")
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"cleaning_{args.input.stem}.json"
    
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"📄 Cleaning report saved to: {report_path}")
    except Exception as e:
        print(f"Error saving report: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
