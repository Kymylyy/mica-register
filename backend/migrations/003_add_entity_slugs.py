"""
Migration: Stable URL slugs

- Adds entities.slug column (nullable, indexed; populated by the next import)
- Creates the entity_slugs registry table (natural identity -> slug), which
  survives register re-imports so public URLs stay stable
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


def column_exists(inspector, table_name, column_name):
    columns = inspector.get_columns(table_name)
    return any(col['name'] == column_name for col in columns)


def run_migration():
    database_url = get_database_url()
    engine = create_engine(database_url)
    inspector = inspect(engine)

    print(f"Running migration on: {database_url}")

    with engine.connect() as conn:
        # 1. entities.slug column
        if not inspector.has_table('entities'):
            print("⚠️  Table entities does not exist, skipping (create_all will handle it)")
        elif column_exists(inspector, 'entities', 'slug'):
            print("✅ Column entities.slug already exists")
        else:
            conn.execute(text("ALTER TABLE entities ADD COLUMN slug VARCHAR"))
            conn.commit()
            print("✅ Added column entities.slug")

        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_entities_slug ON entities(slug)"))
            conn.commit()
            print("✅ Created/verified index ix_entities_slug")
        except Exception as e:
            print(f"❌ Error creating index ix_entities_slug: {e}")
            conn.rollback()

        # 2. entity_slugs registry table
        if inspector.has_table('entity_slugs'):
            print("✅ Table entity_slugs already exists")
        else:
            conn.execute(text("""
                CREATE TABLE entity_slugs (
                    id INTEGER PRIMARY KEY,
                    register_type VARCHAR(10) NOT NULL,
                    identity_key VARCHAR NOT NULL,
                    slug VARCHAR NOT NULL,
                    CONSTRAINT uq_entity_slugs_identity UNIQUE (register_type, identity_key),
                    CONSTRAINT uq_entity_slugs_slug UNIQUE (register_type, slug)
                )
            """) if database_url.startswith('sqlite') else text("""
                CREATE TABLE entity_slugs (
                    id SERIAL PRIMARY KEY,
                    register_type VARCHAR(10) NOT NULL,
                    identity_key VARCHAR NOT NULL,
                    slug VARCHAR NOT NULL,
                    CONSTRAINT uq_entity_slugs_identity UNIQUE (register_type, identity_key),
                    CONSTRAINT uq_entity_slugs_slug UNIQUE (register_type, slug)
                )
            """))
            conn.commit()
            print("✅ Created table entity_slugs")

        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_entity_slugs_register_type ON entity_slugs(register_type)"))
            conn.commit()
            print("✅ Created/verified index ix_entity_slugs_register_type")
        except Exception as e:
            print(f"❌ Error creating index ix_entity_slugs_register_type: {e}")
            conn.rollback()

    print("\nMigration complete")


if __name__ == "__main__":
    run_migration()
