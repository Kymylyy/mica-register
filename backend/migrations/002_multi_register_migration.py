"""
Migration: Refactor database for multi-register support

This migration transforms the database from single-register (CASP only)
to multi-register architecture supporting all 5 ESMA MiCA registers.

Changes:
1. Add register_type column to entities (default 'casp')
2. Remove global uniqueness on lei, add index on (register_type, lei)
3. Create extension tables for each register type
4. Create new CASP association tables (casp_entity_service, casp_entity_passport_country)
5. Migrate existing CASP data to new structure
6. Remove CASP-specific columns from entities table
7. Drop old association tables (entity_service, entity_passport_country)

IMPORTANT: This migration is DESTRUCTIVE in the final steps.
Ensure you have a backup before running!
"""

from sqlalchemy import create_engine, text, inspect
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_database_url():
    """Get database URL from environment or use default SQLite (same as app)"""
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return database_url
    else:
        # Use same path as backend/app/database.py
        backend_dir = Path(__file__).parent.parent
        return f"sqlite:///{backend_dir / 'database.db'}"


def is_sqlite(engine):
    """Check if engine is SQLite"""
    return engine.dialect.name == 'sqlite'


def is_postgres(engine):
    """Check if engine is PostgreSQL"""
    return engine.dialect.name == 'postgresql'


def column_exists(inspector, table_name, column_name):
    """Check if column exists in table"""
    try:
        columns = inspector.get_columns(table_name)
        return any(col['name'] == column_name for col in columns)
    except:
        return False


def table_exists(inspector, table_name):
    """Check if table exists"""
    return inspector.has_table(table_name)


def run_migration():
    """Run the multi-register migration"""
    database_url = get_database_url()
    engine = create_engine(database_url)
    inspector = inspect(engine)

    logger.info(f"Running multi-register migration on: {database_url}")
    logger.info(f"Database type: {engine.dialect.name}")

    with engine.connect() as conn:
        try:
            # ========================================================================
            # STEP 1: Add register_type column to entities
            # ========================================================================
            logger.info("STEP 1: Adding register_type column to entities...")

            if not column_exists(inspector, 'entities', 'register_type'):
                if is_sqlite(engine):
                    # SQLite: Use VARCHAR (no ENUM support)
                    conn.execute(text("""
                        ALTER TABLE entities ADD COLUMN register_type VARCHAR NOT NULL DEFAULT 'casp'
                    """))
                    conn.commit()
                    logger.info("  ✅ Added register_type column as VARCHAR (SQLite)")
                else:
                    # PostgreSQL: Create ENUM type first, then use it
                    # Check if ENUM type already exists
                    enum_check = conn.execute(text("""
                        SELECT 1 FROM pg_type WHERE typname = 'registertype'
                    """))
                    if not enum_check.fetchone():
                        conn.execute(text("""
                            CREATE TYPE registertype AS ENUM ('casp', 'other', 'art', 'emt', 'ncasp')
                        """))
                        conn.commit()
                        logger.info("  ✅ Created registertype ENUM type (PostgreSQL)")
                    else:
                        logger.info("  ⏭️  registertype ENUM type already exists (PostgreSQL)")

                    # Add column using ENUM type
                    conn.execute(text("""
                        ALTER TABLE entities ADD COLUMN register_type registertype NOT NULL DEFAULT 'casp'
                    """))
                    conn.commit()
                    logger.info("  ✅ Added register_type column as ENUM (PostgreSQL)")

                # Update all existing rows to 'casp'
                conn.execute(text("UPDATE entities SET register_type = 'casp'"))
                conn.commit()
                logger.info("  ✅ Set all existing entities to register_type='casp'")

                # Create index
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_entities_register_type ON entities(register_type)"))
                conn.commit()
                logger.info("  ✅ Created index on register_type")
            else:
                logger.info("  ⏭️  register_type column already exists, skipping")

            # ========================================================================
            # STEP 2: Modify lei uniqueness constraint
            # ========================================================================
            logger.info("STEP 2: Modifying LEI uniqueness constraint...")

            # Make lei nullable first
            if column_exists(inspector, 'entities', 'lei'):
                if is_sqlite(engine):
                    # SQLite: Unique constraint from unique=True cannot be dropped with DROP INDEX
                    # It requires table rebuild (CREATE TABLE ... AS SELECT, then rename)
                    logger.warning("  ⚠️  SQLite detected - unique constraint on 'lei' CANNOT be removed without table rebuild")
                    logger.warning("  ⚠️  This will BLOCK duplicate LEIs between registers in SQLite!")
                    logger.warning("  ⚠️  ")
                    logger.warning("  ⚠️  SOLUTION 1 (Recommended for dev): Delete and recreate database:")
                    logger.warning("  ⚠️    rm backend/database.db")
                    logger.warning("  ⚠️    python backend/migrations/002_multi_register_migration.py")
                    logger.warning("  ⚠️  ")
                    logger.warning("  ⚠️  SOLUTION 2 (Advanced): Manually rebuild entities table in SQLite")
                    logger.warning("  ⚠️  ")
                    logger.warning("  ⚠️  For production, use PostgreSQL which handles this migration correctly.")
                    logger.warning("  ⚠️  ")

                    # Drop the index anyway (won't help with unique constraint, but good for consistency)
                    try:
                        conn.execute(text("DROP INDEX IF EXISTS ix_entities_lei"))
                        conn.commit()
                        logger.info("  ⏭️  Dropped index ix_entities_lei (but unique constraint remains in SQLite)")
                    except Exception as e:
                        logger.warning(f"  ⚠️  Could not drop index: {e}")

                else:
                    # PostgreSQL: Can ALTER COLUMN
                    conn.execute(text("ALTER TABLE entities ALTER COLUMN lei DROP NOT NULL"))
                    conn.commit()
                    logger.info("  ✅ Made lei column nullable (PostgreSQL)")

                    # Drop global unique constraint on lei (if exists)
                    try:
                        conn.execute(text("ALTER TABLE entities DROP CONSTRAINT IF EXISTS entities_lei_key"))
                        conn.commit()
                        logger.info("  ✅ Dropped global unique constraint on lei (PostgreSQL)")
                    except Exception as e:
                        logger.warning(f"  ⚠️  Could not drop unique constraint on lei: {e}")

                # Create new composite index on (register_type, lei)
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_entities_register_lei
                    ON entities(register_type, lei)
                """))
                conn.commit()
                logger.info("  ✅ Created composite index on (register_type, lei)")

                # Recreate simple index on lei (for lookups)
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_entities_lei ON entities(lei)"))
                conn.commit()
                logger.info("  ✅ Recreated simple index on lei")

            # ========================================================================
            # STEP 3: Make common fields nullable
            # ========================================================================
            logger.info("STEP 3: Making common fields nullable...")

            nullable_fields = ['commercial_name', 'address', 'website', 'authorisation_notification_date']

            if is_postgres(engine):
                for field in nullable_fields:
                    try:
                        conn.execute(text(f"ALTER TABLE entities ALTER COLUMN {field} DROP NOT NULL"))
                        conn.commit()
                        logger.info(f"  ✅ Made {field} nullable")
                    except Exception as e:
                        logger.info(f"  ⏭️  {field} already nullable or doesn't exist: {e}")
            else:
                logger.info("  ⏭️  SQLite - nullable handled during table creation")

            # ========================================================================
            # STEP 4: Create extension tables
            # ========================================================================
            logger.info("STEP 4: Creating extension tables...")

            # CaspEntity
            if not table_exists(inspector, 'casp_entities'):
                conn.execute(text("""
                    CREATE TABLE casp_entities (
                        id INTEGER PRIMARY KEY,
                        website_platform VARCHAR,
                        authorisation_end_date DATE,
                        FOREIGN KEY (id) REFERENCES entities(id) ON DELETE CASCADE
                    )
                """))
                conn.commit()
                logger.info("  ✅ Created casp_entities table")
            else:
                logger.info("  ⏭️  casp_entities already exists")

            # OtherEntity
            if not table_exists(inspector, 'other_entities'):
                conn.execute(text("""
                    CREATE TABLE other_entities (
                        id INTEGER PRIMARY KEY,
                        lei_name_casp VARCHAR,
                        lei_casp VARCHAR,
                        offer_countries TEXT,
                        dti_ffg VARCHAR,  -- DTI FFG code (identifier string, NOT boolean) - e.g., '1SL20Z9P1'
                        dti_codes TEXT,
                        white_paper_url VARCHAR,
                        white_paper_comments TEXT,
                        white_paper_last_update DATE,
                        FOREIGN KEY (id) REFERENCES entities(id) ON DELETE CASCADE
                    )
                """))
                conn.commit()
                logger.info("  ✅ Created other_entities table")
            else:
                logger.info("  ⏭️  other_entities already exists")

            # ArtEntity
            if not table_exists(inspector, 'art_entities'):
                conn.execute(text("""
                    CREATE TABLE art_entities (
                        id INTEGER PRIMARY KEY,
                        authorisation_end_date DATE,
                        credit_institution BOOLEAN,
                        white_paper_url VARCHAR,
                        white_paper_notification_date DATE,
                        white_paper_offer_countries TEXT,
                        white_paper_comments TEXT,
                        white_paper_last_update DATE,
                        FOREIGN KEY (id) REFERENCES entities(id) ON DELETE CASCADE
                    )
                """))
                conn.commit()
                logger.info("  ✅ Created art_entities table")
            else:
                logger.info("  ⏭️  art_entities already exists")

            # EmtEntity
            if not table_exists(inspector, 'emt_entities'):
                conn.execute(text("""
                    CREATE TABLE emt_entities (
                        id INTEGER PRIMARY KEY,
                        authorisation_end_date DATE,
                        exemption_48_4 BOOLEAN,
                        exemption_48_5 BOOLEAN,
                        authorisation_other_emt TEXT,
                        dti_ffg VARCHAR,  -- DTI FFG code (identifier string, NOT boolean) - e.g., '13XTMPZT3'
                        dti_codes TEXT,
                        white_paper_url VARCHAR,
                        white_paper_notification_date DATE,
                        white_paper_comments TEXT,
                        white_paper_last_update DATE,
                        FOREIGN KEY (id) REFERENCES entities(id) ON DELETE CASCADE
                    )
                """))
                conn.commit()
                logger.info("  ✅ Created emt_entities table")
            else:
                logger.info("  ⏭️  emt_entities already exists")

            # NcaspEntity
            if not table_exists(inspector, 'ncasp_entities'):
                conn.execute(text("""
                    CREATE TABLE ncasp_entities (
                        id INTEGER PRIMARY KEY,
                        websites TEXT,
                        infringement VARCHAR,
                        reason TEXT,
                        decision_date DATE,
                        FOREIGN KEY (id) REFERENCES entities(id) ON DELETE CASCADE
                    )
                """))
                conn.commit()
                logger.info("  ✅ Created ncasp_entities table")
            else:
                logger.info("  ⏭️  ncasp_entities already exists")

            # ========================================================================
            # STEP 5: Create new CASP association tables
            # ========================================================================
            logger.info("STEP 5: Creating new CASP association tables...")

            if not table_exists(inspector, 'casp_entity_service'):
                conn.execute(text("""
                    CREATE TABLE casp_entity_service (
                        casp_entity_id INTEGER,
                        service_id INTEGER,
                        PRIMARY KEY (casp_entity_id, service_id),
                        FOREIGN KEY (casp_entity_id) REFERENCES casp_entities(id) ON DELETE CASCADE,
                        FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE
                    )
                """))
                conn.commit()
                logger.info("  ✅ Created casp_entity_service table")
            else:
                logger.info("  ⏭️  casp_entity_service already exists")

            if not table_exists(inspector, 'casp_entity_passport_country'):
                conn.execute(text("""
                    CREATE TABLE casp_entity_passport_country (
                        casp_entity_id INTEGER,
                        country_id INTEGER,
                        PRIMARY KEY (casp_entity_id, country_id),
                        FOREIGN KEY (casp_entity_id) REFERENCES casp_entities(id) ON DELETE CASCADE,
                        FOREIGN KEY (country_id) REFERENCES passport_countries(id) ON DELETE CASCADE
                    )
                """))
                conn.commit()
                logger.info("  ✅ Created casp_entity_passport_country table")
            else:
                logger.info("  ⏭️  casp_entity_passport_country already exists")

            # ========================================================================
            # STEP 6: Migrate existing CASP data
            # ========================================================================
            logger.info("STEP 6: Migrating existing CASP data to extension tables...")

            # Check if we have existing entities to migrate
            result = conn.execute(text("SELECT COUNT(*) FROM entities WHERE register_type = 'casp'"))
            casp_count = result.scalar()

            if casp_count > 0:
                logger.info(f"  Found {casp_count} CASP entities to migrate")

                # Check if data already migrated
                result = conn.execute(text("SELECT COUNT(*) FROM casp_entities"))
                existing_casp = result.scalar()

                if existing_casp == 0:
                    # Migrate to casp_entities
                    if column_exists(inspector, 'entities', 'website_platform'):
                        conn.execute(text("""
                            INSERT INTO casp_entities (id, website_platform, authorisation_end_date)
                            SELECT id, website_platform, authorisation_end_date
                            FROM entities
                            WHERE register_type = 'casp'
                        """))
                        conn.commit()
                        logger.info(f"  ✅ Migrated {casp_count} entities to casp_entities")
                    else:
                        # website_platform already removed, create empty casp_entities
                        conn.execute(text("""
                            INSERT INTO casp_entities (id, website_platform, authorisation_end_date)
                            SELECT id, NULL, NULL
                            FROM entities
                            WHERE register_type = 'casp'
                        """))
                        conn.commit()
                        logger.info(f"  ✅ Created {casp_count} casp_entities entries")

                    # Migrate services relationships
                    if table_exists(inspector, 'entity_service'):
                        conn.execute(text("""
                            INSERT INTO casp_entity_service (casp_entity_id, service_id)
                            SELECT entity_id, service_id FROM entity_service
                        """))
                        conn.commit()
                        logger.info("  ✅ Migrated services relationships")

                    # Migrate passport countries relationships
                    if table_exists(inspector, 'entity_passport_country'):
                        conn.execute(text("""
                            INSERT INTO casp_entity_passport_country (casp_entity_id, country_id)
                            SELECT entity_id, country_id FROM entity_passport_country
                        """))
                        conn.commit()
                        logger.info("  ✅ Migrated passport countries relationships")
                else:
                    logger.info(f"  ⏭️  CASP data already migrated ({existing_casp} entries exist)")
            else:
                logger.info("  ⏭️  No CASP entities to migrate")

            # ========================================================================
            # STEP 7: Remove CASP-specific columns from entities (OPTIONAL - can break app)
            # ========================================================================
            logger.info("STEP 7: Removing CASP-specific columns from entities...")
            logger.warning("  ⚠️  SKIPPING column removal to maintain backward compatibility")
            logger.warning("  ⚠️  Columns website_platform and authorisation_end_date will remain in entities table")
            logger.warning("  ⚠️  This allows gradual migration - remove manually after confirming app works")

            # Uncomment below to actually remove columns (DESTRUCTIVE!)
            # if is_postgres(engine):
            #     if column_exists(inspector, 'entities', 'website_platform'):
            #         conn.execute(text("ALTER TABLE entities DROP COLUMN website_platform"))
            #         conn.commit()
            #     if column_exists(inspector, 'entities', 'authorisation_end_date'):
            #         conn.execute(text("ALTER TABLE entities DROP COLUMN authorisation_end_date"))
            #         conn.commit()

            # ========================================================================
            # STEP 8: Drop old association tables (OPTIONAL - can break app)
            # ========================================================================
            logger.info("STEP 8: Dropping old association tables...")
            logger.warning("  ⚠️  SKIPPING drop of old tables to maintain backward compatibility")
            logger.warning("  ⚠️  Tables entity_service and entity_passport_country will remain")
            logger.warning("  ⚠️  Drop manually after confirming app works with new tables")

            # Uncomment below to actually drop tables (DESTRUCTIVE!)
            # conn.execute(text("DROP TABLE IF EXISTS entity_service"))
            # conn.execute(text("DROP TABLE IF EXISTS entity_passport_country"))
            # conn.commit()

            logger.info("=" * 70)
            logger.info("Migration completed successfully!")
            logger.info("=" * 70)
            logger.info("Next steps:")
            logger.info("1. Test the application with new models")
            logger.info("2. Verify CASP data is accessible via casp_entity relationship")
            logger.info("3. Once confirmed working, manually drop old columns/tables:")
            logger.info("   - ALTER TABLE entities DROP COLUMN website_platform;")
            logger.info("   - ALTER TABLE entities DROP COLUMN authorisation_end_date;")
            logger.info("   - DROP TABLE entity_service;")
            logger.info("   - DROP TABLE entity_passport_country;")

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            import traceback
            traceback.print_exc()
            conn.rollback()
            raise


def rollback_migration():
    """Rollback the migration (WARNING: May lose data!)"""
    logger.warning("=" * 70)
    logger.warning("ROLLBACK NOT FULLY IMPLEMENTED")
    logger.warning("To rollback, restore from backup")
    logger.warning("=" * 70)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback_migration()
    else:
        run_migration()
