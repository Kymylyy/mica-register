def test_grouped_companies_list_returns_one_company_per_lei(client, db_with_casp_grouped_data):
    response = client.get("/api/casp/companies?limit=10")
    assert response.status_code == 200

    payload = response.json()
    assert payload["total"] == 3
    assert len(payload["items"]) == 3

    euwax = next(item for item in payload["items"] if item["lei"] == "529900032TYR45XIEW79")
    assert euwax["record_count"] == 2
    assert euwax["authorisation_notification_date"] == "2025-11-21"
    assert sorted(service["code"] for service in euwax["services"]) == ["c", "d", "e"]
    assert sorted(country["country_code"] for country in euwax["passport_countries"]) == [
        "AT", "DE", "ES", "FR", "GR", "IT", "SI", "SK"
    ]


def test_grouped_companies_detail_returns_all_authorisation_records_for_any_group_member(client, db_with_casp_grouped_data):
    raw_response = client.get("/api/entities?register_type=casp&limit=10")
    assert raw_response.status_code == 200
    raw_items = raw_response.json()["items"]

    euwax_rows = [item for item in raw_items if item["lei"] == "529900032TYR45XIEW79"]
    assert len(euwax_rows) == 2

    canonical_id = max(item["id"] for item in euwax_rows)
    sibling_id = min(item["id"] for item in euwax_rows)

    response = client.get(f"/api/casp/companies/{sibling_id}")
    assert response.status_code == 200

    company = response.json()
    assert company["id"] == canonical_id
    assert company["record_count"] == 2
    assert [record["entity_id"] for record in company["authorisation_records"]] == [sibling_id, canonical_id]
    assert company["authorisation_records"][0]["authorisation_notification_date"] == "2025-04-01"
    assert company["authorisation_records"][1]["authorisation_notification_date"] == "2025-11-21"


def test_grouped_companies_filters_use_any_authorisation_semantics(client, db_with_casp_grouped_data):
    response = client.get("/api/casp/companies?service_codes=h")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["lei"] == "11111111111111111111"
    assert payload["items"][0]["record_count"] == 2

    response = client.get("/api/casp/companies?auth_date_from=2025-11-01")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["lei"] == "529900032TYR45XIEW79"


def test_grouped_companies_filter_counts_count_companies_not_raw_rows(client, db_with_casp_grouped_data):
    response = client.get("/api/casp/filters/counts")
    assert response.status_code == 200
    payload = response.json()

    assert payload["country_counts"] == {"DE": 1, "FR": 1, "LU": 1}
    assert payload["service_counts"]["a"] == 2
    assert payload["service_counts"]["e"] == 1
    assert payload["service_counts"]["h"] == 1


def test_grouped_companies_service_counts_respect_current_selection_with_any_authorisation(client, db_with_casp_grouped_data):
    response = client.get("/api/casp/filters/counts?service_codes=e")
    assert response.status_code == 200
    payload = response.json()

    assert payload["country_counts"] == {"DE": 1}
    assert payload["service_counts"]["c"] == 1
    assert payload["service_counts"]["d"] == 1
    assert payload["service_counts"]["e"] == 1
    assert payload["service_counts"]["a"] == 0


def test_raw_generic_casp_endpoints_remain_unchanged(client, db_with_casp_grouped_data):
    response = client.get("/api/entities?register_type=casp&limit=10")
    assert response.status_code == 200
    payload = response.json()

    assert payload["total"] == 5
    assert len(payload["items"]) == 5

    count_response = client.get("/api/entities/count?register_type=casp")
    assert count_response.status_code == 200
    assert count_response.json() == {"count": 5}
