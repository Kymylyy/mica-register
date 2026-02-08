#!/usr/bin/env python3
"""
Master orchestration script for updating all MiCA registers.

Single command to:
1. Check ESMA for updates
2. Download new CSVs
3. Validate CSVs
4. Clean CSVs
5. Import to database
6. Update frontend date
7. Generate summary report

Usage:
    # Update all registers (full pipeline, non-destructive)
    python scripts/update_all_registers.py --all

    # Update specific registers only
    python scripts/update_all_registers.py --registers casp,art,emt

    # Skip validation/cleaning (use existing cleaned files)
    python scripts/update_all_registers.py --all --skip-validation --skip-cleaning

    # Dry run (show what would happen)
    python scripts/update_all_registers.py --all --dry-run

    # Force redownload even if up to date
    python scripts/update_all_registers.py --all --force

    # Drop entire DB before import (DESTRUCTIVE - use with caution!)
    python scripts/update_all_registers.py --all --drop-db

    # Prefer _clean files over _clean_llm files
    python scripts/update_all_registers.py --all --no-use-clean-llm
"""

import sys
import argparse
import json
import subprocess
from pathlib import Path
from datetime import datetime, date
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, asdict

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.models import RegisterType
from app.config.registers import REGISTER_CSV_URLS, get_register_config
from app.utils.file_utils import (
    get_latest_csv_for_register,
    extract_date_from_filename,
    get_base_data_dir,
    ensure_directory_structure
)


@dataclass
class UpdateResult:
    """Result of updating a single register"""
    register_type: RegisterType
    success: bool = False
    skipped: bool = False
    skip_reason: Optional[str] = None
    steps_completed: List[str] = None
    errors: Dict[str, str] = None
    warnings: List[str] = None
    downloaded_file: Optional[Path] = None
    cleaned_file: Optional[Path] = None
    entities_imported: Optional[int] = None

    def __post_init__(self):
        if self.steps_completed is None:
            self.steps_completed = []
        if self.errors is None:
            self.errors = {}
        if self.warnings is None:
            self.warnings = []

    def complete_step(self, step: str):
        """Mark a step as completed"""
        self.steps_completed.append(step)

    def fail(self, step: str, error: str):
        """Mark a step as failed"""
        self.errors[step] = error

    def warning(self, step: str, message: str):
        """Add a warning"""
        self.warnings.append(f"{step}: {message}")

    def skip(self, reason: str):
        """Mark as skipped"""
        self.skipped = True
        self.skip_reason = reason


EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_ESMA_DATE_UNAVAILABLE = 2


def get_esma_update_date() -> Optional[date]:
    """Get the last update date from ESMA website (scrape from check_esma_update.py).

    Returns:
        date object if found, None otherwise
    """
    try:
        # Import from existing script
        from check_esma_update import get_esma_update_date as _get_date
        result = _get_date()
        # Convert datetime to date if needed
        if result and hasattr(result, 'date'):
            return result.date()
        return result
    except Exception as e:
        print(f"⚠️  Warning: Could not get ESMA update date: {e}")
        return None


def download_csv(url: str, output_path: Path, dry_run: bool = False) -> bool:
    """Download CSV file from URL.

    Args:
        url: URL to download from
        output_path: Path to save the file
        dry_run: If True, only print what would happen

    Returns:
        True if successful, False otherwise
    """
    if dry_run:
        print(f"  [DRY RUN] Would download from {url} to {output_path}")
        return True

    try:
        import requests

        print(f"  Downloading CSV from {url}...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        with open(output_path, 'wb') as f:
            f.write(response.content)

        print(f"  ✓ Downloaded {len(response.content)} bytes to {output_path}")
        return True
    except ImportError:
        print("  ❌ Error: requests library not installed. Install with: pip install requests")
        return False
    except Exception as e:
        print(f"  ❌ Error downloading CSV: {e}")
        return False


def validate_csv(csv_path: Path, dry_run: bool = False) -> Tuple[bool, Optional[dict]]:
    """Validate CSV file using validate_csv.py script.

    Args:
        csv_path: Path to CSV file
        dry_run: If True, only print what would happen

    Returns:
        (success, report_dict) tuple
    """
    if dry_run:
        print(f"  [DRY RUN] Would validate {csv_path}")
        return True, None

    try:
        print(f"  Validating {csv_path.name}...")
        result = subprocess.run(
            [sys.executable, "scripts/validate_csv.py", str(csv_path)],
            capture_output=True,
            text=True,
            timeout=60
        )

        # Exit code 0 = no errors/warnings, 1 = warnings only, 2 = errors
        if result.returncode in [0, 1]:
            print(f"  ✓ Validation passed (exit code: {result.returncode})")
            return True, None
        else:
            print(f"  ⚠️  Validation found issues (exit code: {result.returncode})")
            return False, None

    except Exception as e:
        print(f"  ⚠️  Validation error: {e}")
        return False, None


def clean_csv(input_path: Path, output_path: Path, dry_run: bool = False) -> bool:
    """Clean CSV file using clean_csv.py script.

    Args:
        input_path: Path to raw CSV file
        output_path: Path to save cleaned CSV file
        dry_run: If True, only print what would happen

    Returns:
        True if successful, False otherwise
    """
    if dry_run:
        print(f"  [DRY RUN] Would clean {input_path} to {output_path}")
        return True

    try:
        print(f"  Cleaning {input_path.name}...")

        cmd = [
            sys.executable,
            "scripts/clean_csv.py",
            "--input", str(input_path),
            "--output", str(output_path)
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            print(f"  ✓ Cleaned CSV saved to {output_path}")
            return True
        else:
            print(f"  ❌ Cleaning failed (exit code: {result.returncode})")
            if result.stderr:
                print(f"     Error: {result.stderr[:200]}")
            return False

    except Exception as e:
        print(f"  ❌ Cleaning error: {e}")
        return False


def import_to_db(
    drop_db: bool = False,
    prefer_llm: bool = True,
    dry_run: bool = False
) -> Tuple[bool, Dict[RegisterType, int]]:
    """Import all cleaned CSVs to database using import_all_registers.py.

    Args:
        drop_db: Whether to drop all tables before import
        prefer_llm: Whether to prefer _clean_llm files over _clean files
        dry_run: If True, only print what would happen

    Returns:
        (success, entity_counts) tuple where entity_counts maps RegisterType to count
    """
    if dry_run:
        print(f"  [DRY RUN] Would import to database (drop_db={drop_db})")
        return True, {}

    try:
        print(f"  Importing to database...")

        cmd = [sys.executable, "backend/import_all_registers.py"]
        if drop_db:
            cmd.append("--drop-db")
        if prefer_llm:
            cmd.append("--use-clean-llm")
        else:
            cmd.append("--no-use-clean-llm")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            print(f"  ✓ Database import completed")

            # Parse entity counts from output
            entity_counts = {}
            for line in result.stdout.split('\n'):
                for reg_type in RegisterType:
                    reg_name = reg_type.value.upper()
                    if f"{reg_name}" in line and "entities" in line:
                        try:
                            # Parse line like "CASP     :  147 entities"
                            count_str = line.split(':')[1].strip().split()[0]
                            entity_counts[reg_type] = int(count_str)
                        except:
                            pass

            return True, entity_counts
        else:
            print(f"  ❌ Database import failed (exit code: {result.returncode})")
            if result.stderr:
                print(f"     Error: {result.stderr[:200]}")
            return False, {}

    except Exception as e:
        print(f"  ❌ Import error: {e}")
        return False, {}


def update_frontend_date(update_date: date, dry_run: bool = False) -> bool:
    """Update the last update date in frontend App.jsx.

    Args:
        update_date: Date to set
        dry_run: If True, only print what would happen

    Returns:
        True if successful, False otherwise
    """
    if dry_run:
        print(f"  [DRY RUN] Would update frontend date to {update_date.strftime('%d %B %Y')}")
        return True

    try:
        # Import function from update_esma_data.py
        from update_esma_data import update_frontend_date as update_app_jsx_date

        print(f"  Updating frontend date to {update_date.strftime('%d %B %Y')}...")
        success = update_app_jsx_date(update_date)

        if success:
            print(f"  ✓ Frontend date updated")
        else:
            print(f"  ⚠️  Failed to update frontend date")

        return success

    except Exception as e:
        print(f"  ⚠️  Frontend update error: {e}")
        return False


def update_register(
    register_type: RegisterType,
    esma_date: Optional[date],
    force: bool = False,
    skip_validation: bool = False,
    skip_cleaning: bool = False,
    prefer_llm: bool = True,
    dry_run: bool = False
) -> UpdateResult:
    """Update a single register through the full pipeline.

    Args:
        register_type: Register to update
        force: Force redownload even if up to date
        skip_validation: Skip validation step
        skip_cleaning: Skip cleaning step (use existing cleaned file)
        dry_run: Only show what would happen

    Returns:
        UpdateResult object
    """
    result = UpdateResult(register_type=register_type)
    config = get_register_config(register_type)
    register_name = register_type.value
    prefix = config.csv_prefix
    url = REGISTER_CSV_URLS[register_type]

    print(f"\n{'='*60}")
    print(f"Processing {register_name.upper()} register")
    print(f"{'='*60}")

    # Step 1: Check if update needed
    print("Step 1: Checking for updates...")

    effective_date = esma_date
    if esma_date is None:
        if force:
            effective_date = date.today()
            print("  ⚠️  ESMA update date unavailable, proceeding due to --force")
            print(f"  Using current date for output files: {effective_date.strftime('%d %B %Y')}")
        else:
            result.skip("Could not determine ESMA update date")
            print("  ⚠️  Skipping register update: ESMA update date unavailable")
            return result

    if esma_date:
        print(f"  ESMA last update: {esma_date.strftime('%d %B %Y')}")

    # ESMA date gates filename selection for deterministic runs.
    file_date_str = effective_date.strftime("%Y%m%d")

    # Get latest local raw CSV
    base_dir = get_base_data_dir()
    latest_raw_file = get_latest_csv_for_register(
        register_type,
        base_dir / "raw",
        file_stage="raw",
        prefer_llm=prefer_llm
    )

    if latest_raw_file:
        latest_local_date = extract_date_from_filename(latest_raw_file.name)
        if latest_local_date:
            print(f"  Latest local file: {latest_raw_file.name} ({latest_local_date.strftime('%d %B %Y')})")

            # Check if up to date
            if effective_date and latest_local_date >= effective_date and not force:
                result.skip("Already up to date")
                print(f"  ℹ️  {register_name.upper()} is up to date (use --force to redownload)")
                return result

    # Step 2: Download
    if skip_cleaning and not force:
        # Check if we have a cleaned file already
        latest_cleaned_file = get_latest_csv_for_register(
            register_type,
            base_dir / "cleaned",
            file_stage="cleaned",
            prefer_llm=prefer_llm
        )
        if latest_cleaned_file:
            cleaned_date = extract_date_from_filename(latest_cleaned_file.name)
            if effective_date and cleaned_date:
                if cleaned_date >= effective_date:
                    print("Step 2: Skipping download (existing cleaned file is up to date)")
                    result.cleaned_file = latest_cleaned_file
                    result.complete_step("download")
                    result.complete_step("validate")
                    result.complete_step("clean")
                    result.success = True
                    return result
                print("Step 2: Existing cleaned file is stale, will download and re-clean")
            else:
                print("Step 2: Could not determine cleaned file date, will download and re-clean")

    print("Step 2: Downloading CSV...")

    # Determine output path
    raw_dir = base_dir / "raw" / register_name
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_file = raw_dir / f"{prefix}{file_date_str}.csv"

    if not download_csv(url, raw_file, dry_run=dry_run):
        result.fail("download", "Download failed")
        return result

    result.downloaded_file = raw_file
    result.complete_step("download")

    # Step 3: Validate (optional)
    if not skip_validation:
        print("Step 3: Validating CSV...")
        valid, report = validate_csv(raw_file, dry_run=dry_run)
        if not valid:
            result.warning("validate", "Validation found issues (continuing anyway)")
        else:
            result.complete_step("validate")
    else:
        print("Step 3: Skipping validation (--skip-validation)")

    # Step 4: Clean
    if not skip_cleaning:
        print("Step 4: Cleaning CSV...")
        cleaned_dir = base_dir / "cleaned" / register_name
        cleaned_dir.mkdir(parents=True, exist_ok=True)
        cleaned_file = cleaned_dir / f"{prefix}{file_date_str}_clean.csv"

        if not clean_csv(raw_file, cleaned_file, dry_run=dry_run):
            result.fail("clean", "Cleaning failed")
            return result

        result.cleaned_file = cleaned_file
        result.complete_step("clean")
    else:
        print("Step 4: Skipping cleaning (--skip-cleaning)")
        # Find latest cleaned file
        latest_cleaned_file = get_latest_csv_for_register(
            register_type,
            base_dir / "cleaned",
            file_stage="cleaned",
            prefer_llm=prefer_llm
        )
        if latest_cleaned_file:
            result.cleaned_file = latest_cleaned_file
            print(f"  Using existing cleaned file: {latest_cleaned_file.name}")
        else:
            result.fail("clean", "No cleaned file found and --skip-cleaning specified")
            return result

    result.success = True
    return result


def print_summary(
    results: List[UpdateResult],
    entity_counts: Dict[RegisterType, int],
    dry_run: bool = False
):
    """Print summary of all updates.

    Args:
        results: List of UpdateResult objects
        entity_counts: Dictionary mapping RegisterType to entity count
        dry_run: Whether this was a dry run
    """
    print(f"\n{'='*60}")
    print("UPDATE SUMMARY")
    if dry_run:
        print("(DRY RUN - No actual changes made)")
    print(f"{'='*60}\n")

    successful = [r for r in results if r.success]
    skipped = [r for r in results if r.skipped]
    failed = [r for r in results if not r.success and not r.skipped]

    print(f"Results:")
    print(f"  ✓ Successful: {len(successful)}")
    print(f"  ⊘ Skipped: {len(skipped)}")
    print(f"  ✗ Failed: {len(failed)}")
    print()

    if successful:
        print("Successfully updated registers:")
        for result in successful:
            register_name = result.register_type.value.upper()
            count = entity_counts.get(result.register_type, "?")
            steps = ", ".join(result.steps_completed)
            print(f"  ✓ {register_name}: {count} entities (steps: {steps})")
            if result.warnings:
                for warning in result.warnings:
                    print(f"     ⚠️  {warning}")
        print()

    if skipped:
        print("Skipped registers:")
        for result in skipped:
            register_name = result.register_type.value.upper()
            print(f"  ⊘ {register_name}: {result.skip_reason}")
        print()

    if failed:
        print("Failed registers:")
        for result in failed:
            register_name = result.register_type.value.upper()
            print(f"  ✗ {register_name}:")
            for step, error in result.errors.items():
                print(f"     {step}: {error}")
        print()

    if not dry_run and successful:
        print("Next steps:")
        print("  1. Review the changes above")
        print("  2. Test the application locally")
        print("  3. Commit the changes:")
        print(f"     git add data/ frontend/src/App.jsx")
        print(f"     git commit -m \"Update ESMA data to {datetime.now().strftime('%d %B %Y')}\"")
        print("  4. Push to remote and deploy")
        print()


def save_report(results: List[UpdateResult], entity_counts: Dict[RegisterType, int], output_path: Path):
    """Save detailed report to JSON file.

    Args:
        results: List of UpdateResult objects
        entity_counts: Dictionary mapping RegisterType to entity count
        output_path: Path to save report
    """
    try:
        report = {
            "timestamp": datetime.now().isoformat(),
            "results": [
                {
                    **asdict(r),
                    "register_type": r.register_type.value,
                    "downloaded_file": str(r.downloaded_file) if r.downloaded_file else None,
                    "cleaned_file": str(r.cleaned_file) if r.cleaned_file else None,
                    "entities_imported": entity_counts.get(r.register_type)
                }
                for r in results
            ],
            "summary": {
                "successful": len([r for r in results if r.success]),
                "skipped": len([r for r in results if r.skipped]),
                "failed": len([r for r in results if not r.success and not r.skipped]),
                "total_entities": sum(entity_counts.values())
            }
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"Detailed report saved to: {output_path}")

    except Exception as e:
        print(f"⚠️  Warning: Could not save report: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Master orchestration script for updating all MiCA registers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Update all registers"
    )
    parser.add_argument(
        "--registers",
        type=str,
        help="Comma-separated list of registers to update (e.g., casp,art,emt)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force redownload even if up to date"
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip validation step"
    )
    parser.add_argument(
        "--skip-cleaning",
        action="store_true",
        help="Skip cleaning step (use existing cleaned files)"
    )
    llm_group = parser.add_mutually_exclusive_group()
    llm_group.add_argument(
        "--use-clean-llm",
        dest="use_clean_llm",
        action="store_true",
        help="Prefer _clean_llm files over _clean files"
    )
    llm_group.add_argument(
        "--no-use-clean-llm",
        dest="use_clean_llm",
        action="store_false",
        help="Prefer _clean files over _clean_llm files"
    )
    parser.set_defaults(use_clean_llm=True)
    parser.add_argument(
        "--drop-db",
        action="store_true",
        help="Drop all tables before import (DESTRUCTIVE!)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making changes"
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Path to save detailed JSON report"
    )

    args = parser.parse_args()

    # Determine which registers to update
    if args.all:
        registers_to_update = list(RegisterType)
    elif args.registers:
        register_names = [r.strip().lower() for r in args.registers.split(',')]
        registers_to_update = []
        for name in register_names:
            try:
                registers_to_update.append(RegisterType(name))
            except ValueError:
                print(f"Error: Unknown register type: {name}")
                print(f"Valid types: {', '.join(r.value for r in RegisterType)}")
                return 1
    else:
        print("Error: Must specify --all or --registers")
        parser.print_help()
        return 1

    print("="*60)
    print("MiCA Register Update Orchestration")
    print("="*60)
    print(f"Registers to update: {', '.join(r.value.upper() for r in registers_to_update)}")
    print(f"Force redownload: {args.force}")
    print(f"Skip validation: {args.skip_validation}")
    print(f"Skip cleaning: {args.skip_cleaning}")
    print(f"Prefer _clean_llm: {args.use_clean_llm}")
    print(f"Drop DB before import: {args.drop_db}")
    print(f"Dry run: {args.dry_run}")
    print()

    if args.dry_run:
        print("⚠️  DRY RUN MODE - No actual changes will be made")
        print()

    esma_date = get_esma_update_date()
    if esma_date:
        print(f"ESMA update date: {esma_date.strftime('%d %B %Y')}")
    else:
        print("⚠️  Could not determine ESMA update date")
        if args.force:
            print("⚠️  Continuing because --force is enabled")
        else:
            print("⚠️  Registers will be skipped (use --force to proceed anyway)")

    # Ensure directory structure exists
    ensure_directory_structure()

    # Process each register
    results = []
    for register_type in registers_to_update:
        result = update_register(
            register_type,
            esma_date=esma_date,
            force=args.force,
            skip_validation=args.skip_validation,
            skip_cleaning=args.skip_cleaning,
            prefer_llm=args.use_clean_llm,
            dry_run=args.dry_run
        )
        results.append(result)

    # Import to database (if any succeeded)
    entity_counts = {}
    successful_results = [r for r in results if r.success]
    if successful_results and not args.dry_run:
        print(f"\n{'='*60}")
        print("Step 5: Importing to database")
        print("Note: Import checks all registers; only updated ones have fresh data")
        print(f"{'='*60}")

        import_success, entity_counts = import_to_db(
            drop_db=args.drop_db,
            prefer_llm=args.use_clean_llm,
            dry_run=args.dry_run
        )

        if not import_success:
            print("⚠️  Warning: Database import failed")

        # Update entity counts in results
        for result in results:
            if result.success and result.register_type in entity_counts:
                result.entities_imported = entity_counts[result.register_type]
                result.complete_step("import")

    # Update frontend date (if any succeeded)
    if successful_results and not args.dry_run:
        print(f"\n{'='*60}")
        print("Step 6: Updating frontend date")
        print(f"{'='*60}")

        if esma_date:
            update_frontend_date(esma_date, dry_run=args.dry_run)
        else:
            print("⚠️  Warning: Could not determine ESMA update date, skipping frontend update")

    # Print summary
    print_summary(results, entity_counts, dry_run=args.dry_run)

    # Save detailed report
    if args.report:
        save_report(results, entity_counts, args.report)
    elif not args.dry_run:
        # Auto-save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = Path("reports/updates") / f"update_{timestamp}.json"
        save_report(results, entity_counts, report_path)

    # Return appropriate exit code
    if esma_date is None and not args.force:
        return EXIT_ESMA_DATE_UNAVAILABLE
    if any(not r.success and not r.skipped for r in results):
        return EXIT_FAILURE
    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
