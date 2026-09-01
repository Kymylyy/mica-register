"""Stable URL slugs: generation, persistence across re-imports, API lookup."""

from backend.app.import_csv import import_csv_to_db
from backend.app.models import Entity, EntitySlug
from backend.app.slugs import compute_identity_key, slugify
from backend.app.config.registers import RegisterType


# --- unit: slugify ---

def test_slugify_normalizes_names():
    assert slugify("Bitpanda Asset Management GmbH") == "bitpanda-asset-management-gmbh"
    assert slugify("Zażółć  S.A.") == "zazolc-s-a"
    assert slugify("  --  ") == ""
    assert slugify(None) == ""


def test_identity_key_per_register():
    assert compute_identity_key("casp", lei="ABC") == "lei:ABC"
    assert compute_identity_key("casp", lei="abc") == "lei:ABC"
    art_a = compute_identity_key("art", lei="ABC", white_paper_url="https://x/wp1")
    art_b = compute_identity_key("art", lei="ABC", white_paper_url="https://x/wp2")
    assert art_a != art_b
    ncasp_lei = compute_identity_key("ncasp", lei="ABC")
    ncasp_name = compute_identity_key("ncasp", lei_name="Scam Co", home_member_state="DE")
    ncasp_web = compute_identity_key("ncasp", websites="scam.example")
    assert len({ncasp_lei, ncasp_name, ncasp_web}) == 3


# --- integration: import assigns slugs ---

def test_import_assigns_slugs_and_casp_lei_group_shares_one(db_with_casp_grouped_data):
    db = db_with_casp_grouped_data
    entities = db.query(Entity).filter(Entity.register_type == RegisterType.CASP).all()
    assert entities
    assert all(entity.slug for entity in entities)

    euwax_slugs = {e.slug for e in entities if e.lei == "529900032TYR45XIEW79"}
    assert len(euwax_slugs) == 1


def test_slugs_survive_reimport(db_session, casp_grouped_sample_csv):
    import_csv_to_db(db_session, str(casp_grouped_sample_csv), RegisterType.CASP)
    before = {e.lei: e.slug for e in db_session.query(Entity).all()}

    # Re-import (delete + re-insert; entity ids may rotate)
    import_csv_to_db(db_session, str(casp_grouped_sample_csv), RegisterType.CASP)
    after = {e.lei: e.slug for e in db_session.query(Entity).all()}

    assert before == after
    # Registry keeps exactly one row per identity (no duplicates from re-import)
    registry_count = db_session.query(EntitySlug).count()
    assert registry_count == len(before)


def test_slug_collision_gets_deterministic_suffix(db_session):
    from backend.app.slugs import assign_slugs

    class FakeEntity:
        slug = None

    a, b, c = FakeEntity(), FakeEntity(), FakeEntity()
    pending = [
        (a, "lei:AAA", "Acme", "DE"),
        (b, "lei:BBB", "Acme", "FR"),
        (c, "lei:CCC", "Acme", "FR"),
    ]
    assign_slugs(db_session, "casp", pending)

    assert a.slug == "acme"
    assert b.slug == "acme-fr"
    assert c.slug not in {a.slug, b.slug} and c.slug.startswith("acme-")

    # Re-running with the same identities reuses the registered slugs
    a2, b2 = FakeEntity(), FakeEntity()
    assign_slugs(db_session, "casp", [(a2, "lei:AAA", "Acme", "DE"), (b2, "lei:BBB", "Acme", "FR")])
    assert a2.slug == "acme"
    assert b2.slug == "acme-fr"


# --- API ---

def test_entities_list_and_feed_expose_slug(client, db_with_casp_data):
    response = client.get("/api/entities?register_type=casp&limit=5")
    assert response.status_code == 200
    items = response.json()["items"]
    assert items and all(item.get("slug") for item in items)

    feed = client.get("/api/feeds/casp.json")
    assert feed.status_code == 200
    assert all(item.get("slug") for item in feed.json()["items"])


def test_get_entity_by_slug(client, db_with_ncasp_data):
    listed = client.get("/api/entities?register_type=ncasp&limit=1").json()["items"][0]
    response = client.get(f"/api/entities/by-slug/{listed['slug']}?register_type=ncasp")
    assert response.status_code == 200
    assert response.json()["id"] == listed["id"]

    assert client.get("/api/entities/by-slug/nope-does-not-exist").status_code == 404


def test_get_casp_company_by_slug_returns_grouped_payload(client, db_with_casp_grouped_data):
    listed = client.get("/api/casp/companies?limit=10").json()["items"]
    euwax = next(item for item in listed if item["lei"] == "529900032TYR45XIEW79")
    assert euwax["slug"]

    response = client.get(f"/api/casp/companies/by-slug/{euwax['slug']}")
    assert response.status_code == 200
    company = response.json()
    assert company["id"] == euwax["id"]
    assert company["record_count"] == 2
    assert company["slug"] == euwax["slug"]

    assert client.get("/api/casp/companies/by-slug/nope").status_code == 404
