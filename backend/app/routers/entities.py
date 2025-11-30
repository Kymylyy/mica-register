from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from datetime import date
from ..database import get_db, engine, Base
from ..models import Entity, Service, PassportCountry, EntityTag
from ..schemas import Entity as EntitySchema, EntityTag as EntityTagSchema, TagCreate, EntityUpdate

router = APIRouter()

# MiCA service descriptions for search matching (full descriptions)
MICA_SERVICE_DESCRIPTIONS = {
    "a": "providing custody and administration of crypto-assets on behalf of clients",
    "b": "operation of a trading platform for crypto-assets",
    "c": "exchange of crypto-assets for funds",
    "d": "exchange of crypto-assets for other crypto-assets",
    "e": "execution of orders for crypto-assets on behalf of clients",
    "f": "placing of crypto-assets",
    "g": "reception and transmission of orders for crypto-assets on behalf of clients",
    "h": "providing advice on crypto-assets",
    "i": "providing portfolio management on crypto-assets",
    "j": "providing transfer services for crypto-assets on behalf of clients"
}

# Short service names for search matching
MICA_SERVICE_SHORT_NAMES = {
    "a": "Custody",
    "b": "Trading platform",
    "c": "Crypto-to-funds",
    "d": "Crypto-to-crypto",
    "e": "Order execution",
    "f": "Placement",
    "g": "Order routing",
    "h": "Advisory",
    "i": "Portfolio management",
    "j": "Transfer"
}

# Medium service names for search matching
MICA_SERVICE_MEDIUM_NAMES = {
    "a": "Custody and administration",
    "b": "Trading platform operation",
    "c": "Crypto-to-funds exchange",
    "d": "Crypto-to-crypto exchange",
    "e": "Order execution",
    "f": "Placing of crypto-assets",
    "g": "Reception and transmission of orders",
    "h": "Crypto-asset advisory",
    "i": "Portfolio management",
    "j": "Transfer services"
}

# Country code to full English name mapping (for search)
COUNTRY_NAMES = {
    'AT': 'Austria',
    'BE': 'Belgium',
    'BG': 'Bulgaria',
    'CY': 'Cyprus',
    'CZ': 'Czech Republic',
    'DE': 'Germany',
    'DK': 'Denmark',
    'EE': 'Estonia',
    'ES': 'Spain',
    'FI': 'Finland',
    'FR': 'France',
    'GR': 'Greece',
    'HR': 'Croatia',
    'HU': 'Hungary',
    'IE': 'Ireland',
    'IS': 'Iceland',
    'IT': 'Italy',
    'LI': 'Liechtenstein',
    'LT': 'Lithuania',
    'LU': 'Luxembourg',
    'LV': 'Latvia',
    'MT': 'Malta',
    'NL': 'Netherlands',
    'NO': 'Norway',
    'PL': 'Poland',
    'PT': 'Portugal',
    'RO': 'Romania',
    'SE': 'Sweden',
    'SI': 'Slovenia',
    'SK': 'Slovakia',
    'EL': 'Greece',  # Alternative code for Greece
}

def apply_search_filter(query, search: str):
    """Apply search filter: commercial name, country names, and service names (short/medium/full)"""
    if not search:
        return query
    
    search_lower = search.lower().strip()
    search_original = search.strip()
    
    # Build search conditions - only commercial_name
    search_conditions = [
        Entity.commercial_name.ilike(f"%{search_original}%"),
    ]
    
    # Check if search term matches any country name (e.g., "Germany" -> "DE")
    # Only map country names, NOT country codes
    matching_country_codes = []
    for code, name in COUNTRY_NAMES.items():
        if search_lower in name.lower() or name.lower().startswith(search_lower):
            matching_country_codes.append(code)
    
    # Add country code matches to search conditions
    if matching_country_codes:
        search_conditions.append(Entity.home_member_state.in_(matching_country_codes))
    
    # Check if search term matches any service description (full, medium, or short)
    matching_service_codes = []
    
    # Check full descriptions
    for code, description in MICA_SERVICE_DESCRIPTIONS.items():
        if search_lower in description.lower():
            if code not in matching_service_codes:
                matching_service_codes.append(code)
    
    # Check medium names
    for code, name in MICA_SERVICE_MEDIUM_NAMES.items():
        if search_lower in name.lower():
            if code not in matching_service_codes:
                matching_service_codes.append(code)
    
    # Check short names
    for code, name in MICA_SERVICE_SHORT_NAMES.items():
        if search_lower in name.lower():
            if code not in matching_service_codes:
                matching_service_codes.append(code)
    
    # Combine all search conditions
    search_filter = or_(*search_conditions)
    
    if matching_service_codes:
        # If search matches services, also filter by those services
        # Use join (inner join) to ensure we only get entities with matching services
        query = query.join(Entity.services).filter(
            or_(
                search_filter,
                Service.code.in_(matching_service_codes)
            )
        ).distinct()
    else:
        query = query.filter(search_filter)
    
    return query


@router.get("/entities", response_model=List[EntitySchema])
def get_entities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    home_member_states: Optional[List[str]] = Query(None),
    service_codes: Optional[List[str]] = Query(None),
    search: Optional[str] = None,
    auth_date_from: Optional[date] = None,
    auth_date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get list of entities with filtering"""
    query = db.query(Entity)
    
    # Apply filters
    if home_member_states and len(home_member_states) > 0:
        query = query.filter(Entity.home_member_state.in_(home_member_states))
    
    if service_codes and len(service_codes) > 0:
        query = query.join(Entity.services).filter(Service.code.in_(service_codes)).distinct()
    
    if search:
        query = apply_search_filter(query, search)
    
    if auth_date_from:
        query = query.filter(Entity.authorisation_notification_date >= auth_date_from)
    
    if auth_date_to:
        query = query.filter(Entity.authorisation_notification_date <= auth_date_to)
    
    entities = query.offset(skip).limit(limit).all()
    return entities


@router.get("/entities/count")
def get_entities_count(
    home_member_states: Optional[List[str]] = Query(None),
    service_codes: Optional[List[str]] = Query(None),
    search: Optional[str] = None,
    auth_date_from: Optional[date] = None,
    auth_date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get count of entities with applied filters"""
    query = db.query(Entity)
    
    # Apply same filters as get_entities
    if home_member_states and len(home_member_states) > 0:
        query = query.filter(Entity.home_member_state.in_(home_member_states))
    
    if service_codes and len(service_codes) > 0:
        query = query.join(Entity.services).filter(Service.code.in_(service_codes)).distinct()
    
    if search:
        query = apply_search_filter(query, search)
    
    if auth_date_from:
        query = query.filter(Entity.authorisation_notification_date >= auth_date_from)
    
    if auth_date_to:
        query = query.filter(Entity.authorisation_notification_date <= auth_date_to)
    
    count = query.count()
    return {"count": count}


@router.get("/entities/{entity_id}", response_model=EntitySchema)
def get_entity(entity_id: int, db: Session = Depends(get_db)):
    """Get single entity by ID"""
    entity = db.query(Entity).filter(Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.get("/filters/options")
def get_filter_options(db: Session = Depends(get_db)):
    """Get available filter options"""
    import re
    
    # Get home member states with their authorities grouped by country
    authorities_data = db.query(
        Entity.home_member_state,
        Entity.competent_authority
    ).distinct().all()
    
    # Group by country code and extract abbreviations
    countries_dict = {}
    for state, authority in authorities_data:
        if state and authority:
            if state not in countries_dict:
                countries_dict[state] = []
            
            # Extract abbreviation from authority name (e.g., "Austrian Financial Market Authority (FMA)" -> "FMA")
            abbreviation = None
            match = re.search(r'\(([^)]+)\)', authority)
            if match:
                abbreviation = match.group(1)
            
            authority_info = {
                "name": authority,
                "abbreviation": abbreviation
            }
            
            # Check if this authority is already in the list
            if not any(a["name"] == authority for a in countries_dict[state]):
                countries_dict[state].append(authority_info)
    
    # Format as list of countries with authorities
    home_member_states = [
        {
            "country_code": country_code,
            "authorities": authorities
        }
        for country_code, authorities in sorted(countries_dict.items())
    ]
    
    # Get service codes (should be a-j after normalization)
    services = db.query(Service.code).distinct().order_by(Service.code).all()
    
    # MiCA standard service codes with descriptions
    mica_service_descriptions = {
        "a": "providing custody and administration of crypto-assets on behalf of clients",
        "b": "operation of a trading platform for crypto-assets",
        "c": "exchange of crypto-assets for funds",
        "d": "exchange of crypto-assets for other crypto-assets",
        "e": "execution of orders for crypto-assets on behalf of clients",
        "f": "placing of crypto-assets",
        "g": "reception and transmission of orders for crypto-assets on behalf of clients",
        "h": "providing advice on crypto-assets",
        "i": "providing portfolio management on crypto-assets",
        "j": "providing transfer services for crypto-assets on behalf of clients"
    }
    
    service_codes = [
        {
            "code": s[0],
            "description": mica_service_descriptions.get(s[0], s[0])
        }
        for s in services
        if s[0] in mica_service_descriptions
    ]
    
    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Services from DB: {[s[0] for s in services]}")
    logger.info(f"Service codes after processing: {len(service_codes)}")
    
    result = {
        "home_member_states": home_member_states,
        "service_codes": service_codes
    }
    
    return result


def _apply_filters(query, home_member_states, service_codes, search, auth_date_from, auth_date_to):
    """Helper function to apply filters to a query"""
    if home_member_states and len(home_member_states) > 0:
        query = query.filter(Entity.home_member_state.in_(home_member_states))
    
    if service_codes and len(service_codes) > 0:
        query = query.join(Entity.services).filter(Service.code.in_(service_codes)).distinct()
    
    if search:
        query = apply_search_filter(query, search)
    
    if auth_date_from:
        query = query.filter(Entity.authorisation_notification_date >= auth_date_from)
    
    if auth_date_to:
        query = query.filter(Entity.authorisation_notification_date <= auth_date_to)
    
    return query


@router.get("/filters/counts")
def get_filter_counts(
    home_member_states: Optional[List[str]] = Query(None),
    service_codes: Optional[List[str]] = Query(None),
    search: Optional[str] = None,
    auth_date_from: Optional[date] = None,
    auth_date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get entity counts for each filter option with current filters applied"""
    import re
    
    # Get all available countries and services
    all_countries = db.query(Entity.home_member_state).distinct().all()
    all_services = db.query(Service.code).distinct().order_by(Service.code).all()
    
    # MiCA standard service codes
    mica_service_descriptions = {
        "a": "providing custody and administration of crypto-assets on behalf of clients",
        "b": "operation of a trading platform for crypto-assets",
        "c": "exchange of crypto-assets for funds",
        "d": "exchange of crypto-assets for other crypto-assets",
        "e": "execution of orders for crypto-assets on behalf of clients",
        "f": "placing of crypto-assets",
        "g": "reception and transmission of orders for crypto-assets on behalf of clients",
        "h": "providing advice on crypto-assets",
        "i": "providing portfolio management on crypto-assets",
        "j": "providing transfer services for crypto-assets on behalf of clients"
    }
    
    # Calculate counts for each country
    # For each country, count entities matching current filters + this country
    country_counts = {}
    for (country_code,) in all_countries:
        if not country_code:
            continue
        
        # Build query with current filters + this specific country
        # Exclude home_member_states from current filters and add this country
        query = db.query(Entity)
        
        # Apply other filters (search, dates)
        if search:
            query = apply_search_filter(query, search)
        
        if auth_date_from:
            query = query.filter(Entity.authorisation_notification_date >= auth_date_from)
        
        if auth_date_to:
            query = query.filter(Entity.authorisation_notification_date <= auth_date_to)
        
        # Apply service_codes filter if present
        if service_codes and len(service_codes) > 0:
            query = query.join(Entity.services).filter(Service.code.in_(service_codes)).distinct()
        
        # Add this specific country
        query = query.filter(Entity.home_member_state == country_code)
        
        count = query.count()
        country_counts[country_code] = count
    
    # Calculate counts for each service
    # For each service, count entities matching current filters + this service
    service_counts = {}
    for (service_code,) in all_services:
        if service_code not in mica_service_descriptions:
            continue
        
        # Build query with current filters + this specific service
        query = db.query(Entity)
        
        # Apply other filters (home_member_states, search, dates)
        if home_member_states and len(home_member_states) > 0:
            query = query.filter(Entity.home_member_state.in_(home_member_states))
        
        if search:
            query = apply_search_filter(query, search)
        
        if auth_date_from:
            query = query.filter(Entity.authorisation_notification_date >= auth_date_from)
        
        if auth_date_to:
            query = query.filter(Entity.authorisation_notification_date <= auth_date_to)
        
        # Add this specific service
        query = query.join(Entity.services).filter(Service.code == service_code).distinct()
        
        count = query.count()
        service_counts[service_code] = count
    
    return {
        "country_counts": country_counts,
        "service_counts": service_counts
    }


@router.post("/entities/{entity_id}/tags", response_model=EntityTagSchema)
def add_tag(entity_id: int, tag: TagCreate, db: Session = Depends(get_db)):
    """Add a custom tag to an entity"""
    entity = db.query(Entity).filter(Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    # Check if tag already exists
    existing_tag = db.query(EntityTag).filter(
        EntityTag.entity_id == entity_id,
        EntityTag.tag_name == tag.tag_name
    ).first()
    
    if existing_tag:
        raise HTTPException(status_code=400, detail="Tag already exists")
    
    entity_tag = EntityTag(
        entity_id=entity_id,
        tag_name=tag.tag_name,
        tag_value=tag.tag_value
    )
    db.add(entity_tag)
    db.commit()
    db.refresh(entity_tag)
    return entity_tag


@router.delete("/entities/{entity_id}/tags/{tag_name}")
def remove_tag(entity_id: int, tag_name: str, db: Session = Depends(get_db)):
    """Remove a tag from an entity"""
    tag = db.query(EntityTag).filter(
        EntityTag.entity_id == entity_id,
        EntityTag.tag_name == tag_name
    ).first()
    
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    db.delete(tag)
    db.commit()
    return {"message": "Tag removed"}


@router.patch("/entities/{entity_id}", response_model=EntitySchema)
def update_entity(
    entity_id: int,
    update_data: EntityUpdate,
    db: Session = Depends(get_db)
):
    """Update entity fields (currently only comments)"""
    entity = db.query(Entity).filter(Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    if update_data.comments is not None:
        entity.comments = update_data.comments
    
    db.commit()
    db.refresh(entity)
    return entity


@router.post("/admin/import")
def import_data(db: Session = Depends(get_db)):
    """Import CSV data into database (admin endpoint)"""
    import os
    from pathlib import Path
    from ..import_csv import import_csv_to_db
    
    # Try multiple locations for CSV file
    possible_paths = [
        "/app/casp-register.csv",  # Docker container
        os.path.join(Path(__file__).parent.parent.parent, "casp-register.csv"),  # Local dev
        "casp-register.csv",  # Current directory
    ]
    
    csv_path = None
    for path in possible_paths:
        if os.path.exists(path):
            csv_path = path
            break
    
    if not csv_path:
        raise HTTPException(
            status_code=404, 
            detail=f"CSV file not found. Tried: {possible_paths}"
        )
    
    try:
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        
        # Import data
        import_csv_to_db(db, csv_path)
        
        # Get count of imported entities
        entity_count = db.query(Entity).count()
        
        return {
            "message": "Data imported successfully",
            "csv_path": csv_path,
            "entities_count": entity_count
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error importing data: {str(e)}"
        )


