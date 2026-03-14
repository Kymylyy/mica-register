import importlib

from backend.app.models import Entity


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_entity_write_endpoints_require_authorization_header(client, db_with_casp_data):
    entity_id = db_with_casp_data.query(Entity).first().id

    patch_response = client.patch(f"/api/entities/{entity_id}", json={"comments": "Updated"})
    add_tag_response = client.post(
        f"/api/entities/{entity_id}/tags",
        json={"tag_name": "reviewed", "tag_value": "yes"},
    )
    delete_tag_response = client.delete(f"/api/entities/{entity_id}/tags/reviewed")

    assert patch_response.status_code == 401
    assert patch_response.json()["detail"] == "Missing Authorization header"
    assert add_tag_response.status_code == 401
    assert add_tag_response.json()["detail"] == "Missing Authorization header"
    assert delete_tag_response.status_code == 401
    assert delete_tag_response.json()["detail"] == "Missing Authorization header"


def test_entity_write_endpoints_reject_invalid_token(client, db_with_casp_data, monkeypatch):
    monkeypatch.setenv("ADMIN_API_TOKEN", "expected-token")
    entity_id = db_with_casp_data.query(Entity).first().id
    headers = _auth_header("wrong-token")

    patch_response = client.patch(f"/api/entities/{entity_id}", json={"comments": "Updated"}, headers=headers)
    add_tag_response = client.post(
        f"/api/entities/{entity_id}/tags",
        json={"tag_name": "reviewed", "tag_value": "yes"},
        headers=headers,
    )
    delete_tag_response = client.delete(f"/api/entities/{entity_id}/tags/reviewed", headers=headers)

    assert patch_response.status_code == 401
    assert patch_response.json()["detail"] == "Invalid admin token"
    assert add_tag_response.status_code == 401
    assert add_tag_response.json()["detail"] == "Invalid admin token"
    assert delete_tag_response.status_code == 401
    assert delete_tag_response.json()["detail"] == "Invalid admin token"


def test_entity_write_endpoints_return_503_when_token_is_not_configured(client, db_with_casp_data, monkeypatch):
    monkeypatch.delenv("ADMIN_API_TOKEN", raising=False)
    monkeypatch.delenv("ADMIN_TOKEN", raising=False)
    entity_id = db_with_casp_data.query(Entity).first().id

    response = client.patch(
        f"/api/entities/{entity_id}",
        json={"comments": "Updated"},
        headers=_auth_header("any-token"),
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Admin API token is not configured"


def test_entity_write_endpoints_succeed_with_valid_token(client, db_with_casp_data, monkeypatch):
    monkeypatch.setenv("ADMIN_API_TOKEN", "expected-token")
    entity = db_with_casp_data.query(Entity).first()
    headers = _auth_header("expected-token")

    patch_response = client.patch(
        f"/api/entities/{entity.id}",
        json={"comments": "Updated via API"},
        headers=headers,
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["comments"] == "Updated via API"

    add_tag_response = client.post(
        f"/api/entities/{entity.id}/tags",
        json={"tag_name": "reviewed", "tag_value": "yes"},
        headers=headers,
    )
    assert add_tag_response.status_code == 200
    assert add_tag_response.json()["tag_name"] == "reviewed"

    refreshed_entity = client.get(f"/api/entities/{entity.id}")
    assert refreshed_entity.status_code == 200
    assert any(tag["tag_name"] == "reviewed" for tag in refreshed_entity.json()["tags"])

    delete_tag_response = client.delete(f"/api/entities/{entity.id}/tags/reviewed", headers=headers)
    assert delete_tag_response.status_code == 200
    assert delete_tag_response.json()["message"] == "Tag removed"

    refreshed_entity = client.get(f"/api/entities/{entity.id}")
    assert refreshed_entity.status_code == 200
    assert all(tag["tag_name"] != "reviewed" for tag in refreshed_entity.json()["tags"])


def test_app_startup_does_not_create_tables_implicitly(monkeypatch):
    import backend.app.database as database_module
    import backend.app.main as main_module

    def fail_create_all(*args, **kwargs):
        raise AssertionError("create_all should not run during app startup")

    monkeypatch.setattr(database_module.Base.metadata, "create_all", fail_create_all)

    reloaded = importlib.reload(main_module)

    assert reloaded.app.title == "MiCA Register API"


def test_admin_import_endpoints_do_not_call_create_all(client, monkeypatch):
    import backend.app.database as database_module
    import backend.app.import_csv as import_csv_module

    monkeypatch.setenv("ADMIN_API_TOKEN", "expected-token")

    def fail_create_all(*args, **kwargs):
        raise AssertionError("create_all should not run in admin import endpoints")

    monkeypatch.setattr(database_module.Base.metadata, "create_all", fail_create_all)
    monkeypatch.setattr(
        import_csv_module,
        "import_csv_to_db",
        lambda *args, **kwargs: None,
    )

    import_all_response = client.post("/api/admin/import-all", headers=_auth_header("expected-token"))
    import_response = client.post("/api/admin/import", headers=_auth_header("expected-token"))

    assert import_all_response.status_code == 200
    assert import_all_response.json()["message"] == "All registers imported successfully"
    assert import_response.status_code == 200
    assert import_response.json()["message"] == "Data imported successfully"
