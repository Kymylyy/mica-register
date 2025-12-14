#!/usr/bin/env python3
"""
CLI script for validating ESMA CASP register CSV files.

Usage:
    python scripts/validate_csv.py <path_to_csv> [--report <path_to_json>] [--max-examples N] [--strict]

Exit codes:
    0: no errors and no warnings
    1: no errors but at least one warning
    2: at least one error (or warnings treated as errors with --strict)
"""

import sys
import argparse
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.csv_validate import validate_csv, Severity


def print_summary(report: dict, strict: bool = False) -> None:
    """Print human-readable summary to stdout"""
    stats = report["stats"]
    issues = report["issues"]
    encoding = report["encoding"]

    print("=" * 60)
    print("CSV Validation Report")
    print("=" * 60)
    print(f"Input file: {report['input_file']}")
    print(f"Encoding: {encoding['detected']} (confidence: {encoding['confidence']:.2f})")
    if encoding.get("notes"):
        print(f"Encoding notes: {encoding['notes']}")
    print()
    print(f"Statistics:")
    print(f"  Total rows: {stats['rows_total']}")
    print(f"  Parsed rows: {stats['rows_parsed']}")
    print(f"  Columns: {stats['columns']}")
    print()

    # Count issues by severity
    error_count = sum(1 for issue in issues if issue["severity"] == "ERROR")
    warning_count = sum(1 for issue in issues if issue["severity"] == "WARNING")

    print(f"Issues found:")
    print(f"  Errors: {error_count}")
    print(f"  Warnings: {warning_count}")
    print()

    if issues:
        # Group issues by code
        issues_by_code: dict[str, int] = {}
        for issue in issues:
            code = issue["code"]
            issues_by_code[code] = issues_by_code.get(code, 0) + 1

        # Sort by frequency
        sorted_codes = sorted(issues_by_code.items(), key=lambda x: x[1], reverse=True)

        print("Top issue codes by frequency:")
        for code, count in sorted_codes[:5]:
            print(f"  {code}: {count} occurrence(s)")
        print()

        # Show some example issues
        print("Sample issues:")
        for issue in issues[:5]:
            severity_marker = "❌" if issue["severity"] == "ERROR" else "⚠️"
            print(f"  {severity_marker} [{issue['code']}] {issue['message']}")
            if issue.get("examples"):
                for example in issue["examples"][:2]:
                    print(f"      Example: {example}")
        if len(issues) > 5:
            print(f"  ... and {len(issues) - 5} more issue(s)")
    else:
        print("✅ No issues found - CSV is valid!")

    print("=" * 60)


def determine_exit_code(report: dict, strict: bool = False) -> int:
    """Determine exit code based on issues"""
    issues = report["issues"]
    error_count = sum(1 for issue in issues if issue["severity"] == "ERROR")
    warning_count = sum(1 for issue in issues if issue["severity"] == "WARNING")

    if strict:
        # Treat warnings as errors
        if error_count + warning_count > 0:
            return 2
        return 0
    else:
        if error_count > 0:
            return 2
        if warning_count > 0:
            return 1
        return 0


def main() -> int:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Validate ESMA CASP register CSV file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exit codes:
  0  No errors and no warnings
  1  No errors but at least one warning
  2  At least one error (or warnings treated as errors with --strict)

Examples:
  # Basic validation
  python scripts/validate_csv.py casp-register.csv

  # Save JSON report
  python scripts/validate_csv.py casp-register.csv --report report.json

  # Strict mode (warnings as errors)
  python scripts/validate_csv.py casp-register.csv --strict

  # Limit examples in report
  python scripts/validate_csv.py casp-register.csv --max-examples 3
        """
    )

    parser.add_argument(
        "csv_file",
        type=Path,
        help="Path to CSV file to validate"
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Path to save JSON report (optional)"
    )
    parser.add_argument(
        "--max-examples",
        type=int,
        default=5,
        help="Maximum number of examples per issue in report (default: 5)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors (exit code 2)"
    )

    args = parser.parse_args()

    # Validate input file exists
    if not args.csv_file.exists():
        print(f"Error: File not found: {args.csv_file}", file=sys.stderr)
        return 2

    # Run validation
    try:
        report = validate_csv(args.csv_file, max_examples=args.max_examples)
    except Exception as e:
        print(f"Error during validation: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 2

    # Print human-readable summary
    print_summary(report, strict=args.strict)

    # Save JSON report if requested
    if args.report:
        try:
            with open(args.report, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\nJSON report saved to: {args.report}")
        except Exception as e:
            print(f"Error saving JSON report: {e}", file=sys.stderr)
            return 2

    # Determine and return exit code
    exit_code = determine_exit_code(report, strict=args.strict)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
