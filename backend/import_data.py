#!/usr/bin/env python3
"""
Script to import CSV data into the database.
Run this after setting up the database.

Automatically finds the newest *_clean.csv file in data/cleaned/ directory.
"""
import sys
import os
from pathlib import Path
from glob import glob

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import SessionLocal, engine, Base
from app.import_csv import import_csv_to_db

if __name__ == "__main__":
    # Create database tables first
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")
    
    # Find the newest cleaned CSV file automatically
    base_paths = [
        Path("/app/data/cleaned"),  # Docker container
        Path(__file__).parent.parent / "data" / "cleaned",  # Local dev
    ]
    
    csv_path = None
    newest_file = None
    newest_time = 0
    
    for base_path in base_paths:
        if base_path.exists():
            # Find all *_clean.csv files
            pattern = str(base_path / "*_clean.csv")
            for file_path in glob(pattern):
                file_time = os.path.getmtime(file_path)
                if file_time > newest_time:
                    newest_time = file_time
                    newest_file = file_path
    
    if newest_file:
        csv_path = newest_file
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