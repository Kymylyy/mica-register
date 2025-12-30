#!/usr/bin/env python3
"""
CLI script to generate remediation tasks from validation report.

Usage:
    python scripts/generate_remediation_tasks.py <csv_file> <validation_report.json> [--out tasks.json] [--max-tasks N]
"""

import sys
import json
import argparse
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.remediation.tasks import RemediationTaskGenerator


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate remediation tasks from validation report",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "csv_file",
        type=Path,
        help="Path to cleaned CSV file"
    )
    parser.add_argument(
        "validation_report",
        type=Path,
        help="Path to validation report JSON file"
    )
    parser.add_argument(
        "--out", "-o",
        type=Path,
        help="Output file for tasks (default: reports/remediation/tasks/tasks_{csv_name}.json)"
    )
    parser.add_argument(
        "--max-tasks",
        type=int,
        default=50,
        help="Maximum number of tasks to generate (default: 50)"
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.csv_file.exists():
        print(f"Error: CSV file not found: {args.csv_file}", file=sys.stderr)
        return 1
    
    if not args.validation_report.exists():
        print(f"Error: Validation report not found: {args.validation_report}", file=sys.stderr)
        return 1
    
    # Load validation report
    try:
        with open(args.validation_report, 'r', encoding='utf-8') as f:
            validation_report = json.load(f)
    except Exception as e:
        print(f"Error loading validation report: {e}", file=sys.stderr)
        return 1
    
    # Generate tasks
    generator = RemediationTaskGenerator(args.csv_file)
    tasks = generator.generate_tasks(validation_report, max_tasks=args.max_tasks)
    
    if not tasks:
        print("No remediation tasks generated.")
        return 0
    
    # Determine output path
    if args.out:
        output_path = args.out
    else:
        # Auto-save to reports/remediation/tasks/
        report_dir = Path("reports/remediation/tasks")
        report_dir.mkdir(parents=True, exist_ok=True)
        csv_name = args.csv_file.stem
        output_path = report_dir / f"tasks_{csv_name}.json"
    
    # Save tasks
    tasks_data = {
        "version": 1,
        "generated_at": validation_report.get("generated_at"),
        "csv_file": str(args.csv_file),
        "validation_report": str(args.validation_report),
        "tasks": [task.model_dump() for task in tasks],
        "stats": {
            "total_tasks": len(tasks),
            "by_type": {},
            "by_severity": {"ERROR": 0, "WARNING": 0}
        }
    }
    
    # Calculate stats
    for task in tasks:
        # task_type is already a string (use_enum_values=True)
        task_type = task.task_type if isinstance(task.task_type, str) else task.task_type.value
        tasks_data["stats"]["by_type"][task_type] = tasks_data["stats"]["by_type"].get(task_type, 0) + 1
        # severity is already a string (use_enum_values=True)
        severity = task.severity if isinstance(task.severity, str) else task.severity.value
        tasks_data["stats"]["by_severity"][severity] = tasks_data["stats"]["by_severity"].get(severity, 0) + 1
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(tasks_data, f, indent=2, ensure_ascii=False)
        print(f"Generated {len(tasks)} remediation tasks")
        print(f"Saved to: {output_path}")
        print(f"\nStats:")
        print(f"  By type: {tasks_data['stats']['by_type']}")
        print(f"  By severity: {tasks_data['stats']['by_severity']}")
        return 0
    except Exception as e:
        print(f"Error saving tasks: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

