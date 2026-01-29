"""
Migration: Add performance indexes for ETAP 0.5

This migration adds critical indexes to improve query performance:
- Ensures indexes exist on entities table for common filter fields
- Adds index on entity_service.entity_id for faster join operations
"""

from sqlalchemy import create_engine, text, inspect
import os
from pathlib import Path


def get_database_url():
    """Get database URL from environment or use default SQLite (same as app)"""
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return database_url
    else:
        # Use same path as backend/app/database.py
        backend_dir = Path(__file__).parent.parent
        return f"sqlite:///{backend_dir / 'database.db'}"


def index_exists(inspector, table_name, index_name):
    """Check if index exists on table"""
    indexes = inspector.get_indexes(table_name)
    return any(idx['name'] == index_name for idx in indexes)


def run_migration():
    """Run the migration to add performance indexes"""
    database_url = get_database_url()
    engine = create_engine(database_url)
    inspector = inspect(engine)

    print(f"Running migration on: {database_url}")

    with engine.connect() as conn:
        # List of indexes to ensure exist
        indexes_to_create = [
            # Entities table indexes (some may already exist from model definitions)
            ("entities", "ix_entities_home_member_state", "CREATE INDEX IF NOT EXISTS ix_entities_home_member_state ON entities(home_member_state)"),
            ("entities", "ix_entities_auth_date", "CREATE INDEX IF NOT EXISTS ix_entities_auth_date ON entities(authorisation_notification_date)"),
            ("entities", "ix_entities_commercial_name", "CREATE INDEX IF NOT EXISTS ix_entities_commercial_name ON entities(commercial_name)"),
            ("entities", "ix_entities_competent_authority", "CREATE INDEX IF NOT EXISTS ix_entities_competent_authority ON entities(competent_authority)"),
            ("entities", "ix_entities_lei", "CREATE INDEX IF NOT EXISTS ix_entities_lei ON entities(lei)"),

            # Association table index - CRITICAL for join performance
            ("entity_service", "ix_entity_service_entity_id", "CREATE INDEX IF NOT EXISTS ix_entity_service_entity_id ON entity_service(entity_id)"),
            ("entity_service", "ix_entity_service_service_id", "CREATE INDEX IF NOT EXISTS ix_entity_service_service_id ON entity_service(service_id)"),

            # Passport country association table
            ("entity_passport_country", "ix_entity_passport_country_entity_id", "CREATE INDEX IF NOT EXISTS ix_entity_passport_country_entity_id ON entity_passport_country(entity_id)"),
            ("entity_passport_country", "ix_entity_passport_country_country_id", "CREATE INDEX IF NOT EXISTS ix_entity_passport_country_country_id ON entity_passport_country(country_id)"),
        ]

        created_count = 0
        skipped_count = 0

        for table_name, index_name, sql in indexes_to_create:
            # Check if table exists
            if not inspector.has_table(table_name):
                print(f"⚠️  Table {table_name} does not exist, skipping index {index_name}")
                skipped_count += 1
                continue

            try:
                # Use CREATE INDEX IF NOT EXISTS (works for SQLite and PostgreSQL)
                conn.execute(text(sql))
                conn.commit()
                print(f"✅ Created/verified index: {index_name} on {table_name}")
                created_count += 1
            except Exception as e:
                print(f"❌ Error creating index {index_name}: {e}")
                conn.rollback()

        print(f"\nMigration complete: {created_count} indexes created/verified, {skipped_count} skipped")


def rollback_migration():
    """Rollback migration (not recommended - indexes improve performance)"""
    database_url = get_database_url()
    engine = create_engine(database_url)

    print(f"Rolling back migration on: {database_url}")
    print("⚠️  WARNING: Removing indexes will degrade performance!")

    # Note: We don't actually drop indexes here as it would hurt performance
    # This is just for documentation purposes
    print("Rollback not implemented - keeping indexes for performance")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback_migration()
    else:
        run_migration()
