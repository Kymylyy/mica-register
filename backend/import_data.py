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
    
    # Path to CSV file - try multiple locations
    # In Docker container: /app/casp-register.csv
    # In local development: ../casp-register.csv (relative to backend/)
    possible_paths = [
        "/app/casp-register.csv",  # Docker container
        os.path.join(os.path.dirname(__file__), "..", "casp-register.csv"),  # Local dev
        "casp-register.csv",  # Current directory
    ]
    
    csv_path = None
    for path in possible_paths:
        if os.path.exists(path):
            csv_path = path
            break
    
    if not csv_path:
        print(f"Error: CSV file not found. Tried: {possible_paths}")
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