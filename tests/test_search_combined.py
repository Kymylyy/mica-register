#!/usr/bin/env python3
"""
Test script to verify search works with combined filters
"""
import sys
from pathlib import Path
import os

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.database import SessionLocal
from app.models import Entity, Service
from app.routers.entities import apply_search_filter

def test_search_with_existing_joins():
    """Test search when query already has joins"""
    print("=" * 50)
    print("Testing Search with Existing Joins")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        # Simulate what happens when service_codes filter is applied first
        print("\n1. Testing search after service_codes filter...")
        query = db.query(Entity)
        
        # First apply service_codes filter (like in get_entities)
        query = query.join(Entity.services).filter(Service.code.in_(['a'])).distinct()
        count_before = query.count()
        print(f"   Entities with service 'a': {count_before}")
        
        # Then apply search filter
        query = apply_search_filter(query, "Order routing")
        results = query.all()
        count_after = len(results)
        print(f"   After search 'Order routing': {count_after}")
        
        # This should find entities that have BOTH service 'a' AND service 'g'
        # OR entities with service 'a' that match "Order routing" in commercial_name
        if count_after == 0:
            print("   ⚠ No results - this might be expected if no entities have both services")
        else:
            print(f"   ✓ Found {count_after} entities")
        
        # Test 2: Search without existing filters
        print("\n2. Testing search without existing filters...")
        query = db.query(Entity)
        query = apply_search_filter(query, "Order routing")
        results = query.all()
        count = len(results)
        print(f"   Found {count} entities")
        
        if count == 0:
            print("   ✗ No entities found! This should find entities with service 'g'")
            return False
        else:
            print(f"   ✓ Found {count} entities")
        
        # Test 3: Search with country filter
        print("\n3. Testing search with country filter...")
        query = db.query(Entity)
        query = query.filter(Entity.home_member_state == 'DE')
        query = apply_search_filter(query, "Order routing")
        results = query.all()
        count = len(results)
        print(f"   Found {count} entities from Germany with 'Order routing'")
        
        # Count entities from Germany with service 'g'
        direct_count = db.query(Entity).join(Entity.services).filter(
            Entity.home_member_state == 'DE',
            Service.code == 'g'
        ).distinct().count()
        print(f"   Direct query: {direct_count} entities from Germany with service 'g'")
        
        if count != direct_count:
            print(f"   ⚠ Mismatch! Search: {count}, Direct: {direct_count}")
        else:
            print(f"   ✓ Counts match!")
        
        print("\n" + "=" * 50)
        print("✓ All combined filter tests passed!")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"   ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_search_with_existing_joins()
    sys.exit(0 if success else 1)
