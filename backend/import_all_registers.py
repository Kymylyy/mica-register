#!/usr/bin/env python3
"""
Import all MiCA registers (CASP, ART, EMT, NCASP, OTHER) into database.
"""
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import SessionLocal, engine, Base
from app.import_csv import import_csv_to_db
from app.models import RegisterType
from app.utils.file_utils import get_latest_csv_for_register, get_base_data_dir

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import all MiCA registers")
    parser.add_argument("--drop-db", action="store_true",
                       help="Drop all tables before import (DESTRUCTIVE!)")
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
    args = parser.parse_args()

    if args.drop_db:
        print("⚠️  WARNING: Dropping all existing tables...")
        Base.metadata.drop_all(bind=engine)
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully!\n")
    else:
        print("Creating database tables (if not exist)...")
        Base.metadata.create_all(bind=engine)
        print("ℹ️  Existing data will be replaced per-register (not dropped globally)\n")

    # Support both local and Docker paths
    base_dir = get_base_data_dir() / "cleaned"

    # Auto-detect latest cleaned CSV for each register
    register_files = {}
    print(f"File preference: {'_clean_llm' if args.use_clean_llm else '_clean'}")
    for register_type in RegisterType:
        latest_file = get_latest_csv_for_register(
            register_type,
            base_dir,
            file_stage="cleaned",
            prefer_llm=args.use_clean_llm
        )
        if latest_file:
            register_files[register_type] = latest_file
        else:
            print(f"⚠️  Warning: No cleaned CSV found for {register_type.value.upper()}")

    db = SessionLocal()
    try:
        for register_type, csv_path in register_files.items():
            if not csv_path.exists():
                print(f"⚠ Warning: {csv_path} not found, skipping {register_type.value.upper()}")
                continue

            print(f"\n{'='*60}")
            print(f"Importing {register_type.value.upper()} register...")
            print(f"{'='*60}")
            import_csv_to_db(db, str(csv_path), register_type)

        # Get count of imported entities per register
        from app.models import Entity
        print(f"\n{'='*60}")
        print("Import Summary:")
        print(f"{'='*60}")
        for register_type in RegisterType:
            count = db.query(Entity).filter(Entity.register_type == register_type).count()
            print(f"{register_type.value.upper():8} : {count:4} entities")

        total = db.query(Entity).count()
        print(f"{'='*60}")
        print(f"TOTAL   : {total:4} entities")
        print(f"{'='*60}")
        print("\n✓ All registers imported successfully!")

    except Exception as e:
        print(f"\n✗ Error during import: {e}")
        db.rollback()
        raise
    finally:
        db.close()
