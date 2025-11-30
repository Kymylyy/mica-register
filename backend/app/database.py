from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path

# Database configuration
# Use PostgreSQL if DATABASE_URL is set, otherwise fallback to SQLite for local development
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # PostgreSQL connection
    # DATABASE_URL format: postgresql://user:password@host:port/database
    # For production, this will be set by the hosting platform
    engine = create_engine(
        DATABASE_URL,
        echo=False
    )
else:
    # SQLite fallback for local development
    backend_dir = Path(__file__).parent.parent
    sqlite_url = f"sqlite:///{backend_dir / 'database.db'}"
    engine = create_engine(
        sqlite_url,
        connect_args={"check_same_thread": False},
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

