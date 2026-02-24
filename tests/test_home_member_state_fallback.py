"""Regression tests for home member state fallback filtering."""

from backend.app.config.registers import RegisterType
from backend.app.models import Entity


def _add_casp_entity(
    db_session,
    *,
    lei: str,
    home_member_state: str | None,
    lei_cou_code: str | None,
    commercial_name: str,
    authority: str,
) -> None:
    entity = Entity(
        register_type=RegisterType.CASP,
        competent_authority=authority,
        home_member_state=home_member_state,
        lei_name=f"{commercial_name} Legal Name",
        lei=lei,
        lei_cou_code=lei_cou_code,
        commercial_name=commercial_name,
    )
    db_session.add(entity)


def test_entities_filter_uses_lei_country_fallback(client, db_session):
    """Entity list and count endpoints should include LEI country fallback."""
    _add_casp_entity(
        db_session,
        lei="LEI-FALLBACK-AT-0001",
        home_member_state="",
        lei_cou_code="AT",
        commercial_name="Cryptonow Fallback",
        authority="Austrian Financial Market Authority (FMA)",
    )
    _add_casp_entity(
        db_session,
        lei="LEI-DIRECT-AT-0002",
        home_member_state="AT",
        lei_cou_code="AT",
        commercial_name="Direct Austria",
        authority="Austrian Financial Market Authority (FMA)",
    )
    db_session.commit()

    entities_response = client.get("/api/entities?register_type=casp&home_member_states=AT&limit=100")
    assert entities_response.status_code == 200
    entities_payload = entities_response.json()
    assert entities_payload["total"] == 2
    returned_leis = {item["lei"] for item in entities_payload["items"]}
    assert returned_leis == {"LEI-FALLBACK-AT-0001", "LEI-DIRECT-AT-0002"}

    count_response = client.get("/api/entities/count?register_type=casp&home_member_states=AT")
    assert count_response.status_code == 200
    assert count_response.json()["count"] == 2


def test_filter_options_and_counts_include_lei_country_fallback(client, db_session):
    """Filter metadata should expose countries coming from LEI fallback."""
    _add_casp_entity(
        db_session,
        lei="LEI-FALLBACK-AT-1001",
        home_member_state="",
        lei_cou_code="AT",
        commercial_name="Fallback Austria Only",
        authority="Austrian Financial Market Authority (FMA)",
    )
    _add_casp_entity(
        db_session,
        lei="LEI-DIRECT-DE-1002",
        home_member_state="DE",
        lei_cou_code="DE",
        commercial_name="Direct Germany",
        authority="Bundesanstalt fuer Finanzdienstleistungsaufsicht (BaFin)",
    )
    db_session.commit()

    options_response = client.get("/api/filters/options?register_type=casp")
    assert options_response.status_code == 200
    options_payload = options_response.json()
    country_codes = {country["country_code"] for country in options_payload["home_member_states"]}
    assert "AT" in country_codes

    counts_response = client.get("/api/filters/counts?register_type=casp")
    assert counts_response.status_code == 200
    country_counts = counts_response.json()["country_counts"]
    assert country_counts["AT"] == 1
    assert "" not in country_counts
