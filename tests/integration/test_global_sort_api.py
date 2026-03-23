import pytest


@pytest.mark.parametrize(
    "fixture_name, url, query, expected_key, expected_value",
    [
        (
            "db_with_casp_data",
            "/api/entities",
            "register_type=casp&sort_by=authorisation_notification_date&sort_dir=asc&limit=1",
            "authorisation_notification_date",
            "2023-03-10",
        ),
        (
            "db_with_other_data",
            "/api/entities",
            "register_type=other&sort_by=white_paper_url&sort_dir=asc&limit=1",
            "white_paper_url",
            "https://circle.com/usdc",
        ),
        (
            "db_with_emt_data",
            "/api/entities",
            "register_type=emt&sort_by=white_paper_notification_date&sort_dir=desc&limit=1",
            "white_paper_notification_date",
            "2024-12-15",
        ),
        (
            "db_with_art_data",
            "/api/entities",
            "register_type=art&sort_by=authorisation_end_date&sort_dir=asc&limit=3",
            "authorisation_end_date",
            "2026-12-31",
        ),
        (
            "db_with_ncasp_data",
            "/api/entities",
            "register_type=ncasp&sort_by=decision_date&sort_dir=asc&limit=1",
            "decision_date",
            "2023-03-10",
        ),
    ],
)
def test_entities_list_supports_global_sort_before_pagination(
    client,
    request,
    fixture_name,
    url,
    query,
    expected_key,
    expected_value,
):
    request.getfixturevalue(fixture_name)

    response = client.get(f"{url}?{query}")
    assert response.status_code == 200

    payload = response.json()
    assert payload["items"], payload

    first_item = payload["items"][0]
    assert first_item[expected_key] == expected_value

    if fixture_name == "db_with_art_data":
        assert payload["items"][-1]["authorisation_end_date"] is None


def test_grouped_casp_companies_keep_default_sort_when_no_explicit_sort_is_requested(
    client,
    db_with_casp_grouped_data,
):
    response = client.get("/api/casp/companies?limit=1")
    assert response.status_code == 200

    payload = response.json()
    assert payload["total"] == 3
    assert payload["items"][0]["lei"] == "529900032TYR45XIEW79"
    assert payload["items"][0]["authorisation_notification_date"] == "2025-11-21"


def test_grouped_casp_companies_sort_globally_before_pagination(
    client,
    db_with_casp_grouped_data,
):
    response = client.get(
        "/api/casp/companies?sort_by=authorisation_notification_date&sort_dir=asc&limit=1"
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["total"] == 3
    assert payload["items"][0]["lei"] == "22222222222222222222"
    assert payload["items"][0]["authorisation_notification_date"] == "2024-02-20"

    next_page = client.get(
        "/api/casp/companies?sort_by=authorisation_notification_date&sort_dir=asc&skip=1&limit=1"
    )
    assert next_page.status_code == 200
    assert next_page.json()["items"][0]["lei"] == "11111111111111111111"


def test_entities_reject_unsupported_sort_field(client, db_with_other_data):
    response = client.get("/api/entities?register_type=other&sort_by=bogus&limit=1")
    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported sort field: bogus"
