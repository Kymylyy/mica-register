#!/usr/bin/env python3
"""
Test script to clean and import CASP data, then verify functionality.
"""
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.csv_clean import CSVCleaner
from app.import_csv import import_csv_to_db
from app.database import SessionLocal, engine, Base
from app.models import Entity, RegisterType
from app.config.registers import get_register_config
from app.utils.file_utils import get_latest_csv_for_register, get_base_data_dir

def clean_csv():
    """Clean the newest raw CASP CSV"""
    # Find newest raw CSV using file_utils
    base_dir = get_base_data_dir()
    newest_csv = get_latest_csv_for_register(
        RegisterType.CASP,
        base_dir / "raw",
        file_stage="raw"
    )

    if not newest_csv:
        print("Error: No CASP CSV files found in data/raw/")
        return None

    print(f"\n1. Cleaning CSV: {newest_csv.name}")

    # Clean CSV
    cleaner = CSVCleaner(newest_csv, RegisterType.CASP)
    if not cleaner.load_csv():
        print("Error: Failed to load CSV")
        return None

    cleaner.fix_all_issues()

    # Save cleaned CSV to proper subdirectory
    cleaned_dir = base_dir / "cleaned" / "casp"
    cleaned_dir.mkdir(parents=True, exist_ok=True)

    cleaned_path = cleaned_dir / f"{newest_csv.stem}_clean.csv"
    if cleaner.save_clean_csv(cleaned_path):
        print(f"✓ Cleaned CSV saved to: {cleaned_path}")
        print(f"  Changes made: {len(cleaner.changes)}")
        print(f"  Rows: {cleaner.rows_before} → {cleaner.rows_after}")
        return cleaned_path
    else:
        print("Error: Failed to save cleaned CSV")
        return None

def import_data(cleaned_path):
    """Import cleaned CSV into database"""
    print(f"\n2. Importing data from: {cleaned_path.name}")

    # Create tables
    print("  Creating tables...")
    Base.metadata.create_all(bind=engine)

    # Import data
    db = SessionLocal()
    try:
        import_csv_to_db(db, str(cleaned_path), RegisterType.CASP)

        # Get count
        entity_count = db.query(Entity).filter(Entity.register_type == RegisterType.CASP).count()
        print(f"✓ Import completed! {entity_count} CASP entities imported.")
        return entity_count
    except Exception as e:
        print(f"✗ Error during import: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def verify_data():
    """Verify imported data"""
    print(f"\n3. Verifying imported data...")

    db = SessionLocal()
    try:
        # Check entities
        entities = db.query(Entity).filter(Entity.register_type == RegisterType.CASP).limit(5).all()

        if not entities:
            print("✗ No CASP entities found!")
            return False

        print(f"✓ Found {len(entities)} entities (showing first 5):")

        for entity in entities:
            print(f"\n  Entity ID: {entity.id}")
            print(f"    LEI: {entity.lei}")
            print(f"    Name: {entity.commercial_name or entity.lei_name}")
            print(f"    Country: {entity.home_member_state}")

            # Check legacy relationships (for backward compatibility)
            print(f"    Services (legacy): {len(entity.services)}")
            print(f"    Passport countries (legacy): {len(entity.passport_countries)}")

            # Check new relationships (via casp_entity)
            if entity.casp_entity:
                print(f"    Services (new): {len(entity.casp_entity.services)}")
                print(f"    Passport countries (new): {len(entity.casp_entity.passport_countries)}")
            else:
                print(f"    ✗ No casp_entity found!")

        return True

    except Exception as e:
        print(f"✗ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("CASP Functionality Test")
    print("=" * 60)

    try:
        # Step 1: Clean CSV
        cleaned_path = clean_csv()
        if not cleaned_path:
            sys.exit(1)

        # Step 2: Import data
        entity_count = import_data(cleaned_path)
        if entity_count == 0:
            print("\n✗ No entities imported!")
            sys.exit(1)

        # Step 3: Verify data
        if verify_data():
            print("\n" + "=" * 60)
            print("✓ CASP functionality test PASSED!")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("✗ CASP functionality test FAILED!")
            print("=" * 60)
            sys.exit(1)

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
