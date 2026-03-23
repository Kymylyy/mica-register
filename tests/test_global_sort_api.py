from datetime import date

from backend.app.config.registers import RegisterType
from backend.app.models import Entity, NcaspEntity


def test_grouped_casp_companies_sort_globally_before_pagination(client, db_with_casp_grouped_data):
    first_page = client.get(
        "/api/casp/companies?sort_by=authorisation_notification_date&sort_dir=asc&limit=1&skip=0"
    )
    second_page = client.get(
        "/api/casp/companies?sort_by=authorisation_notification_date&sort_dir=asc&limit=1&skip=1"
    )
    third_page = client.get(
        "/api/casp/companies?sort_by=authorisation_notification_date&sort_dir=asc&limit=1&skip=2"
    )

    assert first_page.status_code == 200
    assert second_page.status_code == 200
    assert third_page.status_code == 200

    assert first_page.json()["items"][0]["commercial_name"] == "Lux Digital Markets"
    assert second_page.json()["items"][0]["commercial_name"] == "Alpha Crypto France"
    assert third_page.json()["items"][0]["commercial_name"] == "EUWAX AG"


def test_other_entities_sort_globally_before_pagination(client, db_with_other_data):
    first_page = client.get("/api/entities?register_type=other&sort_by=lei_name&sort_dir=asc&limit=1&skip=0")
    second_page = client.get("/api/entities?register_type=other&sort_by=lei_name&sort_dir=asc&limit=1&skip=1")
    third_page = client.get("/api/entities?register_type=other&sort_by=lei_name&sort_dir=asc&limit=1&skip=2")

    assert first_page.status_code == 200
    assert second_page.status_code == 200
    assert third_page.status_code == 200

    assert first_page.json()["items"][0]["lei_name"] == "Circle Internet Financial"
    assert second_page.json()["items"][0]["lei_name"] == "Paxos Trust Company"
    assert third_page.json()["items"][0]["lei_name"] == "Tether Operations Limited"


def test_ncasp_date_sort_keeps_nulls_last_in_both_directions(client, db_with_ncasp_data, db_session):
    missing_date_entity = Entity(
        register_type=RegisterType.NCASP,
        competent_authority="ESMA",
        commercial_name="Missing Date Entity",
        last_update=date(2025, 1, 1),
    )
    missing_date_entity.ncasp_entity = NcaspEntity(
        websites="https://missing-date.example",
        infringement="YES",
        reason="No decision date yet",
        decision_date=None,
    )
    db_session.add(missing_date_entity)
    db_session.commit()

    ascending = client.get("/api/entities?register_type=ncasp&sort_by=decision_date&sort_dir=asc&limit=10")
    descending = client.get("/api/entities?register_type=ncasp&sort_by=decision_date&sort_dir=desc&limit=10")

    assert ascending.status_code == 200
    assert descending.status_code == 200

    ascending_items = ascending.json()["items"]
    descending_items = descending.json()["items"]

    assert ascending_items[0]["commercial_name"] == "Luxembourg Ponzi Scheme"
    assert ascending_items[-1]["commercial_name"] == "Missing Date Entity"
    assert descending_items[0]["commercial_name"] == "Crypto Scam Platform GmbH"
    assert descending_items[-1]["commercial_name"] == "Missing Date Entity"


def test_emt_supports_global_white_paper_notification_date_sort(client, db_with_emt_data):
    response = client.get(
        "/api/entities?register_type=emt&sort_by=white_paper_notification_date&sort_dir=desc&limit=10"
    )
    assert response.status_code == 200

    items = response.json()["items"]
    assert [item["commercial_name"] for item in items] == [
        "German E-Money Token",
        "French Digital Euro",
        "Lux E-Money Platform",
    ]


def test_art_accepts_sort_params_for_empty_result_set(client, db_session):
    response = client.get(
        "/api/entities?register_type=art&sort_by=authorisation_notification_date&sort_dir=asc&limit=10"
    )
    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["total"] == 0


def test_entities_reject_unsupported_sort_field(client, db_with_other_data):
    response = client.get("/api/entities?register_type=other&sort_by=not_a_field&sort_dir=asc")
    assert response.status_code == 400
    assert "Unsupported sort field" in response.json()["detail"]
