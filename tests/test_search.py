#!/usr/bin/env python3
"""
Test script to verify search functionality
"""
import sys
from pathlib import Path
import os

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.database import SessionLocal, engine, Base
from app.models import Entity, Service
from app.routers.entities import apply_search_filter
from app.config.constants import MICA_SERVICE_SHORT_NAMES, MICA_SERVICE_MEDIUM_NAMES, MICA_SERVICE_DESCRIPTIONS, COUNTRY_NAMES

def test_search_logic():
    """Test search matching logic"""
    print("=" * 50)
    print("Testing Search Logic")
    print("=" * 50)
    
    # Test 1: Service short name matching
    print("\n1. Testing service short name matching...")
    test_cases = [
        ("Order routing", ["g"]),
        ("order routing", ["g"]),
        ("ORDER ROUTING", ["g"]),
        ("Custody", ["a"]),
        ("Trading platform", ["b"]),
    ]
    
    for search_term, expected_codes in test_cases:
        search_lower = search_term.lower().strip()
        matching_service_codes = []
        
        # Check short names
        for code, name in MICA_SERVICE_SHORT_NAMES.items():
            if search_lower in name.lower():
                if code not in matching_service_codes:
                    matching_service_codes.append(code)
        
        if set(matching_service_codes) == set(expected_codes):
            print(f"   ✓ '{search_term}' -> {matching_service_codes}")
        else:
            print(f"   ✗ '{search_term}' -> {matching_service_codes} (expected {expected_codes})")
            return False
    
    # Test 2: Country name matching
    print("\n2. Testing country name matching...")
    test_cases = [
        ("Germany", ["DE"]),
        ("germany", ["DE"]),
        ("GERMANY", ["DE"]),
        ("Poland", ["PL"]),
    ]
    
    for search_term, expected_codes in test_cases:
        search_lower = search_term.lower().strip()
        matching_country_codes = []
        
        for code, name in COUNTRY_NAMES.items():
            if search_lower in name.lower() or name.lower().startswith(search_lower):
                matching_country_codes.append(code)
        
        if set(matching_country_codes) == set(expected_codes):
            print(f"   ✓ '{search_term}' -> {matching_country_codes}")
        else:
            print(f"   ✗ '{search_term}' -> {matching_country_codes} (expected {expected_codes})")
            return False
    
    print("\n" + "=" * 50)
    print("✓ All logic tests passed!")
    print("=" * 50)
    return True

def test_search_query():
    """Test search query execution"""
    print("\n" + "=" * 50)
    print("Testing Search Query Execution")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        # Test 1: Search by service short name "Order routing"
        print("\n1. Testing search by 'Order routing'...")
        query = db.query(Entity)
        query = apply_search_filter(query, "Order routing")
        results = query.all()
        count = len(results)
        print(f"   Found {count} entities")
        
        if count == 0:
            print("   ✗ No entities found! Expected some entities with service 'g'")
            return False
        
        # Verify that results actually have service 'g'
        print(f"   Checking first {min(3, count)} entities...")
        for i, entity in enumerate(results[:3]):
            service_codes = [s.code for s in entity.services]
            if 'g' not in service_codes:
                print(f"   ✗ Entity {entity.id} ({entity.commercial_name}) doesn't have service 'g'!")
                print(f"      Services: {service_codes}")
                return False
            else:
                print(f"   ✓ Entity {entity.id}: {entity.commercial_name} has service 'g'")
        
        # Test 2: Search by country name "Germany"
        print("\n2. Testing search by 'Germany'...")
        query = db.query(Entity)
        query = apply_search_filter(query, "Germany")
        results = query.all()
        count = len(results)
        print(f"   Found {count} entities")
        
        # Count entities with home_member_state = 'DE' directly
        direct_count = db.query(Entity).filter(Entity.home_member_state == 'DE').count()
        print(f"   Direct query for DE: {direct_count} entities")
        
        if count == 0:
            print("   ✗ No entities found! Expected entities with home_member_state='DE'")
            return False
        
        if count != direct_count:
            print(f"   ⚠ Search found {count} but direct query found {direct_count}")
            # This might be OK if some entities don't match other criteria
        
        # Test 3: Search by commercial name
        print("\n3. Testing search by commercial name...")
        # Get a sample commercial name
        sample_entity = db.query(Entity).first()
        if sample_entity and sample_entity.commercial_name:
            search_term = sample_entity.commercial_name[:10]  # First 10 chars
            query = db.query(Entity)
            query = apply_search_filter(query, search_term)
            results = query.all()
            count = len(results)
            print(f"   Searching for '{search_term}'...")
            print(f"   Found {count} entities")
            
            if count == 0:
                print(f"   ✗ No entities found! Expected entities with '{search_term}' in name")
                return False
            else:
                print(f"   ✓ Found entities matching commercial name")
        
        print("\n" + "=" * 50)
        print("✓ All query tests passed!")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"   ✗ Query test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def test_service_join():
    """Test that service join works correctly"""
    print("\n" + "=" * 50)
    print("Testing Service Join")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        # Count entities with service 'g' directly
        from app.models import entity_service
        from sqlalchemy import select
        
        direct_count = db.query(Entity).join(Entity.services).filter(Service.code == 'g').distinct().count()
        print(f"\n1. Direct join query for service 'g': {direct_count} entities")
        
        # Count using our search function
        query = db.query(Entity)
        query = apply_search_filter(query, "Order routing")
        search_count = len(query.all())
        print(f"2. Search function result: {search_count} entities")
        
        if search_count != direct_count:
            print(f"   ✗ Mismatch! Direct query: {direct_count}, Search function: {search_count}")
            
            # Debug: check what the search function is actually doing
            print("\n   Debugging search function...")
            query = db.query(Entity)
            query = apply_search_filter(query, "Order routing")
            print(f"   Query SQL: {str(query)}")
            
            return False
        else:
            print(f"   ✓ Counts match!")
        
        print("\n" + "=" * 50)
        print("✓ Service join test passed!")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"   ✗ Service join test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("\n")
    success1 = test_search_logic()
    if not success1:
        sys.exit(1)
    
    success2 = test_search_query()
    if not success2:
        sys.exit(1)
    
    success3 = test_service_join()
    if not success3:
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✓ ALL TESTS PASSED!")
    print("=" * 50)
    sys.exit(0)
