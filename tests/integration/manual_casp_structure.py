#!/usr/bin/env python3
"""
Test script to verify CASP structure after refactoring (without importing data).
"""
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

def test_imports():
    """Test that all modules import correctly"""
    print("\n1. Testing imports...")
    try:
        from app.models import Entity, CaspEntity, Service, PassportCountry, RegisterType
        from app.config.registers import get_register_config, RegisterType as ConfigRegisterType
        from app.schemas import EntityBase, Entity as EntitySchema
        from app.routers import entities
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_schema():
    """Test database schema"""
    print("\n2. Testing database schema...")
    try:
        from app.database import engine
        from sqlalchemy import inspect

        inspector = inspect(engine)
        tables = inspector.get_table_names()

        required_tables = [
            'entities',
            'casp_entities',
            'casp_entity_service',
            'casp_entity_passport_country',
            'services',
            'passport_countries',
            'entity_service',  # Legacy
            'entity_passport_country',  # Legacy
        ]

        missing = [t for t in required_tables if t not in tables]

        if missing:
            print(f"  ✗ Missing tables: {missing}")
            return False

        print(f"  ✓ All required tables exist ({len(required_tables)} tables)")

        # Check entities table has register_type column
        columns = [col['name'] for col in inspector.get_columns('entities')]
        if 'register_type' not in columns:
            print("  ✗ entities table missing register_type column")
            return False

        print("  ✓ entities table has register_type column")

        # Check casp_entities table structure
        casp_columns = [col['name'] for col in inspector.get_columns('casp_entities')]
        expected_casp_cols = ['id', 'website_platform', 'authorisation_end_date']

        for col in expected_casp_cols:
            if col not in casp_columns:
                print(f"  ✗ casp_entities missing column: {col}")
                return False

        print(f"  ✓ casp_entities table has correct structure")

        return True

    except Exception as e:
        print(f"  ✗ Database schema error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_register_config():
    """Test register configuration"""
    print("\n3. Testing register configuration...")
    try:
        from app.config.registers import get_register_config, RegisterType

        config = get_register_config(RegisterType.CASP)

        # Check required fields
        assert hasattr(config, 'register_type')
        assert hasattr(config, 'csv_url')
        assert hasattr(config, 'column_mapping')
        assert hasattr(config, 'date_format')

        print(f"  ✓ CASP config loaded successfully")
        print(f"    - CSV URL: {config.csv_url}")
        print(f"    - Date format: {config.date_format}")
        print(f"    - Column mappings: {len(config.column_mapping)} columns")
        print(f"    - Multi-value fields: {list(config.multi_value_fields.keys())}")

        return True

    except Exception as e:
        print(f"  ✗ Register config error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_relationships():
    """Test model relationships"""
    print("\n4. Testing model relationships...")
    try:
        from app.models import Entity, CaspEntity, Service, PassportCountry, RegisterType
        from app.database import SessionLocal

        db = SessionLocal()

        # Check if we can create a test entity
        try:
            # Create test service
            test_service = Service(code='a', description='Test service')
            db.add(test_service)

            # Create test country
            test_country = PassportCountry(country_code='FR')
            db.add(test_country)

            # Create test entity
            test_entity = Entity(
                register_type=RegisterType.CASP,
                lei='12345678901234567890',
                lei_name='Test Entity',
                home_member_state='FR',
                services=[test_service],  # Legacy relationship
                passport_countries=[test_country],  # Legacy relationship
            )
            db.add(test_entity)
            db.flush()

            # Create CASP extension
            test_casp = CaspEntity(
                id=test_entity.id,
                website_platform='test.com',
                services=[test_service],  # New relationship
                passport_countries=[test_country],  # New relationship
            )
            db.add(test_casp)
            db.flush()

            # Verify relationships
            assert len(test_entity.services) == 1, "Legacy services relationship failed"
            assert len(test_entity.passport_countries) == 1, "Legacy passport_countries relationship failed"
            assert test_entity.casp_entity is not None, "casp_entity relationship failed"
            assert len(test_entity.casp_entity.services) == 1, "New services relationship failed"
            assert len(test_entity.casp_entity.passport_countries) == 1, "New passport_countries relationship failed"

            print("  ✓ All relationships work correctly")
            print("    - Legacy services: ✓")
            print("    - Legacy passport_countries: ✓")
            print("    - New casp_entity: ✓")
            print("    - New casp_entity.services: ✓")
            print("    - New casp_entity.passport_countries: ✓")

            # Rollback test data
            db.rollback()
            return True

        except Exception as e:
            db.rollback()
            raise

        finally:
            db.close()

    except Exception as e:
        print(f"  ✗ Model relationships error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """Test API endpoints compile correctly"""
    print("\n5. Testing API endpoints...")
    try:
        from app.routers.entities import router

        # Check endpoints exist
        routes = [route.path for route in router.routes]

        expected_routes = [
            '/entities',
            '/entities/count',
            '/entities/{entity_id}',
            '/filters/options',
            '/filters/counts',
        ]

        for route in expected_routes:
            if route not in routes:
                print(f"  ✗ Missing route: {route}")
                return False

        print(f"  ✓ All API endpoints exist ({len(expected_routes)} endpoints)")

        return True

    except Exception as e:
        print(f"  ✗ API endpoints error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("CASP Structure Test (Post-Refactor)")
    print("=" * 70)

    all_passed = True

    # Run all tests
    tests = [
        test_imports,
        test_database_schema,
        test_register_config,
        test_model_relationships,
        test_api_endpoints,
    ]

    for test_func in tests:
        if not test_func():
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED!")
        print("=" * 70)
        print("\nCASP functionality structure is correct after refactoring.")
        print("Note: This test doesn't import actual data (requires pandas).")
        print("To test with real data, install dependencies: pip install -r requirements.txt")
        sys.exit(0)
    else:
        print("✗ SOME TESTS FAILED!")
        print("=" * 70)
        sys.exit(1)
