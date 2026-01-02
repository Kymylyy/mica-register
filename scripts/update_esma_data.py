#!/usr/bin/env python3
"""
Orchestration script to update ESMA data automatically.

This script:
1. Checks if ESMA has updated the register
2. Downloads the latest CSV file
3. Runs validation, cleaning, and optional LLM remediation
4. Prepares files for manual backend import

Usage:
    python scripts/update_esma_data.py
"""
import sys
import subprocess
import json
import os
from pathlib import Path
from datetime import datetime
from glob import glob
from typing import Tuple

# Import functions from check_esma_update.py
sys.path.insert(0, str(Path(__file__).parent))
from check_esma_update import get_esma_update_date, get_latest_csv_date

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


def download_csv(url: str, output_path: Path) -> bool:
    """Download CSV file from URL.
    
    Args:
        url: URL to download from
        output_path: Path to save the file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        import requests
        
        print(f"Downloading CSV from {url}...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✓ Downloaded {len(response.content)} bytes to {output_path}")
        return True
    except ImportError:
        print("Error: requests library not installed. Install with: pip install requests")
        return False
    except Exception as e:
        print(f"Error downloading CSV: {e}")
        return False


def run_script(script_name: str, args: list, description: str) -> Tuple[bool, str]:
    """Run a Python script and return success status and output.
    
    Args:
        script_name: Name of the script (e.g., 'validate_csv.py')
        args: List of arguments to pass
        description: Description of what the script does
        
    Returns:
        Tuple of (success: bool, output: str)
    """
    script_path = Path(__file__).parent / script_name
    if not script_path.exists():
        return False, f"Script not found: {script_path}"
    
    cmd = [sys.executable, str(script_path)] + args
    
    print(f"\n{'='*60}")
    print(f"Step: {description}")
    print(f"Running: {' '.join(cmd)}")
    print('='*60)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        success = result.returncode == 0
        return success, result.stdout + result.stderr
    except Exception as e:
        print(f"Error running script: {e}")
        return False, str(e)


def check_validation_errors(validation_report_path: Path) -> Tuple[int, int]:
    """Check validation report for errors and warnings.
    
    Args:
        validation_report_path: Path to validation report JSON
        
    Returns:
        Tuple of (error_count, warning_count)
    """
    if not validation_report_path.exists():
        return 0, 0
    
    try:
        with open(validation_report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        stats = report.get('stats', {})
        error_count = stats.get('errors', 0)
        warning_count = stats.get('warnings', 0)
        
        return error_count, warning_count
    except Exception as e:
        print(f"Warning: Could not read validation report: {e}")
        return 0, 0


def main():
    """Main orchestration function."""
    print("=" * 60)
    print("ESMA Data Update Orchestration")
    print("=" * 60)
    
    # Step 1: Check for updates
    print("\n[1/7] Checking for ESMA updates...")
    csv_date, csv_file = get_latest_csv_date(quiet=True)
    if not csv_date:
        print("Warning: No existing CSV files found. Will proceed with download.")
    else:
        print(f"Latest CSV file: {csv_file}")
        print(f"CSV file date: {csv_date.strftime('%d %B %Y')}")
    
    esma_date = get_esma_update_date(quiet=False)
    if not esma_date:
        print("\nError: Could not retrieve update date from ESMA website")
        sys.exit(3)
    
    print(f"ESMA last update: {esma_date.strftime('%d %B %Y')}")
    
    # Check if update is needed
    if csv_date and esma_date <= csv_date:
        print(f"\n✓ Your data is up to date!")
        print(f"ESMA date: {esma_date.strftime('%d %B %Y')}")
        print(f"Your CSV date: {csv_date.strftime('%d %B %Y')}")
        sys.exit(2)
    
    if csv_date:
        days_diff = (esma_date - csv_date).days
        print(f"\n⚠️  Update available! ({days_diff} day(s) newer)")
    else:
        print(f"\n⚠️  No existing data found. Will download latest.")
    
    # Generate filename based on ESMA date
    date_str = esma_date.strftime("%Y%m%d")
    raw_filename = f"CASP{date_str}.csv"
    raw_path = Path(__file__).parent.parent / "data" / "raw" / raw_filename
    
    # Step 2: Download CSV
    print(f"\n[2/7] Downloading CSV file...")
    csv_url = "https://www.esma.europa.eu/sites/default/files/2024-12/CASPS.csv"
    
    if raw_path.exists():
        print(f"File already exists: {raw_path}")
        response = input("Overwrite? (y/N): ").strip().lower()
        if response != 'y':
            print("Skipping download.")
        else:
            if not download_csv(csv_url, raw_path):
                print("Error: Failed to download CSV file")
                sys.exit(3)
    else:
        if not download_csv(csv_url, raw_path):
            print("Error: Failed to download CSV file")
            sys.exit(3)
    
    # Step 3: Validate raw file
    print(f"\n[3/7] Validating raw CSV file...")
    success, output = run_script(
        "validate_csv.py",
        [str(raw_path)],
        "Validation of raw CSV file"
    )
    
    if not success:
        print("Warning: Validation found issues, but continuing with cleaning...")
    
    # Find validation report
    validation_raw_report = Path(__file__).parent.parent / "reports" / "validation" / "raw" / f"validation_{raw_path.stem}.json"
    
    # Step 4: Clean CSV
    print(f"\n[4/7] Cleaning CSV file...")
    cleaned_filename = f"CASP{date_str}_clean.csv"
    cleaned_path = Path(__file__).parent.parent / "data" / "cleaned" / cleaned_filename
    
    success, output = run_script(
        "clean_csv.py",
        ["--input", str(raw_path)],
        "Cleaning CSV file"
    )
    
    if not success:
        print("Error: Cleaning failed")
        sys.exit(1)
    
    # Verify cleaned file exists
    if not cleaned_path.exists():
        print(f"Error: Cleaned file not found at {cleaned_path}")
        sys.exit(1)
    
    print(f"✓ Cleaned file saved to: {cleaned_path}")
    
    # Step 5: Validate cleaned file
    print(f"\n[5/7] Validating cleaned CSV file...")
    success, output = run_script(
        "validate_csv.py",
        [str(cleaned_path)],
        "Validation of cleaned CSV file"
    )
    
    # Find validation report
    validation_clean_report = Path(__file__).parent.parent / "reports" / "validation" / "clean" / f"validation_{cleaned_path.stem}.json"
    
    error_count, warning_count = check_validation_errors(validation_clean_report)
    print(f"\nValidation results: {error_count} errors, {warning_count} warnings")
    
    # Step 6: LLM Remediation (if errors exist)
    final_csv_path = cleaned_path
    if error_count > 0:
        print(f"\n[6/7] Running LLM remediation ({error_count} errors found)...")
        
        # Check for API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Warning: GEMINI_API_KEY not set. Skipping LLM remediation.")
            print("Set GEMINI_API_KEY environment variable to enable LLM remediation.")
        else:
            # Generate remediation tasks
            tasks_filename = f"tasks_{cleaned_path.stem}.json"
            tasks_path = Path(__file__).parent.parent / "reports" / "remediation" / "tasks" / tasks_filename
            
            success, output = run_script(
                "generate_remediation_tasks.py",
                [str(cleaned_path), str(validation_clean_report), "--max-tasks", "50"],
                "Generating remediation tasks"
            )
            
            if not success or not tasks_path.exists():
                print("Warning: Failed to generate remediation tasks. Skipping LLM remediation.")
            else:
                # Run LLM remediation
                success, output = run_script(
                    "run_llm_remediation.py",
                    [str(tasks_path)],
                    "Running LLM remediation"
                )
                
                if not success:
                    print("Warning: LLM remediation failed. Continuing with cleaned file.")
                else:
                    # Find the latest patch file
                    patches_dir = Path(__file__).parent.parent / "reports" / "remediation" / "patches"
                    patch_files = sorted(glob(str(patches_dir / "patch_*.json")), reverse=True)
                    
                    if patch_files:
                        patch_path = Path(patch_files[0])
                        llm_filename = f"CASP{date_str}_clean_llm.csv"
                        llm_path = Path(__file__).parent.parent / "data" / "cleaned" / llm_filename
                        
                        # Apply patch (auto-apply low-risk changes)
                        success, output = run_script(
                            "apply_remediation_patch.py",
                            [
                                str(cleaned_path),
                                str(patch_path),
                                str(tasks_path),
                                "--out", str(llm_path),
                                "--auto-apply-low-risk"
                            ],
                            "Applying LLM remediation patch"
                        )
                        
                        if success and llm_path.exists():
                            final_csv_path = llm_path
                            print(f"✓ LLM remediation applied. Final file: {llm_path}")
                            
                            # Validate final file
                            print("\nValidating final LLM-remediated file...")
                            success, output = run_script(
                                "validate_csv.py",
                                [str(llm_path)],
                                "Validation of final LLM-remediated file"
                            )
                            
                            final_error_count, final_warning_count = check_validation_errors(
                                Path(__file__).parent.parent / "reports" / "validation" / "final" / f"validation_{llm_path.stem}.json"
                            )
                            print(f"Final validation: {final_error_count} errors, {final_warning_count} warnings")
                        else:
                            print("Warning: Failed to apply LLM patch. Using cleaned file.")
                    else:
                        print("Warning: No patch file found. Using cleaned file.")
    else:
        print(f"\n[6/7] Skipping LLM remediation (no errors found)")
    
    # Step 7: Summary
    print(f"\n[7/7] Summary")
    print("=" * 60)
    print("✓ Update pipeline completed successfully!")
    print()
    print("Files prepared:")
    print(f"  Raw CSV:     {raw_path}")
    print(f"  Cleaned CSV: {final_csv_path}")
    print()
    print("Next steps:")
    print("  1. Review the cleaned file if needed")
    print("  2. Commit the files to git:")
    print(f"     git add {raw_path} {final_csv_path}")
    # Format date separately to avoid f-string backslash issue
    date_formatted = esma_date.strftime("%d %B %Y")
    print(f"     git commit -m 'Update ESMA data to {date_formatted}'")
    print("  3. Push to GitHub (Railway will auto-deploy):")
    print("     git push")
    print("  4. After deployment, import data to Railway:")
    print("     ./update_production.sh <YOUR_RAILWAY_URL>")
    print()
    print("=" * 60)
    
    sys.exit(0)


if __name__ == "__main__":
    main()

