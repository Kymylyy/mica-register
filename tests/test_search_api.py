#!/usr/bin/env python3
"""
Test script to verify search API endpoint works correctly
Simulates actual HTTP requests
"""
import sys
from pathlib import Path
import os

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, engine, Base
from app.models import Entity, Service

# Create test client
client = TestClient(app)

def test_search_api_endpoint():
    """Test the actual API endpoint"""
    print("=" * 50)
    print("Testing Search API Endpoint")
    print("=" * 50)
    
    # Test 1: Search by service short name "Order routing"
    print("\n1. Testing GET /api/entities?search=Order+routing...")
    response = client.get("/api/entities?search=Order+routing&limit=1000")
    
    if response.status_code != 200:
        print(f"   ✗ Status code: {response.status_code}")
        print(f"   Response: {response.text}")
        return False
    
    data = response.json()
    entities = data.get("items", data) if isinstance(data, dict) else data
    count = len(entities)
    print(f"   Found {count} entities")
    
    if count == 0:
        print("   ✗ No entities found! Expected entities with service 'g'")
        return False
    
    # Verify that results actually have service 'g'
    print(f"   Checking first {min(3, count)} entities...")
    db = SessionLocal()
    try:
        for i, entity_data in enumerate(entities[:3]):
            entity_id = entity_data['id']
            entity = db.query(Entity).filter(Entity.id == entity_id).first()
            if entity:
                service_codes = [s.code for s in entity.services]
                if 'g' not in service_codes:
                    print(f"   ✗ Entity {entity_id} ({entity.commercial_name}) doesn't have service 'g'!")
                    print(f"      Services: {service_codes}")
                    return False
                else:
                    print(f"   ✓ Entity {entity_id}: {entity.commercial_name} has service 'g'")
    finally:
        db.close()
    
    # Test 2: Search by service short name with URL encoding
    print("\n2. Testing GET /api/entities?search=Order%20routing...")
    response = client.get("/api/entities?search=Order%20routing&limit=1000")
    
    if response.status_code != 200:
        print(f"   ✗ Status code: {response.status_code}")
        return False
    
    data2 = response.json()
    entities2 = data2.get("items", data2) if isinstance(data2, dict) else data2
    count2 = len(entities2)
    print(f"   Found {count2} entities")
    
    if count != count2:
        print(f"   ✗ Different counts! First: {count}, Second: {count2}")
        return False
    
    # Test 3: Search by country name "Germany"
    print("\n3. Testing GET /api/entities?search=Germany...")
    response = client.get("/api/entities?search=Germany&limit=1000")
    
    if response.status_code != 200:
        print(f"   ✗ Status code: {response.status_code}")
        return False
    
    data3 = response.json()
    entities3 = data3.get("items", data3) if isinstance(data3, dict) else data3
    count3 = len(entities3)
    print(f"   Found {count3} entities")
    
    # Count entities with home_member_state = 'DE' directly
    db = SessionLocal()
    try:
        direct_count = db.query(Entity).filter(Entity.home_member_state == 'DE').count()
        print(f"   Direct query for DE: {direct_count} entities")
        
        if count3 != direct_count:
            print(f"   ⚠ Search found {count3} but direct query found {direct_count}")
    finally:
        db.close()
    
    # Test 4: Count endpoint
    print("\n4. Testing GET /api/entities/count?search=Order+routing...")
    response = client.get("/api/entities/count?search=Order+routing")
    
    if response.status_code != 200:
        print(f"   ✗ Status code: {response.status_code}")
        return False
    
    count_data = response.json()
    api_count = count_data.get('count', 0)
    print(f"   API count: {api_count}")
    print(f"   Actual entities returned: {count}")
    
    if api_count != count:
        print(f"   ⚠ Count mismatch! API count: {api_count}, Actual: {count}")
    else:
        print(f"   ✓ Counts match!")
    
    print("\n" + "=" * 50)
    print("✓ All API endpoint tests passed!")
    print("=" * 50)
    return True

if __name__ == "__main__":
    success = test_search_api_endpoint()
    sys.exit(0 if success else 1)
