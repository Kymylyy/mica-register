import os
from functools import cmp_to_key

from fastapi import APIRouter, Depends, HTTPException, Query, Header, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import or_, and_, func, distinct, exists, select
from typing import Any, Dict, List, Optional
from datetime import date
from ..database import get_db
from ..models import (
    Entity, Service, PassportCountry, EntityTag,
    casp_entity_service,  # New association table
    CaspEntity, OtherEntity, ArtEntity, EmtEntity, NcaspEntity, RegisterUpdateMetadata
)
from ..schemas import (
    CaspCompanyDetail,
    Entity as EntitySchema,
    EntityTag as EntityTagSchema,
    TagCreate,
    EntityUpdate,
    PaginatedCaspCompanyResponse,
    PaginatedResponse,
    LastUpdatedResponse,
)
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

COMMON_SORT_FIELDS = {
    "commercial_name",
    "lei_name",
    "lei",
    "lei_cou_code",
    "home_member_state",
    "competent_authority",
    "address",
    "website",
    "comments",
    "last_update",
}

REGISTER_SORT_FIELDS = {
    RegisterType.CASP: COMMON_SORT_FIELDS | {
        "authorisation_notification_date",
        "services",
        "passport_countries",
        "authorisation_end_date",
        "website_platform",
    },
    RegisterType.OTHER: COMMON_SORT_FIELDS | {
        "white_paper_url",
        "lei_casp",
        "lei_name_casp",
        "offer_countries",
        "dti_ffg",
        "dti_codes",
        "white_paper_comments",
    },
    RegisterType.ART: COMMON_SORT_FIELDS | {
        "authorisation_notification_date",
        "credit_institution",
        "white_paper_url",
        "white_paper_offer_countries",
        "authorisation_end_date",
        "white_paper_notification_date",
        "white_paper_comments",
    },
    RegisterType.EMT: COMMON_SORT_FIELDS | {
        "authorisation_notification_date",
        "authorisation_other_emt",
        "exemption_48_4",
        "exemption_48_5",
        "white_paper_notification_date",
        "white_paper_url",
        "dti_ffg",
        "dti_codes",
        "authorisation_end_date",
        "white_paper_comments",
    },
    RegisterType.NCASP: COMMON_SORT_FIELDS | {
        "infringement",
        "reason",
        "decision_date",
        "websites",
    },
}

CASP_COMPANY_SORT_FIELDS = COMMON_SORT_FIELDS | {
    "authorisation_notification_date",
    "services",
    "passport_countries",
    "authorisation_end_date",
    "website_platform",
}


def get_effective_home_member_state_expr():
    """Use home member state with fallback to LEI country code."""
    return func.upper(
        func.coalesce(
            func.nullif(func.trim(Entity.home_member_state), ""),
            func.nullif(func.trim(Entity.lei_cou_code), "")
        )
    )


def normalize_country_codes(country_codes: Optional[List[str]]) -> List[str]:
    """Normalize country codes from query params to uppercase 2-letter-like values."""
    return [code.strip().upper() for code in (country_codes or []) if code and code.strip()]


def apply_home_member_state_filter(query, home_member_states: Optional[List[str]]):
    """Filter by effective home member state (home state with LEI country fallback)."""
    normalized_states = normalize_country_codes(home_member_states)
    if not normalized_states:
        return query

    return query.filter(get_effective_home_member_state_expr().in_(normalized_states))


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
        search_conditions.append(get_effective_home_member_state_expr().in_(matching_country_codes))

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


def _get_casp_service_filter_subquery(service_codes: List[str]):
    return (
        select(CaspEntity.id)
        .join(CaspEntity.services)
        .filter(Service.code.in_(service_codes))
        .group_by(CaspEntity.id)
        .having(func.count(Service.code) == len(service_codes))
    )


def _apply_casp_row_filters(
    query,
    home_member_states: Optional[List[str]] = None,
    service_codes: Optional[List[str]] = None,
    search: Optional[str] = None,
    auth_date_from: Optional[date] = None,
    auth_date_to: Optional[date] = None,
):
    query = apply_home_member_state_filter(query, home_member_states)

    if service_codes and len(service_codes) > 0:
        query = query.filter(Entity.id.in_(_get_casp_service_filter_subquery(service_codes)))

    if search:
        query = apply_search_filter(query, search, RegisterType.CASP)

    if auth_date_from:
        query = query.filter(Entity.authorisation_notification_date >= auth_date_from)

    if auth_date_to:
        query = query.filter(Entity.authorisation_notification_date <= auth_date_to)

    return query


def _normalize_lei(lei: Optional[str]) -> Optional[str]:
    if not lei:
        return None
    lei = lei.strip()
    return lei or None


def _normalize_text_sort_value(value: Any) -> Optional[str]:
    if value is None:
        return None
    normalized = str(value).strip().lower()
    return normalized or None


def _normalize_url_sort_value(value: Optional[str]) -> Optional[str]:
    normalized = _normalize_text_sort_value(value)
    if not normalized:
        return None
    return normalized.removeprefix("https://").removeprefix("http://").removeprefix("www.")


def _normalize_pipe_sort_value(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    parts = sorted(
        part.strip().lower()
        for part in value.split("|")
        if part and part.strip()
    )
    if not parts:
        return None
    return "|".join(parts)


def _normalize_sequence_sort_value(values: List[str]) -> Optional[str]:
    parts = sorted(value.strip().lower() for value in values if value and value.strip())
    if not parts:
        return None
    return "|".join(parts)


def _normalize_bool_sort_value(value: Optional[bool]) -> Optional[int]:
    if value is None:
        return None
    return 1 if value else 0


def _normalize_reason_sort_value(value: Optional[str]) -> Optional[str]:
    if value == "None":
        return None
    return _normalize_text_sort_value(value)


def _effective_country_code(home_member_state: Optional[str], lei_cou_code: Optional[str]) -> Optional[str]:
    return _normalize_text_sort_value(home_member_state or lei_cou_code)


def _primary_display_name(commercial_name: Optional[str], lei_name: Optional[str]) -> Optional[str]:
    return _normalize_text_sort_value(commercial_name or lei_name)


def _compare_sort_values(left: Any, right: Any, descending: bool) -> int:
    if left is None and right is None:
        return 0
    if left is None:
        return 1
    if right is None:
        return -1

    if left < right:
        return -1 if not descending else 1
    if left > right:
        return 1 if not descending else -1
    return 0


def _compare_sorted_items(
    left_item: Any,
    right_item: Any,
    left_value: Any,
    right_value: Any,
    descending: bool,
) -> int:
    comparison = _compare_sort_values(left_value, right_value, descending)
    if comparison != 0:
        return comparison

    left_id = left_item.get("id") if isinstance(left_item, dict) else left_item.id
    right_id = right_item.get("id") if isinstance(right_item, dict) else right_item.id
    if left_id < right_id:
        return -1
    if left_id > right_id:
        return 1
    return 0


def _parse_sort_params(sort_by: Optional[str], sort_dir: Optional[str], allowed_fields: set[str]) -> tuple[Optional[str], bool]:
    if not sort_by:
        return None, False

    if sort_by not in allowed_fields:
        raise HTTPException(status_code=400, detail=f"Unsupported sort field: {sort_by}")

    if sort_dir is None:
        return sort_by, False

    normalized_sort_dir = sort_dir.lower()
    if normalized_sort_dir not in {"asc", "desc"}:
        raise HTTPException(status_code=400, detail=f"Unsupported sort direction: {sort_dir}")

    return sort_by, normalized_sort_dir == "desc"


def _casp_group_key(entity: Entity) -> str:
    return _normalize_lei(entity.lei) or f"entity:{entity.id}"


def _date_ordinal(value: Optional[date]) -> int:
    return value.toordinal() if value else 0


def _primary_casp_entity(entity: Entity) -> tuple[int, int, int, int, int]:
    return (
        _date_ordinal(entity.last_update),
        _date_ordinal(entity.authorisation_notification_date),
        len(entity.services or []),
        len(entity.passport_countries or []),
        -entity.id,
    )


def _record_sort_key(entity: Entity) -> tuple[int, int, int]:
    return (
        _date_ordinal(entity.authorisation_notification_date),
        _date_ordinal(entity.last_update),
        entity.id,
    )


def _serialize_service(service: Service) -> Dict[str, Any]:
    return {
        "id": service.id,
        "code": service.code,
        "description": service.description,
    }


def _serialize_passport_country(country: PassportCountry) -> Dict[str, Any]:
    return {
        "id": country.id,
        "country_code": country.country_code,
    }


def _collect_services(entities: List[Entity]) -> List[Dict[str, Any]]:
    services_by_code: Dict[str, Service] = {}
    for entity in entities:
        for service in entity.services or []:
            services_by_code.setdefault(service.code, service)
    return [
        _serialize_service(services_by_code[code])
        for code in sorted(services_by_code.keys())
    ]


def _collect_passport_countries(entities: List[Entity]) -> List[Dict[str, Any]]:
    countries_by_code: Dict[str, PassportCountry] = {}
    for entity in entities:
        for country in entity.passport_countries or []:
            countries_by_code.setdefault(country.country_code, country)
    return [
        _serialize_passport_country(countries_by_code[code])
        for code in sorted(countries_by_code.keys())
    ]


def _serialize_casp_authorisation_record(entity: Entity) -> Dict[str, Any]:
    return {
        "entity_id": entity.id,
        "authorisation_notification_date": entity.authorisation_notification_date,
        "authorisation_end_date": entity.authorisation_end_date,
        "last_update": entity.last_update,
        "services": [_serialize_service(service) for service in sorted(entity.services or [], key=lambda item: item.code)],
        "passport_countries": [
            _serialize_passport_country(country)
            for country in sorted(entity.passport_countries or [], key=lambda item: item.country_code)
        ],
        "comments": entity.comments,
        "website_platform": entity.website_platform,
    }


def _build_casp_company_payload(entities: List[Entity]) -> Dict[str, Any]:
    primary = max(entities, key=_primary_casp_entity)
    records = [
        _serialize_casp_authorisation_record(entity)
        for entity in sorted(entities, key=_record_sort_key)
    ]
    latest_auth_date = max((entity.authorisation_notification_date for entity in entities if entity.authorisation_notification_date), default=None)
    latest_last_update = max((entity.last_update for entity in entities if entity.last_update), default=None)

    return {
        "id": primary.id,
        "register_type": RegisterType.CASP.value,
        "competent_authority": primary.competent_authority,
        "home_member_state": primary.home_member_state,
        "lei_name": primary.lei_name,
        "lei": primary.lei,
        "lei_cou_code": primary.lei_cou_code,
        "commercial_name": primary.commercial_name,
        "address": primary.address,
        "website": primary.website,
        "authorisation_notification_date": latest_auth_date,
        "last_update": latest_last_update,
        "comments": primary.comments,
        "website_platform": primary.website_platform,
        "authorisation_end_date": primary.authorisation_end_date,
        "services": _collect_services(entities),
        "passport_countries": _collect_passport_countries(entities),
        "tags": [
            {
                "id": tag.id,
                "entity_id": tag.entity_id,
                "tag_name": tag.tag_name,
                "tag_value": tag.tag_value,
            }
            for tag in primary.tags or []
        ],
        "record_count": len(entities),
        "authorisation_records": records,
    }


def _load_all_rows_for_casp_groups(db: Session, seed_entities: List[Entity]) -> List[Entity]:
    leis = sorted({_normalize_lei(entity.lei) for entity in seed_entities if _normalize_lei(entity.lei)})
    singleton_ids = sorted([entity.id for entity in seed_entities if not _normalize_lei(entity.lei)])

    conditions = []
    if leis:
        conditions.append(Entity.lei.in_(leis))
    if singleton_ids:
        conditions.append(Entity.id.in_(singleton_ids))
    if not conditions:
        return []

    return (
        db.query(Entity)
        .options(*ENTITY_EAGER_LOAD_OPTIONS)
        .filter(Entity.register_type == RegisterType.CASP)
        .filter(or_(*conditions))
        .all()
    )


def _group_casp_entities(entities: List[Entity]) -> Dict[str, List[Entity]]:
    grouped: Dict[str, List[Entity]] = {}
    for entity in entities:
        grouped.setdefault(_casp_group_key(entity), []).append(entity)
    return grouped


def _sort_casp_company_payloads(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(
        items,
        key=lambda item: (
            -_date_ordinal(item.get("authorisation_notification_date")),
            (item.get("commercial_name") or item.get("lei_name") or "").lower(),
            item["id"],
        ),
    )


def _get_entity_sort_value(entity: Entity, sort_by: str) -> Any:
    if sort_by == "commercial_name":
        return _primary_display_name(entity.commercial_name, entity.lei_name)
    if sort_by == "home_member_state":
        return _effective_country_code(entity.home_member_state, entity.lei_cou_code)
    if sort_by == "website":
        return _normalize_url_sort_value(entity.website)
    if sort_by == "comments":
        return _normalize_reason_sort_value(entity.comments)
    if sort_by == "services":
        return _normalize_sequence_sort_value([service.code for service in entity.services or []])
    if sort_by == "passport_countries":
        return _normalize_sequence_sort_value([
            country.country_code for country in entity.passport_countries or []
        ])
    if sort_by == "white_paper_url":
        return _normalize_url_sort_value(entity.white_paper_url)
    if sort_by == "lei_casp":
        return _primary_display_name(entity.lei_name_casp, entity.lei_casp)
    if sort_by == "offer_countries":
        return _normalize_pipe_sort_value(entity.offer_countries)
    if sort_by == "dti_codes":
        return _normalize_pipe_sort_value(entity.dti_codes)
    if sort_by == "white_paper_comments":
        return _normalize_reason_sort_value(entity.white_paper_comments)
    if sort_by == "white_paper_offer_countries":
        return _normalize_pipe_sort_value(entity.white_paper_offer_countries)
    if sort_by == "authorisation_other_emt":
        return _normalize_text_sort_value(entity.authorisation_other_emt)
    if sort_by == "websites":
        return _normalize_pipe_sort_value(entity.websites)
    if sort_by == "reason":
        return _normalize_reason_sort_value(entity.reason)
    if sort_by in {"credit_institution", "exemption_48_4", "exemption_48_5"}:
        return _normalize_bool_sort_value(getattr(entity, sort_by))
    if sort_by in {
        "lei_name",
        "lei",
        "lei_cou_code",
        "competent_authority",
        "address",
        "last_update",
        "authorisation_notification_date",
        "authorisation_end_date",
        "lei_name_casp",
        "dti_ffg",
        "white_paper_notification_date",
        "infringement",
        "decision_date",
        "website_platform",
    }:
        value = getattr(entity, sort_by)
        if isinstance(value, date):
            return value
        return _normalize_text_sort_value(value)

    raise HTTPException(status_code=400, detail=f"Unsupported sort field: {sort_by}")


def _get_casp_company_sort_value(item: Dict[str, Any], sort_by: str) -> Any:
    if sort_by == "commercial_name":
        return _primary_display_name(item.get("commercial_name"), item.get("lei_name"))
    if sort_by == "home_member_state":
        return _effective_country_code(item.get("home_member_state"), item.get("lei_cou_code"))
    if sort_by == "website":
        return _normalize_url_sort_value(item.get("website"))
    if sort_by == "comments":
        return _normalize_reason_sort_value(item.get("comments"))
    if sort_by == "services":
        return _normalize_sequence_sort_value([
            service.get("code", "") for service in item.get("services") or []
        ])
    if sort_by == "passport_countries":
        return _normalize_sequence_sort_value([
            country.get("country_code", "") for country in item.get("passport_countries") or []
        ])
    if sort_by in {
        "lei_name",
        "lei",
        "lei_cou_code",
        "competent_authority",
        "address",
        "last_update",
        "authorisation_notification_date",
        "authorisation_end_date",
        "website_platform",
    }:
        value = item.get(sort_by)
        if isinstance(value, date):
            return value
        return _normalize_text_sort_value(value)

    raise HTTPException(status_code=400, detail=f"Unsupported sort field: {sort_by}")


def _sort_entities(items: List[Entity], sort_by: str, descending: bool) -> List[Entity]:
    return sorted(
        items,
        key=cmp_to_key(
            lambda left, right: _compare_sorted_items(
                left,
                right,
                _get_entity_sort_value(left, sort_by),
                _get_entity_sort_value(right, sort_by),
                descending,
            )
        ),
    )


def _sort_casp_company_payloads_dynamic(
    items: List[Dict[str, Any]],
    sort_by: str,
    descending: bool,
) -> List[Dict[str, Any]]:
    return sorted(
        items,
        key=cmp_to_key(
            lambda left, right: _compare_sorted_items(
                left,
                right,
                _get_casp_company_sort_value(left, sort_by),
                _get_casp_company_sort_value(right, sort_by),
                descending,
            )
        ),
    )


def _get_grouped_casp_companies(
    db: Session,
    home_member_states: Optional[List[str]] = None,
    service_codes: Optional[List[str]] = None,
    search: Optional[str] = None,
    auth_date_from: Optional[date] = None,
    auth_date_to: Optional[date] = None,
    sort_by: Optional[str] = None,
    descending: bool = False,
) -> List[Dict[str, Any]]:
    matching_rows = _apply_casp_row_filters(
        db.query(Entity).options(*ENTITY_EAGER_LOAD_OPTIONS).filter(Entity.register_type == RegisterType.CASP),
        home_member_states=home_member_states,
        service_codes=service_codes,
        search=search,
        auth_date_from=auth_date_from,
        auth_date_to=auth_date_to,
    ).all()

    if not matching_rows:
        return []

    full_group_rows = _load_all_rows_for_casp_groups(db, matching_rows)
    grouped = _group_casp_entities(full_group_rows)
    companies = [
        _build_casp_company_payload(group_rows)
        for group_rows in grouped.values()
    ]

    if sort_by:
        return _sort_casp_company_payloads_dynamic(companies, sort_by, descending)
    return _sort_casp_company_payloads(companies)


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
    sort_by: Optional[str] = Query(None),
    sort_dir: Optional[str] = Query(None),
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
    query = apply_home_member_state_filter(query, home_member_states)

    # Service codes filter - only applicable for CASP
    if service_codes and len(service_codes) > 0:
        if register_type == RegisterType.CASP:
            query = query.filter(Entity.id.in_(_get_casp_service_filter_subquery(service_codes)))
        # For other registers, ignore service_codes filter

    if search:
        query = apply_search_filter(query, search, register_type)

    if auth_date_from:
        query = query.filter(Entity.authorisation_notification_date >= auth_date_from)

    if auth_date_to:
        query = query.filter(Entity.authorisation_notification_date <= auth_date_to)

    parsed_sort_by, descending = _parse_sort_params(
        sort_by,
        sort_dir,
        REGISTER_SORT_FIELDS[register_type],
    )

    # Get total count before pagination
    total = query.count()

    if parsed_sort_by:
        entities = _sort_entities(query.all(), parsed_sort_by, descending)
        entities = entities[skip:skip + limit]
    else:
        # Preserve current default behavior when no explicit sort is requested.
        entities = query.offset(skip).limit(limit).all()

    # Return paginated response with metadata
    return PaginatedResponse(
        items=entities,
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + limit) < total
    )


@router.get("/casp/companies", response_model=PaginatedCaspCompanyResponse)
def get_casp_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    home_member_states: Optional[List[str]] = Query(None),
    service_codes: Optional[List[str]] = Query(None),
    search: Optional[str] = None,
    auth_date_from: Optional[date] = None,
    auth_date_to: Optional[date] = None,
    sort_by: Optional[str] = Query(None),
    sort_dir: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get grouped CASP companies with pagination metadata."""
    parsed_sort_by, descending = _parse_sort_params(
        sort_by,
        sort_dir,
        CASP_COMPANY_SORT_FIELDS,
    )
    companies = _get_grouped_casp_companies(
        db,
        home_member_states=home_member_states,
        service_codes=service_codes,
        search=search,
        auth_date_from=auth_date_from,
        auth_date_to=auth_date_to,
        sort_by=parsed_sort_by,
        descending=descending,
    )
    total = len(companies)
    paginated_items = companies[skip:skip + limit]
    return PaginatedCaspCompanyResponse(
        items=paginated_items,
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + limit) < total,
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
    query = apply_home_member_state_filter(query, home_member_states)

    # Service codes filter - only for CASP
    if service_codes and len(service_codes) > 0:
        if register_type == RegisterType.CASP:
            query = query.filter(Entity.id.in_(_get_casp_service_filter_subquery(service_codes)))

    if search:
        query = apply_search_filter(query, search, register_type)

    if auth_date_from:
        query = query.filter(Entity.authorisation_notification_date >= auth_date_from)

    if auth_date_to:
        query = query.filter(Entity.authorisation_notification_date <= auth_date_to)

    count = query.count()
    return {"count": count}


@router.get("/casp/companies/{entity_id}", response_model=CaspCompanyDetail)
def get_casp_company(entity_id: int, db: Session = Depends(get_db)):
    """Get grouped CASP company detail by any raw CASP entity id in the group."""
    entity = (
        db.query(Entity)
        .options(*ENTITY_EAGER_LOAD_OPTIONS)
        .filter(Entity.id == entity_id, Entity.register_type == RegisterType.CASP)
        .first()
    )
    if not entity:
        raise HTTPException(status_code=404, detail="CASP company not found")

    group_rows = _load_all_rows_for_casp_groups(db, [entity])
    return CaspCompanyDetail(**_build_casp_company_payload(group_rows))


@router.get("/metadata/last-updated", response_model=LastUpdatedResponse)
def get_last_updated(
    register_type: RegisterType = Query(RegisterType.CASP, description="Register type"),
    db: Session = Depends(get_db)
):
    """Get latest update date for a single register."""
    metadata = db.query(RegisterUpdateMetadata).filter(
        RegisterUpdateMetadata.register_type == register_type
    ).first()
    if metadata:
        return LastUpdatedResponse(
            register_type=register_type.value,
            last_updated=metadata.esma_update_date
        )

    # Backward-compatible fallback for environments without metadata records.
    if register_type in (RegisterType.CASP, RegisterType.NCASP):
        latest_update = db.query(func.max(Entity.last_update)).filter(
            Entity.register_type == register_type
        ).scalar()
    elif register_type == RegisterType.OTHER:
        latest_update = db.query(
            func.max(func.coalesce(OtherEntity.white_paper_last_update, Entity.last_update))
        ).select_from(Entity).outerjoin(
            OtherEntity, OtherEntity.id == Entity.id
        ).filter(
            Entity.register_type == register_type
        ).scalar()
    elif register_type == RegisterType.ART:
        latest_update = db.query(
            func.max(func.coalesce(ArtEntity.white_paper_last_update, Entity.last_update))
        ).select_from(Entity).outerjoin(
            ArtEntity, ArtEntity.id == Entity.id
        ).filter(
            Entity.register_type == register_type
        ).scalar()
    elif register_type == RegisterType.EMT:
        latest_update = db.query(
            func.max(func.coalesce(EmtEntity.white_paper_last_update, Entity.last_update))
        ).select_from(Entity).outerjoin(
            EmtEntity, EmtEntity.id == Entity.id
        ).filter(
            Entity.register_type == register_type
        ).scalar()
    else:
        latest_update = None

    return LastUpdatedResponse(register_type=register_type.value, last_updated=latest_update)


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
    effective_home_member_state = get_effective_home_member_state_expr().label("effective_home_member_state")

    authorities_data = db.query(
        effective_home_member_state,
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


@router.get("/casp/filters/counts")
def get_casp_filter_counts(
    home_member_states: Optional[List[str]] = Query(None),
    service_codes: Optional[List[str]] = Query(None),
    search: Optional[str] = None,
    auth_date_from: Optional[date] = None,
    auth_date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get grouped CASP filter counts using company-level totals."""
    mica_service_codes = {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'}
    country_counts: Dict[str, int] = {}
    service_counts = {code: 0 for code in sorted(mica_service_codes)}

    companies = _get_grouped_casp_companies(
        db,
        home_member_states=home_member_states,
        service_codes=service_codes,
        search=search,
        auth_date_from=auth_date_from,
        auth_date_to=auth_date_to,
    )

    for company in companies:
        country_code = (company.get("home_member_state") or company.get("lei_cou_code") or "").strip()
        if country_code:
            country_counts[country_code] = country_counts.get(country_code, 0) + 1

        service_codes_in_group = {
            service["code"]
            for service in company.get("services", [])
            if service["code"] in mica_service_codes
        }
        for code in service_codes_in_group:
            service_counts[code] = service_counts.get(code, 0) + 1

    return {
        "country_counts": country_counts,
        "service_counts": service_counts,
    }


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
    effective_home_member_state = get_effective_home_member_state_expr()

    country_query = db.query(
        effective_home_member_state.label("country_code"),
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
    country_query = country_query.group_by(effective_home_member_state)
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
        service_query = apply_home_member_state_filter(service_query, home_member_states)

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
def add_tag(
    entity_id: int,
    tag: TagCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_token),
):
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
def remove_tag(
    entity_id: int,
    tag_name: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_token),
):
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
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_token),
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
            detail="CSV file not found. Checked data/cleaned/ directory for CASP *_clean.csv files and fallback locations."
        )

    try:
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
