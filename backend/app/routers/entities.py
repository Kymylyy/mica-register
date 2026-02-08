import os

from fastapi import APIRouter, Depends, HTTPException, Query, Header, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import or_, and_, func, distinct, exists, select
from typing import List, Optional
from datetime import date
from ..database import get_db, engine, Base
from ..models import (
    Entity, Service, PassportCountry, EntityTag,
    entity_service, casp_entity_service,  # Legacy and new association tables
    CaspEntity, OtherEntity, ArtEntity, EmtEntity, NcaspEntity
)
from ..schemas import Entity as EntitySchema, EntityTag as EntityTagSchema, TagCreate, EntityUpdate, PaginatedResponse
from ..config.registers import RegisterType
from ..config.constants import (
    MICA_SERVICE_DESCRIPTIONS,
    MICA_SERVICE_SHORT_NAMES,
    MICA_SERVICE_MEDIUM_NAMES,
    COUNTRY_NAMES
)

router = APIRouter()


ENTITY_EAGER_LOAD_OPTIONS = [
    selectinload(Entity.tags),
    selectinload(Entity.services),
    selectinload(Entity.passport_countries),
    selectinload(Entity.casp_entity).selectinload(CaspEntity.services),
    selectinload(Entity.casp_entity).selectinload(CaspEntity.passport_countries),
    selectinload(Entity.other_entity),
    selectinload(Entity.art_entity),
    selectinload(Entity.emt_entity),
    selectinload(Entity.ncasp_entity),
]


def require_admin_token(authorization: Optional[str] = Header(None)) -> None:
    """Require valid Bearer token for admin endpoints."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header"
        )

    bearer_prefix = "Bearer "
    if not authorization.startswith(bearer_prefix):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format"
        )

    provided_token = authorization[len(bearer_prefix):].strip()
    expected_token = os.getenv("ADMIN_API_TOKEN") or os.getenv("ADMIN_TOKEN")

    if not expected_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin API token is not configured"
        )

    if provided_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token"
        )


def apply_search_filter(query, search: str, register_type: RegisterType = RegisterType.CASP):
    """Apply search filter: commercial name, LEI name, address, website, authority, comments, country names, and service names (CASP only)

    Args:
        query: SQLAlchemy query object
        search: Search string
        register_type: Register type (for service search - only CASP has services)
    """
    if not search:
        return query

    search_lower = search.lower().strip()
    search_original = search.strip()

    # Build search conditions - search common Entity fields
    search_conditions = [
        Entity.commercial_name.ilike(f"%{search_original}%"),
        Entity.lei_name.ilike(f"%{search_original}%"),
        Entity.address.ilike(f"%{search_original}%"),
        Entity.website.ilike(f"%{search_original}%"),
        Entity.competent_authority.ilike(f"%{search_original}%"),
        Entity.comments.ilike(f"%{search_original}%"),
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

    # Check if search term matches any service description (CASP only)
    # Other registers don't have services, so skip this check
    if register_type == RegisterType.CASP:
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

        # Add service search using NEW casp_entity_service table
        if matching_service_codes:
            # Use EXISTS with casp_entity_service (new table)
            # This ensures it works after legacy entity_service is dropped
            service_exists = exists().where(
                and_(
                    CaspEntity.id == Entity.id,  # Join to CaspEntity first
                    casp_entity_service.c.casp_entity_id == CaspEntity.id,
                    casp_entity_service.c.service_id == Service.id,
                    Service.code.in_(matching_service_codes)
                )
            )
            search_conditions.append(service_exists)

    # Add register-specific field searches
    # Search in white_paper_url for OTHER, ART, EMT registers
    if register_type == RegisterType.OTHER:
        white_paper_exists = exists().where(
            and_(
                OtherEntity.id == Entity.id,
                OtherEntity.white_paper_url.ilike(f"%{search_original}%")
            )
        )
        search_conditions.append(white_paper_exists)
    elif register_type == RegisterType.ART:
        white_paper_exists = exists().where(
            and_(
                ArtEntity.id == Entity.id,
                ArtEntity.white_paper_url.ilike(f"%{search_original}%")
            )
        )
        search_conditions.append(white_paper_exists)
    elif register_type == RegisterType.EMT:
        white_paper_exists = exists().where(
            and_(
                EmtEntity.id == Entity.id,
                EmtEntity.white_paper_url.ilike(f"%{search_original}%")
            )
        )
        search_conditions.append(white_paper_exists)
    elif register_type == RegisterType.NCASP:
        # Search in multiple websites (pipe-separated)
        websites_exists = exists().where(
            and_(
                NcaspEntity.id == Entity.id,
                NcaspEntity.websites.ilike(f"%{search_original}%")
            )
        )
        search_conditions.append(websites_exists)

    # Combine all search conditions with OR
    search_filter = or_(*search_conditions)
    query = query.filter(search_filter)

    return query


@router.get("/entities", response_model=PaginatedResponse)
def get_entities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    register_type: RegisterType = Query(RegisterType.CASP, description="Register type to query"),
    home_member_states: Optional[List[str]] = Query(None),
    service_codes: Optional[List[str]] = Query(None),
    search: Optional[str] = None,
    auth_date_from: Optional[date] = None,
    auth_date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get list of entities with filtering and pagination metadata

    Args:
        register_type: Register type (casp, other, art, emt, ncasp). Default: casp
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        Other filters apply based on register type

    Returns:
        PaginatedResponse with items, total count, and pagination info
    """
    query = db.query(Entity).options(*ENTITY_EAGER_LOAD_OPTIONS)

    # Filter by register type
    query = query.filter(Entity.register_type == register_type)

    # Apply common filters
    if home_member_states and len(home_member_states) > 0:
        query = query.filter(Entity.home_member_state.in_(home_member_states))

    # Service codes filter - only applicable for CASP
    if service_codes and len(service_codes) > 0:
        if register_type == RegisterType.CASP:
            # AND logic: entity must have ALL selected services
            # Count how many selected services each entity has
            service_count_subquery = (
                select(CaspEntity.id)
                .join(CaspEntity.services)
                .filter(Service.code.in_(service_codes))
                .group_by(CaspEntity.id)
                .having(func.count(Service.code) == len(service_codes))
            )
            query = query.filter(Entity.id.in_(service_count_subquery))
        # For other registers, ignore service_codes filter

    if search:
        query = apply_search_filter(query, search, register_type)

    if auth_date_from:
        query = query.filter(Entity.authorisation_notification_date >= auth_date_from)

    if auth_date_to:
        query = query.filter(Entity.authorisation_notification_date <= auth_date_to)

    # Get total count before pagination
    total = query.count()

    # Apply pagination
    entities = query.offset(skip).limit(limit).all()

    # Return paginated response with metadata
    return PaginatedResponse(
        items=entities,
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + limit) < total
    )


@router.get("/entities/count")
def get_entities_count(
    register_type: RegisterType = Query(RegisterType.CASP, description="Register type to query"),
    home_member_states: Optional[List[str]] = Query(None),
    service_codes: Optional[List[str]] = Query(None),
    search: Optional[str] = None,
    auth_date_from: Optional[date] = None,
    auth_date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get count of entities with applied filters"""
    query = db.query(Entity)

    # Filter by register type
    query = query.filter(Entity.register_type == register_type)

    # Apply same filters as get_entities
    if home_member_states and len(home_member_states) > 0:
        query = query.filter(Entity.home_member_state.in_(home_member_states))

    # Service codes filter - only for CASP
    if service_codes and len(service_codes) > 0:
        if register_type == RegisterType.CASP:
            # AND logic: entity must have ALL selected services
            service_count_subquery = (
                select(CaspEntity.id)
                .join(CaspEntity.services)
                .filter(Service.code.in_(service_codes))
                .group_by(CaspEntity.id)
                .having(func.count(Service.code) == len(service_codes))
            )
            query = query.filter(Entity.id.in_(service_count_subquery))

    if search:
        query = apply_search_filter(query, search, register_type)

    if auth_date_from:
        query = query.filter(Entity.authorisation_notification_date >= auth_date_from)

    if auth_date_to:
        query = query.filter(Entity.authorisation_notification_date <= auth_date_to)

    count = query.count()
    return {"count": count}


@router.get("/entities/{entity_id}", response_model=EntitySchema)
def get_entity(entity_id: int, db: Session = Depends(get_db)):
    """Get single entity by ID"""
    entity = db.query(Entity).options(*ENTITY_EAGER_LOAD_OPTIONS).filter(Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.get("/filters/options")
def get_filter_options(
    register_type: RegisterType = Query(RegisterType.CASP, description="Register type to query"),
    db: Session = Depends(get_db)
):
    """Get available filter options for a specific register type"""
    import re

    # Get home member states with their authorities grouped by country
    # Filter by register type
    authorities_data = db.query(
        Entity.home_member_state,
        Entity.competent_authority
    ).filter(Entity.register_type == register_type).distinct().all()
    
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
    
    # Get service codes - only for CASP register
    service_codes = []
    if register_type == RegisterType.CASP:
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

    result = {
        "home_member_states": home_member_states,
        "service_codes": service_codes  # Empty for non-CASP registers
    }

    return result


@router.get("/filters/counts")
def get_filter_counts(
    register_type: RegisterType = Query(RegisterType.CASP, description="Register type to query"),
    home_member_states: Optional[List[str]] = Query(None),
    service_codes: Optional[List[str]] = Query(None),
    search: Optional[str] = None,
    auth_date_from: Optional[date] = None,
    auth_date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get entity counts for each filter option with current filters applied

    OPTIMIZED: Uses GROUP BY queries instead of multiple COUNT queries (15-25x faster)
    """
    # MiCA standard service codes (for filtering valid services)
    mica_service_codes = {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'}

    # === COUNTRY COUNTS - Single GROUP BY query ===
    # Build base query for countries with all filters EXCEPT home_member_states
    country_query = db.query(
        Entity.home_member_state,
        func.count(distinct(Entity.id)).label('count')
    ).filter(Entity.register_type == register_type)  # Filter by register type

    # Apply filters (excluding home_member_states)
    if search:
        country_query = apply_search_filter(country_query, search, register_type)

    if auth_date_from:
        country_query = country_query.filter(Entity.authorisation_notification_date >= auth_date_from)

    if auth_date_to:
        country_query = country_query.filter(Entity.authorisation_notification_date <= auth_date_to)

    # Apply service_codes filter if present (CASP only) - AND logic
    if service_codes and len(service_codes) > 0 and register_type == RegisterType.CASP:
        service_count_subquery = (
            select(CaspEntity.id)
            .join(CaspEntity.services)
            .filter(Service.code.in_(service_codes))
            .group_by(CaspEntity.id)
            .having(func.count(Service.code) == len(service_codes))
        )
        country_query = country_query.filter(Entity.id.in_(service_count_subquery))

    # Group by country and get counts
    country_query = country_query.group_by(Entity.home_member_state)
    country_results = country_query.all()

    # Convert to dict, filtering out null countries
    country_counts = {
        country: count
        for country, count in country_results
        if country is not None
    }

    # === SERVICE COUNTS - Single GROUP BY query (CASP only) ===
    service_counts = {}

    if register_type == RegisterType.CASP:
        # Build base query for services with all filters
        # With AND logic, we need to show services only on entities that have ALL currently selected services
        service_query = db.query(
            Service.code,
            func.count(distinct(Entity.id)).label('count')
        ).join(CaspEntity.services).join(CaspEntity.entity).filter(
            Entity.register_type == RegisterType.CASP
        )  # Join through casp_entity

        # Apply filters
        if home_member_states and len(home_member_states) > 0:
            service_query = service_query.filter(Entity.home_member_state.in_(home_member_states))

        # Apply service_codes filter with AND logic - show counts only for entities that have ALL selected services
        if service_codes and len(service_codes) > 0:
            service_count_subquery = (
                select(CaspEntity.id)
                .join(CaspEntity.services)
                .filter(Service.code.in_(service_codes))
                .group_by(CaspEntity.id)
                .having(func.count(Service.code) == len(service_codes))
            )
            service_query = service_query.filter(Entity.id.in_(service_count_subquery))

        if search:
            service_query = apply_search_filter(service_query, search, register_type)

        if auth_date_from:
            service_query = service_query.filter(Entity.authorisation_notification_date >= auth_date_from)

        if auth_date_to:
            service_query = service_query.filter(Entity.authorisation_notification_date <= auth_date_to)

        # Group by service code and get counts
        service_query = service_query.group_by(Service.code)
        service_results = service_query.all()

        # Convert to dict, filtering to only MiCA standard codes
        service_counts = {
            code: count
            for code, count in service_results
            if code in mica_service_codes
        }

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
def import_data(
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_token)
):
    """Import CSV data for CASP register into database (admin endpoint)

    Automatically finds the newest CASP *_clean.csv file in data/cleaned/casp/
    directory based on date in filename (YYYYMMDD), not file modification time.
    Works both in Docker container and local development.

    Note: This endpoint imports CASP register only.
    For importing all 5 registers, use POST /api/admin/import-all instead.

    Returns:
        dict: Import summary with CASP entity count
    """
    import os
    from pathlib import Path
    from ..import_csv import import_csv_to_db
    from ..models import RegisterType
    from ..utils.file_utils import get_latest_csv_for_register, get_base_data_dir

    # Find newest cleaned CASP CSV using file_utils
    base_dir = get_base_data_dir() / "cleaned"
    csv_file = get_latest_csv_for_register(
        RegisterType.CASP,
        base_dir,
        file_stage="cleaned",
        prefer_llm=True
    )

    if csv_file:
        csv_path = str(csv_file)
    else:
        # Fallback: try old locations for backward compatibility
        possible_paths = [
            "/app/casp-register.csv",
            "/app/data/casp-register.csv",
            os.path.join(Path(__file__).parent.parent.parent, "data", "casp-register.csv"),
            os.path.join(Path(__file__).parent.parent.parent, "casp-register.csv"),
            "casp-register.csv",
        ]

        csv_path = None
        for path in possible_paths:
            if os.path.exists(path):
                csv_path = path
                break

    if not csv_path:
        raise HTTPException(
            status_code=404,
            detail=f"CSV file not found. Checked data/cleaned/ directory for CASP *_clean.csv files and fallback locations."
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


@router.post("/admin/import-all")
def import_all_registers(
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_token)
):
    """Import CSV data for ALL registers into database (admin endpoint)

    Automatically finds the newest *_clean.csv file in data/cleaned/{register}/
    directory for each of the 5 ESMA MiCA registers (CASP, OTHER, ART, EMT, NCASP).

    This is the recommended endpoint for production data imports.
    For CASP-only import, use /api/admin/import instead.

    Returns:
        dict: Import summary with counts per register
    """
    import logging
    from pathlib import Path
    from ..import_csv import import_csv_to_db
    from ..models import RegisterType, Entity
    from ..utils.file_utils import get_latest_csv_for_register, get_base_data_dir

    logger = logging.getLogger(__name__)

    # Base directory for cleaned CSV files
    base_dir = get_base_data_dir() / "cleaned"

    # Auto-detect latest cleaned CSV for each register
    register_files = {}
    for register_type in RegisterType:
        latest_file = get_latest_csv_for_register(
            register_type,
            base_dir,
            file_stage="cleaned",
            prefer_llm=True  # Prefer _clean_llm.csv if available
        )
        if latest_file:
            register_files[register_type] = latest_file
        else:
            logger.warning(f"No cleaned CSV found for {register_type.value.upper()}")

    if not register_files:
        raise HTTPException(
            status_code=404,
            detail="No cleaned CSV files found. Check data/cleaned/ directory structure."
        )

    try:
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)

        # Import each register
        import_summary = {}
        for register_type, csv_path in register_files.items():
            if not csv_path.exists():
                logger.warning(f"CSV file {csv_path} not found, skipping {register_type.value.upper()}")
                continue

            logger.info(f"Importing {register_type.value.upper()} register from {csv_path}")

            # Import CSV to database
            import_csv_to_db(db, str(csv_path), register_type)

            # Get count of imported entities for this register
            count = db.query(Entity).filter(Entity.register_type == register_type).count()
            import_summary[register_type.value] = {
                "csv_path": str(csv_path),
                "entities_count": count
            }

        # Get total count
        total_count = db.query(Entity).count()

        return {
            "message": "All registers imported successfully",
            "registers": import_summary,
            "total_entities": total_count
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error importing all registers: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error importing all registers: {str(e)}"
        )

