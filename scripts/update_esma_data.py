#!/usr/bin/env python3
"""
Orchestration script to update ESMA MiCA registers automatically.

This script:
1. Checks if ESMA has updated the register(s)
2. Downloads the latest CSV file(s)
3. Runs validation, cleaning, and optional LLM remediation
4. Prepares files for manual backend import

Supports all 5 MiCA registers: CASP, OTHER, ART, EMT, NCASP

Usage:
    python scripts/update_esma_data.py [--register REGISTER] [--all]

    --register REGISTER   Update specific register (casp, other, art, emt, ncasp)
    --all                 Update all registers

Examples:
    python scripts/update_esma_data.py --register casp
    python scripts/update_esma_data.py --all
"""
import sys
import subprocess
import json
import os
import argparse
from pathlib import Path
from datetime import datetime
from glob import glob
from typing import Tuple, List

# Import functions from check_esma_update.py
sys.path.insert(0, str(Path(__file__).parent))
from check_esma_update import get_esma_update_date, get_latest_csv_date

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# Register configuration: name -> (CSV filename prefix, CSV URL)
REGISTER_CONFIG = {
    'casp': ('CASP', 'https://www.esma.europa.eu/sites/default/files/2024-12/CASPS.csv'),
    'other': ('OTHER', 'https://www.esma.europa.eu/sites/default/files/2024-12/OTHER.csv'),
    'art': ('ART', 'https://www.esma.europa.eu/sites/default/files/2024-12/ARTZZ.csv'),
    'emt': ('EMT', 'https://www.esma.europa.eu/sites/default/files/2024-12/EMTWP.csv'),
    'ncasp': ('NCASP', 'https://www.esma.europa.eu/sites/default/files/2024-12/NCASP.csv'),
}


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


def update_frontend_date(esma_date: datetime) -> bool:
    """Update the 'Last updated' date in frontend/src/App.jsx.
    
    Args:
        esma_date: The ESMA update date to use
        
    Returns:
        True if successful, False otherwise
    """
    import re
    
    app_jsx_path = Path(__file__).parent.parent / "frontend" / "src" / "App.jsx"
    
    if not app_jsx_path.exists():
        print(f"Warning: Frontend file not found at {app_jsx_path}")
        return False
    
    try:
        # Read the file
        with open(app_jsx_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Format date as "DD Month YYYY" (e.g., "15 January 2026")
        new_date_str = esma_date.strftime("%d %B %Y")
        
        # Pattern to match: Last updated: DD Month YYYY
        # Matches various formats like:
        #   {' '}• Last updated: 15 January 2026
        #   • Last updated: 15 January 2026
        pattern = r"(Last updated:\s+)(\d{1,2}\s+\w+\s+\d{4})"
        
        # Check if pattern exists
        if not re.search(pattern, content):
            print(f"Warning: Could not find 'Last updated:' pattern in {app_jsx_path}")
            return False
        
        # Replace the date using a lambda function to properly handle the replacement
        def replace_date(match):
            return match.group(1) + new_date_str
        
        new_content = re.sub(pattern, replace_date, content)
        
        # Only write if content changed
        if new_content != content:
            with open(app_jsx_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✓ Updated frontend date to: {new_date_str}")
            return True
        else:
            print(f"Frontend date already set to: {new_date_str}")
            return True
            
    except Exception as e:
        print(f"Error updating frontend date: {e}")
        return False


def process_register(register_name: str, esma_date: datetime, force_download: bool = False) -> bool:
    """Process update for a single register.

    Args:
        register_name: Register name (casp, other, art, emt, ncasp)
        esma_date: ESMA update date
        force_download: Force download even if file exists

    Returns:
        True if successful, False otherwise
    """
    if register_name not in REGISTER_CONFIG:
        print(f"Error: Unknown register '{register_name}'")
        return False

    prefix, url = REGISTER_CONFIG[register_name]

    print("\n" + "=" * 60)
    print(f"Processing {register_name.upper()} Register")
    print("=" * 60)

    # Check latest CSV for this register
    data_dir = Path(__file__).parent.parent / "data" / "raw" / register_name
    csv_pattern = str(data_dir / f"{prefix}*.csv")
    existing_csvs = sorted(glob(csv_pattern), reverse=True)

    csv_date = None
    if existing_csvs:
        latest_csv = Path(existing_csvs[0])
        # Extract date from filename (e.g., CASP20260129.csv)
        import re
        match = re.search(r'(\d{8})', latest_csv.stem)
        if match:
            try:
                csv_date = datetime.strptime(match.group(1), '%Y%m%d')
                print(f"Latest CSV: {latest_csv.name} ({csv_date.strftime('%d %B %Y')})")
            except ValueError:
                pass

    # Check if update needed
    if csv_date and esma_date <= csv_date and not force_download:
        print(f"✓ {register_name.upper()} is up to date!")
        return True

    if csv_date:
        days_diff = (esma_date - csv_date).days
        print(f"⚠️  Update available ({days_diff} day(s) newer)")

    # Generate filename
    date_str = esma_date.strftime("%Y%m%d")
    raw_filename = f"{prefix}{date_str}.csv"
    data_dir.mkdir(parents=True, exist_ok=True)
    raw_path = data_dir / raw_filename

    # Download CSV
    print(f"\nDownloading {register_name.upper()} CSV...")
    if raw_path.exists() and not force_download:
        print(f"File already exists: {raw_path}")
        return True

    if not download_csv(url, raw_path):
        print(f"✗ Failed to download {register_name.upper()} CSV")
        return False

    print(f"✓ {register_name.upper()} register downloaded successfully")
    return True


def main():
    """Main orchestration function."""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Update ESMA MiCA register data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--register', '-r',
                       choices=['casp', 'other', 'art', 'emt', 'ncasp'],
                       help='Update specific register')
    parser.add_argument('--all', '-a', action='store_true',
                       help='Update all registers')
    parser.add_argument('--force', '-f', action='store_true',
                       help='Force download even if file exists')

    args = parser.parse_args()

    # Determine which registers to update
    if args.all:
        registers = list(REGISTER_CONFIG.keys())
    elif args.register:
        registers = [args.register]
    else:
        # Default to CASP for backward compatibility
        registers = ['casp']

    print("=" * 60)
    print("ESMA MiCA Registers Update")
    print("=" * 60)
    print(f"Registers to update: {', '.join(r.upper() for r in registers)}")
    print("=" * 60)

    # Get ESMA update date
    print("\nChecking ESMA update date...")
    esma_date = get_esma_update_date(quiet=False)
    if not esma_date:
        print("\nError: Could not retrieve update date from ESMA website")
        sys.exit(3)

    print(f"ESMA last update: {esma_date.strftime('%d %B %Y')}")

    # Process each register
    success_count = 0
    failed_registers = []

    for register in registers:
        if process_register(register, esma_date, force_download=args.force):
            success_count += 1
        else:
            failed_registers.append(register.upper())

    # Update frontend date if at least one register succeeded
    if success_count > 0:
        print("\n" + "=" * 60)
        print("Updating frontend date...")
        print("=" * 60)
        update_frontend_date(esma_date)

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Successfully updated: {success_count}/{len(registers)} register(s)")

    if failed_registers:
        print(f"Failed: {', '.join(failed_registers)}")

    if success_count > 0:
        print("\n✓ Update completed!")
        print("\nNext steps:")
        print("  1. Review the downloaded files in data/raw/")
        print("  2. Import data to backend:")
        print("     For single register: python backend/app/import_csv.py --register <register>")
        print("     For all registers:   python backend/app/import_csv.py --all")
        print("  3. Commit the files to git:")
        date_formatted = esma_date.strftime("%d %B %Y")
        print(f"     git add data/raw/ frontend/src/App.jsx")
        print(f"     git commit -m 'Update ESMA data to {date_formatted}'")
        print("  4. Push to GitHub:")
        print("     git push")
    else:
        print("\n✗ All updates failed")
        sys.exit(1)

    print("=" * 60)
    sys.exit(0)


if __name__ == "__main__":
    main()

