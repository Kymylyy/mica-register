import csv
import hashlib
import json
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
from typing import Any
from threading import Lock

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session, selectinload

from ..config.registers import RegisterType
from ..database import get_db
from ..models import (
    ArtEntity,
    CaspEntity,
    EmtEntity,
    Entity,
    NcaspEntity,
    OtherEntity,
)
from ..schemas import Entity as EntitySchema

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

CSV_COLUMNS = [
    "id",
    "register_type",
    "competent_authority",
    "home_member_state",
    "lei_name",
    "lei",
    "lei_cou_code",
    "commercial_name",
    "address",
    "website",
    "authorisation_notification_date",
    "last_update",
    "comments",
    "website_platform",
    "authorisation_end_date",
    "white_paper_url",
    "white_paper_comments",
    "white_paper_last_update",
    "lei_casp",
    "lei_name_casp",
    "offer_countries",
    "dti_codes",
    "dti_ffg",
    "credit_institution",
    "white_paper_notification_date",
    "white_paper_offer_countries",
    "exemption_48_4",
    "exemption_48_5",
    "authorisation_other_emt",
    "websites",
    "infringement",
    "reason",
    "decision_date",
    "services",
    "passport_countries",
    "tags",
]

FEED_CACHE_TTL_SECONDS = 300
FEED_RATE_LIMIT_WINDOW_SECONDS = 60
FEED_RATE_LIMIT_REQUESTS = 30


@dataclass
class FeedCacheEntry:
    payload: dict[str, Any]
    csv_content: str
    json_etag: str
    csv_etag: str
    expires_at: float


_feed_cache: dict[str, FeedCacheEntry] = {}
_feed_cache_lock = Lock()
_rate_limit_events: dict[str, deque[float]] = {}
_rate_limit_lock = Lock()


def _iso_now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _serialize_entity(entity: Entity) -> dict[str, Any]:
    return EntitySchema.model_validate(entity).model_dump(mode="json")


def _build_feed_payload(register_type: RegisterType, entities: list[Entity]) -> dict[str, Any]:
    items = [_serialize_entity(entity) for entity in entities]
    return {
        "register_type": register_type.value,
        "count": len(items),
        "generated_at": _iso_now_utc(),
        "items": items,
    }


def _build_csv_content(items: list[dict[str, Any]]) -> str:
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    for item in items:
        writer.writerow(_entity_to_csv_row(item))
    return output.getvalue()


def _format_csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _entity_to_csv_row(entity_data: dict[str, Any]) -> dict[str, str]:
    row: dict[str, str] = {column: "" for column in CSV_COLUMNS}

    for column in CSV_COLUMNS:
        if column in {"services", "passport_countries", "tags"}:
            continue
        row[column] = _format_csv_value(entity_data.get(column))

    services = entity_data.get("services") or []
    row["services"] = "|".join(
        service.get("code", "")
        for service in services
        if isinstance(service, dict) and service.get("code")
    )

    passport_countries = entity_data.get("passport_countries") or []
    row["passport_countries"] = "|".join(
        country.get("country_code", "")
        for country in passport_countries
        if isinstance(country, dict) and country.get("country_code")
    )

    tags = entity_data.get("tags") or []
    row["tags"] = "|".join(
        f"{tag.get('tag_name', '')}:{tag.get('tag_value', '')}"
        for tag in tags
        if isinstance(tag, dict) and tag.get("tag_name")
    )
    return row


def _fetch_register_entities(db: Session, register_type: RegisterType) -> list[Entity]:
    return (
        db.query(Entity)
        .options(*ENTITY_EAGER_LOAD_OPTIONS)
        .filter(Entity.register_type == register_type)
        .order_by(Entity.id.asc())
        .all()
    )


def _make_etag(content: str) -> str:
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return f"\"{digest}\""


def _is_not_modified(if_none_match: str | None, expected_etag: str) -> bool:
    if not if_none_match:
        return False

    if if_none_match.strip() == "*":
        return True

    for raw_tag in if_none_match.split(","):
        candidate = raw_tag.strip()
        if candidate.startswith("W/"):
            candidate = candidate[2:].strip()
        if candidate == expected_etag:
            return True
    return False


def _feed_response_headers(etag: str, cache_hit: bool) -> dict[str, str]:
    return {
        "ETag": etag,
        "Cache-Control": f"public, max-age={FEED_CACHE_TTL_SECONDS}",
        "X-Feed-Cache": "hit" if cache_hit else "miss",
    }


def _build_feed_cache_entry(register_type: RegisterType, entities: list[Entity]) -> FeedCacheEntry:
    payload = _build_feed_payload(register_type, entities)
    json_content = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    csv_content = _build_csv_content(payload["items"])

    return FeedCacheEntry(
        payload=payload,
        csv_content=csv_content,
        json_etag=_make_etag(json_content),
        csv_etag=_make_etag(csv_content),
        expires_at=time.time() + FEED_CACHE_TTL_SECONDS,
    )


def _get_or_build_feed_cache_entry(
    db: Session,
    register_type: RegisterType,
) -> tuple[FeedCacheEntry, bool]:
    cache_key = register_type.value
    now = time.time()

    with _feed_cache_lock:
        cached = _feed_cache.get(cache_key)
        if cached and cached.expires_at > now:
            return cached, True

    entities = _fetch_register_entities(db, register_type)
    fresh_entry = _build_feed_cache_entry(register_type, entities)

    with _feed_cache_lock:
        _feed_cache[cache_key] = fresh_entry

    return fresh_entry, False


def _get_request_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _enforce_feed_rate_limit(request: Request) -> None:
    client_ip = _get_request_ip(request)
    now = time.monotonic()

    with _rate_limit_lock:
        bucket = _rate_limit_events.setdefault(client_ip, deque())
        cutoff = now - FEED_RATE_LIMIT_WINDOW_SECONDS
        while bucket and bucket[0] < cutoff:
            bucket.popleft()

        if len(bucket) >= FEED_RATE_LIMIT_REQUESTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Feed rate limit exceeded: "
                    f"{FEED_RATE_LIMIT_REQUESTS} requests per {FEED_RATE_LIMIT_WINDOW_SECONDS} seconds"
                ),
            )

        bucket.append(now)


@router.get("/feeds")
def get_feeds_index(request: Request):
    """Discover feed endpoints, docs, and OpenAPI on the current API host."""
    base_url = str(request.base_url).rstrip("/")

    register_feeds = {
        register_type.value: {
            "json": f"{base_url}/api/feeds/{register_type.value}.json",
            "csv": f"{base_url}/api/feeds/{register_type.value}.csv",
        }
        for register_type in RegisterType
    }

    return {
        "docs_url": f"{base_url}/docs",
        "openapi_url": f"{base_url}/openapi.json",
        "feeds": register_feeds,
    }


@router.get("/feeds/{register_type}.json")
def get_register_feed_json(
    request: Request,
    register_type: RegisterType,
    db: Session = Depends(get_db),
):
    """Public JSON feed for a single register."""
    _enforce_feed_rate_limit(request)

    cache_entry, cache_hit = _get_or_build_feed_cache_entry(db, register_type)
    headers = _feed_response_headers(cache_entry.json_etag, cache_hit)

    if _is_not_modified(request.headers.get("if-none-match"), cache_entry.json_etag):
        return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers=headers)

    return JSONResponse(content=cache_entry.payload, headers=headers)


@router.get("/feeds/{register_type}.csv")
def get_register_feed_csv(
    request: Request,
    register_type: RegisterType,
    db: Session = Depends(get_db),
):
    """Public CSV feed for a single register."""
    _enforce_feed_rate_limit(request)

    cache_entry, cache_hit = _get_or_build_feed_cache_entry(db, register_type)
    headers = _feed_response_headers(cache_entry.csv_etag, cache_hit)
    filename = f"mica-register-{register_type.value}.csv"

    if _is_not_modified(request.headers.get("if-none-match"), cache_entry.csv_etag):
        headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers=headers)

    headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return Response(
        content=cache_entry.csv_content,
        media_type="text/csv; charset=utf-8",
        headers=headers,
    )
