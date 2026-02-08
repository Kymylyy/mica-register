def test_admin_import_requires_authorization_header(client):
    response = client.post("/api/admin/import")
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing Authorization header"


def test_admin_import_all_rejects_invalid_token(client, monkeypatch):
    monkeypatch.setenv("ADMIN_API_TOKEN", "expected-token")
    response = client.post(
        "/api/admin/import-all",
        headers={"Authorization": "Bearer wrong-token"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid admin token"
