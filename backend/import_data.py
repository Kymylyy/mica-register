#!/usr/bin/env python3
"""
Script to import CSV data into the database.
Run this after setting up the database.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import SessionLocal, engine, Base
from app.import_csv import import_csv_to_db

if __name__ == "__main__":
    # Create database tables first
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")
    
    # Path to CSV file (relative to backend directory)
    csv_path = os.path.join(os.path.dirname(__file__), "..", "casp-register.csv")
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        sys.exit(1)
    
    db = SessionLocal()
    try:
        print(f"Importing data from {csv_path}...")
        import_csv_to_db(db, csv_path)
        print("Import completed successfully!")
    except Exception as e:
        print(f"Error during import: {e}")
        db.rollback()
        raise
    finally:
        db.close()