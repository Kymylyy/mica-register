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
from app.models import Entity, Service, PassportCountry

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
    
    # Import data - try cleaned CSV files (import_csv_to_db expects cleaned CSV)
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "..", "data", "cleaned", "CASP20251223_clean.csv"),
        os.path.join(os.path.dirname(__file__), "..", "data", "cleaned", "CASP20251215_clean.csv"),
        os.path.join(os.path.dirname(__file__), "..", "data", "cleaned", "*.csv"),  # Fallback pattern
        os.path.join(os.path.dirname(__file__), "..", "data", "casp-register.csv"),  # Legacy fallback
    ]
    
    csv_path = None
    for path in possible_paths:
        if os.path.exists(path):
            csv_path = path
            break
    
    if not csv_path:
        print(f"   ✗ CSV file not found. Tried: {possible_paths}")
        return False
    
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
