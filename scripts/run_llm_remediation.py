#!/usr/bin/env python3
"""
CLI script to run LLM remediation using Gemini API.

Usage:
    python scripts/run_llm_remediation.py <tasks.json> [--out patch.json] [--api-key KEY]
"""

import sys
import json
import argparse
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.remediation.llm_client import GeminiLLMClient
from app.remediation.schemas import RemediationTask


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run LLM remediation using Gemini API",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "tasks_file",
        type=Path,
        help="Path to remediation tasks JSON file"
    )
    parser.add_argument(
        "--out", "-o",
        type=Path,
        help="Output file for patch (default: reports/remediation/patches/patch_{timestamp}.json)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="Gemini API key (default: from GEMINI_API_KEY env var)"
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.tasks_file.exists():
        print(f"Error: Tasks file not found: {args.tasks_file}", file=sys.stderr)
        return 1
    
    # Load tasks
    try:
        with open(args.tasks_file, 'r', encoding='utf-8') as f:
            tasks_data = json.load(f)
    except Exception as e:
        print(f"Error loading tasks: {e}", file=sys.stderr)
        return 1
    
    tasks_list = tasks_data.get("tasks", [])
    if not tasks_list:
        print("No tasks found in file.", file=sys.stderr)
        return 1
    
    # Parse tasks
    tasks = [RemediationTask(**task) for task in tasks_list]
    
    print(f"Processing {len(tasks)} tasks with Gemini API...")
    
    # Initialize client
    api_key = args.api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: API key not provided. Use --api-key or set GEMINI_API_KEY env var.", file=sys.stderr)
        return 1
    
    client = GeminiLLMClient(api_key=api_key)
    
    # Generate patch
    try:
        patch = client.generate_patch(tasks)
        print(f"Generated patch with {len(patch.tasks)} proposals")
        print(f"Model used: {patch.model_name}")
    except Exception as e:
        print(f"Error generating patch: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    
    # Determine output path
    if args.out:
        output_path = args.out
    else:
        # Auto-save to reports/remediation/patches/
        report_dir = Path("reports/remediation/patches")
        report_dir.mkdir(parents=True, exist_ok=True)
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = report_dir / f"patch_{timestamp}.json"
    
    # Save patch
    patch_data = patch.model_dump()
    patch_data["tasks_file"] = str(args.tasks_file)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(patch_data, f, indent=2, ensure_ascii=False, default=str)
        print(f"Patch saved to: {output_path}")
        print(f"\nStats:")
        print(f"  Model used: {patch.model_name}")
        print(f"  Proposals generated: {len(patch.tasks)}")
        print(f"  Tasks processed: {patch.metadata.get('tasks_processed', 0)}")
        print(f"  Tasks total: {patch.metadata.get('tasks_total', 0)}")
        return 0
    except Exception as e:
        print(f"Error saving patch: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

