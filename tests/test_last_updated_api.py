"""Tests for GET /api/metadata/last-updated."""

from datetime import date

import pytest

from backend.app.config.registers import RegisterType
from backend.app.models import ArtEntity, EmtEntity, Entity, OtherEntity, RegisterUpdateMetadata


def _create_entity(db_session, register_type: RegisterType, last_update: date | None = None) -> Entity:
    entity = Entity(
        register_type=register_type,
        competent_authority="Authority",
        home_member_state="PL",
        lei_name=f"{register_type.value.upper()} LEI Name",
        lei=f"LEI-{register_type.value}",
        last_update=last_update,
    )
    db_session.add(entity)
    db_session.flush()
    return entity


@pytest.mark.parametrize(
    "register_type, expected_date",
    [
        (RegisterType.CASP, date(2026, 2, 1)),
        (RegisterType.NCASP, date(2026, 2, 2)),
        (RegisterType.OTHER, date(2026, 2, 3)),
        (RegisterType.ART, date(2026, 2, 4)),
        (RegisterType.EMT, date(2026, 2, 5)),
    ],
)
def test_last_updated_returns_expected_per_register(client, db_session, register_type, expected_date):
    entity = _create_entity(db_session, register_type, last_update=date(2026, 1, 1))

    if register_type == RegisterType.OTHER:
        db_session.add(OtherEntity(id=entity.id, white_paper_last_update=expected_date))
    elif register_type == RegisterType.ART:
        db_session.add(ArtEntity(id=entity.id, white_paper_last_update=expected_date))
    elif register_type == RegisterType.EMT:
        db_session.add(EmtEntity(id=entity.id, white_paper_last_update=expected_date))
    else:
        entity.last_update = expected_date

    db_session.commit()

    response = client.get(f"/api/metadata/last-updated?register_type={register_type.value}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["register_type"] == register_type.value
    assert payload["last_updated"] == expected_date.isoformat()


def test_last_updated_returns_null_when_register_has_no_data(client):
    response = client.get("/api/metadata/last-updated?register_type=art")
    assert response.status_code == 200
    payload = response.json()
    assert payload["register_type"] == "art"
    assert payload["last_updated"] is None


def test_last_updated_prefers_esma_metadata_over_entity_dates(client, db_session):
    entity = _create_entity(db_session, RegisterType.NCASP, last_update=date(2025, 12, 16))
    db_session.add(RegisterUpdateMetadata(
        register_type=RegisterType.NCASP,
        esma_update_date=date(2026, 2, 8)
    ))
    db_session.commit()

    response = client.get("/api/metadata/last-updated?register_type=ncasp")
    assert response.status_code == 200
    payload = response.json()
    assert payload["register_type"] == "ncasp"
    assert payload["last_updated"] == "2026-02-08"
