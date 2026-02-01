"""
File utilities for MiCA register CSV management.

Provides:
- Auto-detection of latest CSV files for all 5 registers
- Support for both local (data/) and Docker (/app/data/) paths
- Priority handling for _clean_llm vs _clean files
- Directory structure management
- Legacy file migration
"""

from pathlib import Path
from datetime import date
from typing import Optional
import re
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import RegisterType (handle both direct run and module import)
try:
    from app.models import RegisterType
except ImportError:
    from models import RegisterType


def extract_date_from_filename(filename: str) -> Optional[date]:
    """
    Extract YYYYMMDD date from CSV filename.

    Examples:
        CASP20260130.csv → date(2026, 1, 30)
        ART20260129_clean.csv → date(2026, 1, 29)
        EMT20260130_clean_llm.csv → date(2026, 1, 30)
        CASPS-tests.csv → None (test file, no date)

    Args:
        filename: CSV filename to parse

    Returns:
        date object if valid YYYYMMDD found, None otherwise
    """
    # Match pattern: PREFIX + YYYYMMDD + optional suffix
    # Must have exactly 8 digits after prefix
    pattern = r'([A-Z]+)(\d{8})(?:_clean)?(?:_llm)?\.csv'
    match = re.match(pattern, filename, re.IGNORECASE)

    if not match:
        return None

    date_str = match.group(2)

    try:
        year = int(date_str[0:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        return date(year, month, day)
    except (ValueError, IndexError):
        return None


def get_base_data_dir() -> Path:
    """
    Detect base data directory based on environment.

    Returns:
        Path to data directory:
        - /app/data if running in Docker
        - {project_root}/data if running locally
    """
    # Check if running in Docker
    docker_data_dir = Path("/app/data")
    if docker_data_dir.exists():
        return docker_data_dir

    # Local environment: find project root
    # Start from this file's location and walk up
    current = Path(__file__).resolve()

    # Walk up to find directory containing both 'backend' and 'data'
    for parent in [current] + list(current.parents):
        if (parent / "backend").exists() and (parent / "data").exists():
            return parent / "data"

    # Fallback: assume we're in backend/app/utils, so ../../../data
    return (Path(__file__).parent.parent.parent.parent / "data").resolve()


def normalize_base_path(path: Path) -> Path:
    """
    Resolve path variations between local and Docker environments.

    Args:
        path: Path to normalize

    Returns:
        Resolved absolute path
    """
    return path.resolve()


def is_test_file(filename: str) -> bool:
    """
    Check if filename is a test file (should be ignored).

    Test patterns:
        - *-tests.csv
        - *-tests_clean.csv
        - *-test.csv
        - *-test_clean.csv

    Args:
        filename: Filename to check

    Returns:
        True if test file, False otherwise
    """
    filename_lower = filename.lower()
    return ('-test' in filename_lower or filename_lower.startswith('test'))


def get_latest_csv_for_register(
    register_type: RegisterType,
    base_dir: Path,
    file_stage: str = "raw",
    prefer_llm: bool = True
) -> Optional[Path]:
    """
    Find newest CSV by date for any register.

    Search priority:
    1. base_dir/{register_name}/{PREFIX}{YYYYMMDD}_clean_llm.csv (if cleaned + prefer_llm)
    2. base_dir/{register_name}/{PREFIX}{YYYYMMDD}_clean.csv (if cleaned)
    3. base_dir/{register_name}/{PREFIX}{YYYYMMDD}.csv (if raw)
    4. base_dir/{PREFIX}{YYYYMMDD}_clean_llm.csv (backward compat, root)
    5. base_dir/{PREFIX}{YYYYMMDD}_clean.csv (backward compat, root)
    6. base_dir/{PREFIX}{YYYYMMDD}.csv (backward compat, root)

    For cleaned files with same date:
    - If prefer_llm=True: prefer _clean_llm over _clean
    - If prefer_llm=False: prefer _clean over _clean_llm

    For different dates:
    - Always prefer newest date regardless of suffix

    Ignores test files (e.g., CASPS-tests.csv, *-tests_clean.csv).

    Args:
        register_type: Register type to search for
        base_dir: Base directory to search in (e.g., data/raw or data/cleaned)
        file_stage: "raw" or "cleaned"
        prefer_llm: Whether to prefer _clean_llm over _clean for same date

    Returns:
        Path to newest file, or None if not found
    """
    # Import here to avoid circular dependency
    try:
        from app.config.registers import get_register_config
    except ImportError:
        from config.registers import get_register_config

    config = get_register_config(register_type)
    prefix = config.csv_prefix
    register_name = register_type.value

    # Normalize base directory
    base_dir = normalize_base_path(base_dir)

    # Build search patterns based on file_stage
    if file_stage == "cleaned":
        patterns = [
            f"{prefix}*_clean_llm.csv",
            f"{prefix}*_clean.csv",
        ]
    else:  # raw
        patterns = [
            f"{prefix}*.csv",
        ]

    # Search locations: subdirectory first, then root (backward compat)
    search_dirs = [
        base_dir / register_name,  # Preferred: data/raw/casp/
        base_dir,                   # Fallback: data/raw/
    ]

    candidates = []

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue

        for pattern in patterns:
            for file_path in search_dir.glob(pattern):
                # Skip test files
                if is_test_file(file_path.name):
                    continue

                # Extract date
                file_date = extract_date_from_filename(file_path.name)
                if file_date is None:
                    continue

                # Determine if this is an LLM-cleaned file
                is_llm = '_clean_llm' in file_path.name

                candidates.append((file_date, is_llm, file_path))

    if not candidates:
        return None

    # Sort by:
    # 1. Date (descending - newest first)
    # 2. LLM preference (if prefer_llm=True, LLM files first; otherwise regular first)
    # 3. Path length (prefer subdirectory over root)
    candidates.sort(
        key=lambda x: (
            x[0],  # Date (newest first when reversed)
            x[1] if prefer_llm else not x[1],  # LLM preference
            len(str(x[2]))  # Longer path = deeper in structure
        ),
        reverse=True
    )

    return candidates[0][2]


def ensure_directory_structure(base_dir: Optional[Path] = None) -> None:
    """
    Create standardized directory structure for all registers.

    Creates:
        data/raw/{register_name}/
        data/cleaned/{register_name}/

    for all 5 registers (casp, art, emt, ncasp, other).

    Args:
        base_dir: Base data directory (default: auto-detect)
    """
    if base_dir is None:
        base_dir = get_base_data_dir()

    base_dir = normalize_base_path(base_dir)

    for register_type in RegisterType:
        register_name = register_type.value

        # Create subdirectories
        (base_dir / "raw" / register_name).mkdir(parents=True, exist_ok=True)
        (base_dir / "cleaned" / register_name).mkdir(parents=True, exist_ok=True)


def migrate_legacy_files(base_dir: Optional[Path] = None, dry_run: bool = False) -> dict:
    """
    Move legacy CSV files from root to register subdirectories.

    Moves:
        data/raw/CASP20260130.csv → data/raw/casp/CASP20260130.csv
        data/cleaned/CASP20260130_clean.csv → data/cleaned/casp/CASP20260130_clean.csv

    Ignores test files (CASPS-tests.csv, etc.).

    Args:
        base_dir: Base data directory (default: auto-detect)
        dry_run: If True, only print what would be moved without moving

    Returns:
        Dictionary with migration results:
        {
            'moved': [(src, dest), ...],
            'skipped': [(path, reason), ...],
            'errors': [(path, error), ...]
        }
    """
    if base_dir is None:
        base_dir = get_base_data_dir()

    base_dir = normalize_base_path(base_dir)

    # Import here to avoid circular dependency
    try:
        from app.config.registers import get_register_config
    except ImportError:
        from config.registers import get_register_config

    results = {
        'moved': [],
        'skipped': [],
        'errors': []
    }

    # Check both raw and cleaned directories
    for stage in ['raw', 'cleaned']:
        stage_dir = base_dir / stage

        if not stage_dir.exists():
            continue

        # Find CSV files in root of stage directory
        for csv_file in stage_dir.glob("*.csv"):
            # Skip if already in a subdirectory
            if csv_file.parent != stage_dir:
                continue

            # Skip test files
            if is_test_file(csv_file.name):
                results['skipped'].append((csv_file, "test file"))
                continue

            # Try to detect register type
            detected_register = None
            for register_type in RegisterType:
                config = get_register_config(register_type)
                if csv_file.name.upper().startswith(config.csv_prefix):
                    detected_register = register_type
                    break

            if detected_register is None:
                results['skipped'].append((csv_file, "unknown register type"))
                continue

            # Determine destination
            register_name = detected_register.value
            dest_dir = stage_dir / register_name
            dest_file = dest_dir / csv_file.name

            # Skip if destination already exists
            if dest_file.exists():
                results['skipped'].append((csv_file, "destination exists"))
                continue

            # Move file
            try:
                if dry_run:
                    results['moved'].append((csv_file, dest_file))
                else:
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    csv_file.rename(dest_file)
                    results['moved'].append((csv_file, dest_file))
            except Exception as e:
                results['errors'].append((csv_file, str(e)))

    return results


if __name__ == "__main__":
    # Quick test
    print("Testing file_utils...")

    # Test base dir detection
    base_dir = get_base_data_dir()
    print(f"Base data directory: {base_dir}")

    # Test date extraction
    test_filenames = [
        "CASP20260130.csv",
        "ART20260129_clean.csv",
        "EMT20260130_clean_llm.csv",
        "CASPS-tests.csv",
        "invalid.csv"
    ]

    print("\nDate extraction tests:")
    for filename in test_filenames:
        extracted = extract_date_from_filename(filename)
        print(f"  {filename} → {extracted}")

    # Test file detection for each register
    print("\nLatest file detection (cleaned):")
    for register_type in RegisterType:
        latest = get_latest_csv_for_register(
            register_type,
            base_dir / "cleaned",
            file_stage="cleaned",
            prefer_llm=True
        )
        print(f"  {register_type.value.upper()}: {latest}")

    print("\nDone!")
