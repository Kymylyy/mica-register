#!/usr/bin/env python3
"""
Simple test script to verify CSV import works
"""
import sys
from pathlib import Path
import os

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.database import SessionLocal, engine, Base
from app.import_csv import import_csv_to_db
from app.models import Entity, Service, PassportCountry, RegisterType
from app.utils.file_utils import get_latest_csv_for_register, get_base_data_dir

def test_import():
    """Test CSV import"""
    print("=" * 50)
    print("Testing CSV Import")
    print("=" * 50)

    # Create tables
    print("\n1. Creating database tables...")
    Base.metadata.drop_all(bind=engine)  # Drop existing
    Base.metadata.create_all(bind=engine)
    print("   ✓ Tables created")

    # Find latest cleaned CASP CSV using file_utils
    base_dir = get_base_data_dir()
    csv_file = get_latest_csv_for_register(
        RegisterType.CASP,
        base_dir / "cleaned",
        file_stage="cleaned"
    )

    if not csv_file:
        # Fallback to old location
        legacy_path = os.path.join(os.path.dirname(__file__), "..", "data", "casp-register.csv")
        if os.path.exists(legacy_path):
            csv_path = legacy_path
        else:
            print(f"   ✗ No CASP CSV file found")
            return False
    else:
        csv_path = str(csv_file)

    print(f"\n2. Importing data from {csv_path}...")
    db = SessionLocal()
    try:
        import_csv_to_db(db, csv_path)
        print("   ✓ Import completed")
    except Exception as e:
        print(f"   ✗ Import failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()
    
    # Verify data
    print("\n3. Verifying imported data...")
    db = SessionLocal()
    try:
        entity_count = db.query(Entity).count()
        service_count = db.query(Service).count()
        country_count = db.query(PassportCountry).count()
        
        print(f"   Entities: {entity_count}")
        print(f"   Services: {service_count}")
        print(f"   Countries: {country_count}")
        
        if entity_count == 0:
            print("   ✗ No entities imported!")
            return False
        
        # Check first entity
        first_entity = db.query(Entity).first()
        if first_entity:
            print(f"\n4. Sample entity:")
            print(f"   Name: {first_entity.commercial_name}")
            print(f"   LEI: {first_entity.lei}")
            print(f"   Services: {len(first_entity.services)}")
            print(f"   Passport Countries: {len(first_entity.passport_countries)}")
            
            if len(first_entity.services) > 0:
                print(f"   Sample service: {first_entity.services[0].code}")
            if len(first_entity.passport_countries) > 0:
                print(f"   Sample country: {first_entity.passport_countries[0].country_code}")
        
        print("\n" + "=" * 50)
        print("✓ All tests passed!")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"   ✗ Verification failed: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_import()
    sys.exit(0 if success else 1)
