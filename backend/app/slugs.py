"""
Stable URL slugs for register entities.

Slugs are assigned once per natural identity and persisted in the
entity_slugs registry, which survives register re-imports. The import
(import_csv.py) computes an identity key per row, then assign_slugs()
reuses the registered slug or mints a new one.

Identity keys per register:
- casp:        lei                       (one slug per company; rows share it)
- art / emt:   lei + white_paper_url     (one slug per issuer filing)
- other:       lei/lei_name + white_paper_url  (one slug per white paper)
- ncasp:       lei, else lei_name + home_member_state, else websites

Collision policy (deterministic, first-come-wins, persisted):
base name -> base-{country} -> base-{6-char identity hash} -> base-2, base-3...
"""

import hashlib
import re
import unicodedata

from sqlalchemy.orm import Session

from .models import EntitySlug

MAX_SLUG_LENGTH = 80

# Characters with no NFKD decomposition that would otherwise be dropped
_CHAR_MAP = str.maketrans({
    "ł": "l", "Ł": "L", "ø": "o", "Ø": "O", "đ": "d", "Đ": "D",
    "ß": "ss", "æ": "ae", "Æ": "AE", "œ": "oe", "Œ": "OE",
    "þ": "th", "Þ": "Th", "ð": "d", "Ð": "D",
})


def slugify(value):
    """Normalize a display name into a URL slug ('Bitpanda GmbH' -> 'bitpanda-gmbh')."""
    if not value:
        return ""
    value = str(value).translate(_CHAR_MAP)
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    value = re.sub(r"-{2,}", "-", value)
    return value[:MAX_SLUG_LENGTH].rstrip("-")


def _short_hash(value):
    return hashlib.sha1((value or "").encode("utf-8")).hexdigest()[:6]


def compute_identity_key(register_type_value, lei=None, lei_name=None,
                         home_member_state=None, white_paper_url=None, websites=None):
    """Deterministic natural-identity key for a register row (see module docstring)."""
    register_type_value = (register_type_value or "").lower()
    lei = (lei or "").strip().upper()
    name = (lei_name or "").strip().lower()

    if register_type_value == "casp":
        return f"lei:{lei}"
    if register_type_value in ("art", "emt"):
        return f"lei:{lei}|wp:{_short_hash(white_paper_url)}"
    if register_type_value == "other":
        base = f"lei:{lei}" if lei else f"name:{name}"
        return f"{base}|wp:{_short_hash(white_paper_url)}"
    if register_type_value == "ncasp":
        if lei:
            return f"lei:{lei}"
        if name:
            return f"name:{name}|st:{(home_member_state or '').upper()}"
        return f"web:{_short_hash(websites)}"
    raise ValueError(f"Unknown register_type: {register_type_value}")


def assign_slugs(db: Session, register_type_value, pending):
    """Assign stable slugs to freshly imported entities.

    Args:
        db: session (same transaction as the import)
        register_type_value: lowercase register string ('casp', ...)
        pending: list of (entity, identity_key, display_name, country_code)

    Reuses slugs from the entity_slugs registry; new identities get a slug
    minted from display_name with deterministic collision suffixes.
    """
    register_type_value = (register_type_value or "").lower()
    registry = db.query(EntitySlug).filter(
        EntitySlug.register_type == register_type_value
    ).all()
    slug_by_identity = {row.identity_key: row.slug for row in registry}
    used_slugs = set(slug_by_identity.values())

    for entity, identity_key, display_name, country_code in pending:
        slug = slug_by_identity.get(identity_key)
        if slug is None:
            slug = _mint_slug(display_name, country_code, identity_key,
                              register_type_value, used_slugs)
            used_slugs.add(slug)
            slug_by_identity[identity_key] = slug
            db.add(EntitySlug(
                register_type=register_type_value,
                identity_key=identity_key,
                slug=slug,
            ))
        entity.slug = slug


def _mint_slug(display_name, country_code, identity_key, register_type_value, used_slugs):
    base = slugify(display_name)
    if not base:
        base = f"{register_type_value}-{_short_hash(identity_key)}"

    candidates = [base]
    country = slugify(country_code) if country_code else ""
    if country:
        candidates.append(f"{base}-{country}")
    candidates.append(f"{base}-{_short_hash(identity_key)}")

    for candidate in candidates:
        if candidate not in used_slugs:
            return candidate

    counter = 2
    while f"{base}-{counter}" in used_slugs:
        counter += 1
    return f"{base}-{counter}"
