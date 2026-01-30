#!/usr/bin/env python3
"""
Script to import CSV data into the database.
Run this after setting up the database.

Automatically finds the newest *_clean.csv file in data/cleaned/ directory
based on date in filename (YYYYMMDD), not file modification time.

Note: This is a legacy script. For multi-register imports, use import_all_registers.py instead.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import SessionLocal, engine, Base
from app.import_csv import import_csv_to_db
from app.models import RegisterType
from app.utils.file_utils import get_latest_csv_for_register, get_base_data_dir

if __name__ == "__main__":
    # Create database tables first
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

    # Find the newest cleaned CASP CSV file using file_utils
    base_dir = get_base_data_dir() / "cleaned"

    csv_path = get_latest_csv_for_register(
        RegisterType.CASP,
        base_dir,
        file_stage="cleaned",
        prefer_llm=True
    )

    if csv_path:
        csv_path = str(csv_path)
    else:
        # Fallback: try old locations for backward compatibility
        possible_paths = [
            "/app/casp-register.csv",
            os.path.join(os.path.dirname(__file__), "..", "data", "casp-register.csv"),
            os.path.join(os.path.dirname(__file__), "..", "casp-register.csv"),
            "casp-register.csv",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                csv_path = path
                break
    
    if not csv_path:
        print(f"Error: CSV file not found. Checked data/cleaned/ directory for *_clean.csv files and fallback locations.")
        sys.exit(1)
    
    db = SessionLocal()
    try:
        print(f"Importing data from {csv_path}...")
        import_csv_to_db(db, csv_path)
        
        # Get count of imported entities
        from app.models import Entity
        entity_count = db.query(Entity).count()
        print(f"Import completed successfully! Imported {entity_count} entities.")
    except Exception as e:
        print(f"Error during import: {e}")
        db.rollback()
        raise
    finally:
        db.close()