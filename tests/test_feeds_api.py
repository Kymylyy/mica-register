import csv
from io import StringIO

import pytest

import backend.app.routers.feeds as feeds


@pytest.fixture(autouse=True)
def reset_feed_runtime_state():
    feeds._feed_cache.clear()
    feeds._rate_limit_events.clear()
    yield
    feeds._feed_cache.clear()
    feeds._rate_limit_events.clear()


def test_feeds_index_exposes_docs_openapi_and_register_links(client):
    response = client.get("/api/feeds")
    assert response.status_code == 200

    payload = response.json()
    assert payload["docs_url"].endswith("/docs")
    assert payload["openapi_url"].endswith("/openapi.json")

    for register in ("casp", "other", "art", "emt", "ncasp"):
        assert payload["feeds"][register]["json"].endswith(f"/api/feeds/{register}.json")
        assert payload["feeds"][register]["csv"].endswith(f"/api/feeds/{register}.csv")


def test_json_feed_returns_register_data_with_cache_headers(client, db_with_casp_data):
    response = client.get("/api/feeds/casp.json")
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
    assert "etag" in response.headers
    assert response.headers.get("cache-control") == "public, max-age=300"
    assert response.headers.get("x-feed-cache") == "miss"

    payload = response.json()
    assert payload["register_type"] == "casp"
    assert payload["count"] == len(payload["items"])
    assert payload["count"] > 0
    assert all(item["register_type"] == "casp" for item in payload["items"])

    second_response = client.get("/api/feeds/casp.json")
    assert second_response.status_code == 200
    assert second_response.headers.get("x-feed-cache") == "hit"

    not_modified_response = client.get(
        "/api/feeds/casp.json",
        headers={"If-None-Match": response.headers["etag"]},
    )
    assert not_modified_response.status_code == 304


def test_csv_feed_returns_flattened_rows_with_metadata(client, db_with_casp_data):
    response = client.get("/api/feeds/casp.csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == 'attachment; filename="mica-register-casp.csv"'
    assert "etag" in response.headers

    csv_rows = list(csv.DictReader(StringIO(response.text)))
    assert len(csv_rows) > 0
    assert all(row["register_type"] == "casp" for row in csv_rows)
    assert any(row["services"] for row in csv_rows)

    not_modified_response = client.get(
        "/api/feeds/casp.csv",
        headers={"If-None-Match": response.headers["etag"]},
    )
    assert not_modified_response.status_code == 304


def test_feed_rate_limit_returns_429_when_threshold_exceeded(client, db_with_casp_data):
    for _ in range(feeds.FEED_RATE_LIMIT_REQUESTS):
        response = client.get("/api/feeds/casp.json")
        assert response.status_code == 200

    limited_response = client.get("/api/feeds/casp.json")
    assert limited_response.status_code == 429
