#!/usr/bin/env python3
"""
CLI script to apply remediation patch to CSV file.

Usage:
    python scripts/apply_remediation_patch.py <csv_file> <patch.json> <tasks.json> [--out clean_llm.csv] [--report report.json] [--require-approval] [--auto-apply-low-risk]
"""

import sys
import json
import argparse
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.remediation.patch import PatchApplicator
from app.remediation.schemas import RemediationPatch, RemediationTask


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply remediation patch to CSV file",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "csv_file",
        type=Path,
        help="Path to cleaned CSV file"
    )
    parser.add_argument(
        "patch_file",
        type=Path,
        help="Path to remediation patch JSON file"
    )
    parser.add_argument(
        "tasks_file",
        type=Path,
        help="Path to remediation tasks JSON file (for context)"
    )
    parser.add_argument(
        "--out", "-o",
        type=Path,
        help="Output CSV file (default: {csv_file}_llm.csv)"
    )
    parser.add_argument(
        "--report", "-r",
        type=Path,
        help="Output report JSON file (default: reports/remediation/apply/apply_{csv_name}.json)"
    )
    parser.add_argument(
        "--require-approval",
        action="store_true",
        default=True,
        help="Require manual approval for all changes (default: True)"
    )
    parser.add_argument(
        "--auto-apply-low-risk",
        action="store_true",
        help="Auto-apply low-risk changes with confidence >= 0.9"
    )
    parser.add_argument(
        "--auto-apply-confidence-threshold",
        type=float,
        default=0.9,
        help="Confidence threshold for auto-apply (default: 0.9)"
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.csv_file.exists():
        print(f"Error: CSV file not found: {args.csv_file}", file=sys.stderr)
        return 1
    
    if not args.patch_file.exists():
        print(f"Error: Patch file not found: {args.patch_file}", file=sys.stderr)
        return 1
    
    if not args.tasks_file.exists():
        print(f"Error: Tasks file not found: {args.tasks_file}", file=sys.stderr)
        return 1
    
    # Load patch
    try:
        with open(args.patch_file, 'r', encoding='utf-8') as f:
            patch_data = json.load(f)
        patch = RemediationPatch(**patch_data)
    except Exception as e:
        print(f"Error loading patch: {e}", file=sys.stderr)
        return 1
    
    # Load tasks
    try:
        with open(args.tasks_file, 'r', encoding='utf-8') as f:
            tasks_data = json.load(f)
        tasks = [RemediationTask(**task) for task in tasks_data.get("tasks", [])]
    except Exception as e:
        print(f"Error loading tasks: {e}", file=sys.stderr)
        return 1
    
    # Determine output file
    if args.out:
        output_file = args.out
    else:
        output_file = args.csv_file.parent / f"{args.csv_file.stem}_llm{args.csv_file.suffix}"
    
    # Apply patch
    applicator = PatchApplicator(args.csv_file)
    result = applicator.apply_patch_with_tasks(
        patch=patch,
        tasks=tasks,
        require_approval=args.require_approval,
        auto_apply_confidence_threshold=args.auto_apply_confidence_threshold,
        auto_apply_low_risk=args.auto_apply_low_risk
    )
    
    # Save modified CSV
    if not applicator.save_csv(output_file):
        print(f"Error: Failed to save CSV to {output_file}", file=sys.stderr)
        return 1
    
    # Print summary
    print(f"Patch applied successfully!")
    print(f"  Applied: {result.applied_count}")
    print(f"  Rejected: {result.rejected_count}")
    print(f"  Skipped: {result.skipped_count}")
    if result.errors:
        print(f"  Errors: {len(result.errors)}")
        for error in result.errors:
            print(f"    - {error}")
    
    print(f"\nOutput CSV: {output_file}")
    
    # Determine report path
    if args.report:
        report_path = args.report
    else:
        # Auto-save to reports/remediation/apply/
        report_dir = Path("reports/remediation/apply")
        report_dir.mkdir(parents=True, exist_ok=True)
        csv_name = args.csv_file.stem
        report_path = report_dir / f"apply_{csv_name}.json"
    
    # Save report
    report_data = {
        "patch_id": result.patch_id,
        "applied_at": result.applied_at.isoformat() if hasattr(result.applied_at, 'isoformat') else str(result.applied_at),
        "applied_count": result.applied_count,
        "rejected_count": result.rejected_count,
        "skipped_count": result.skipped_count,
        "applied_changes": result.applied_changes,
        "rejected_changes": result.rejected_changes,
        "errors": result.errors,
        "csv_file": str(args.csv_file),
        "output_file": str(output_file),
        "patch_file": str(args.patch_file),
    }
    
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
        print(f"Report saved to: {report_path}")
    except Exception as e:
        print(f"Error saving report: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

