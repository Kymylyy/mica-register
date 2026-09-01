"""API access-log middleware: real client IP, UA and origin for /api/* and /docs."""


def test_api_request_logs_client_details(client, db_with_casp_data, capsys):
    response = client.get(
        "/api/entities?register_type=casp&limit=1",
        headers={
            "X-Forwarded-For": "52.89.191.177, 100.64.0.2",
            "User-Agent": "python-requests/2.31",
            "Origin": "https://example.com",
        },
    )
    assert response.status_code == 200

    log = capsys.readouterr().out
    assert "ACCESS 200 GET /api/entities?register_type=casp&limit=1" in log
    assert "ip=52.89.191.177" in log  # first X-Forwarded-For entry, proxy stripped
    assert 'ua="python-requests/2.31"' in log
    assert "origin=https://example.com" in log


def test_api_request_without_headers_logs_placeholders(client, db_with_casp_data, capsys):
    response = client.get("/api/entities?register_type=casp&limit=1")
    assert response.status_code == 200

    log = capsys.readouterr().out
    assert "ACCESS 200 GET /api/entities" in log
    assert "origin=- " in log


def test_non_api_paths_are_not_access_logged(client, capsys):
    response = client.get("/")
    assert response.status_code == 200
    assert "ACCESS" not in capsys.readouterr().out
