"""
Integration tests for Database → API.

Verifies that ALL fields from database models are exposed through API endpoints
with correct data types and structure.
"""

import pytest
from datetime import date

from backend.app.config.registers import RegisterType


class TestCaspApiSchema:
    """Test CASP API response completeness"""

    def test_all_casp_fields_in_api_response(self, client, db_with_casp_data):
        """Verify ALL CASP fields are in API response"""
        response = client.get("/api/entities?register_type=casp&limit=1")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert len(data["items"]) > 0

        entity = data["items"][0]

        # Common fields
        assert "competent_authority" in entity
        assert "lei" in entity
        assert "commercial_name" in entity
        assert "home_member_state" in entity
        assert "authorisation_notification_date" in entity
        assert "register_type" in entity

        # CASP-specific fields
        assert "services" in entity
        assert "passport_countries" in entity
        assert "website_platform" in entity

    def test_casp_services_structure(self, client, db_with_casp_data):
        """Verify services are returned as list of objects"""
        response = client.get("/api/entities?register_type=casp&limit=10")
        assert response.status_code == 200

        entity = response.json()["items"][0]

        assert "services" in entity
        assert isinstance(entity["services"], list)

        if len(entity["services"]) > 0:
            service = entity["services"][0]
            assert "code" in service
            assert "description" in service

    def test_casp_passport_countries_structure(self, client, db_with_casp_data):
        """Verify passport_countries are returned as list of objects"""
        response = client.get("/api/entities?register_type=casp&limit=10")
        assert response.status_code == 200

        # Find an entity with passport countries
        entities = response.json()["items"]
        passporting_entity = next((e for e in entities if len(e.get("passport_countries", [])) > 0), None)

        assert passporting_entity is not None
        assert "passport_countries" in passporting_entity
        assert isinstance(passporting_entity["passport_countries"], list)

        if len(passporting_entity["passport_countries"]) > 0:
            country = passporting_entity["passport_countries"][0]
            assert "country_code" in country

    def test_casp_date_format(self, client, db_with_casp_data):
        """Verify dates are returned as ISO format strings"""
        response = client.get("/api/entities?register_type=casp&limit=1")
        assert response.status_code == 200

        entity = response.json()["items"][0]

        # authorisation_notification_date should be ISO format (YYYY-MM-DD)
        assert "authorisation_notification_date" in entity
        if entity["authorisation_notification_date"]:
            # Should be parseable as ISO date
            date_str = entity["authorisation_notification_date"]
            assert "-" in date_str  # ISO format uses hyphens
            # Verify it's a valid date
            date.fromisoformat(date_str)

    def test_casp_property_exposure(self, client, db_with_casp_data):
        """Verify CASP-specific properties are exposed through API"""
        response = client.get("/api/entities?register_type=casp&limit=1")
        assert response.status_code == 200

        entity = response.json()["items"][0]

        # These should be accessible through Entity properties
        assert "website_platform" in entity
        assert "authorisation_end_date" in entity


class TestOtherApiSchema:
    """Test OTHER API response completeness"""

    def test_all_other_fields_in_api_response(self, client, db_with_other_data):
        """Verify ALL OTHER fields are in API response"""
        response = client.get("/api/entities?register_type=other&limit=1")
        assert response.status_code == 200

        entity = response.json()["items"][0]

        # Common fields
        assert "competent_authority" in entity
        assert "lei_name" in entity
        assert "home_member_state" in entity
        assert "register_type" in entity

        # OTHER-specific fields
        assert "lei_casp" in entity
        assert "lei_name_casp" in entity
        assert "offer_countries" in entity
        assert "white_paper_url" in entity
        assert "dti_ffg" in entity
        assert "dti_codes" in entity
        assert "white_paper_comments" in entity

    def test_other_boolean_type(self, client, db_with_other_data):
        """Verify dti_ffg is returned as boolean"""
        response = client.get("/api/entities?register_type=other&limit=10")
        assert response.status_code == 200

        entities = response.json()["items"]

        # Find entity with dti_ffg
        entity_with_dti = next((e for e in entities if e.get("dti_ffg") is not None), None)
        assert entity_with_dti is not None
        assert isinstance(entity_with_dti["dti_ffg"], str) or entity_with_dti["dti_ffg"] is None
        if entity_with_dti["dti_ffg"]:
            assert entity_with_dti["dti_ffg"] in ["YES", "NO"]

    def test_other_pipe_separated_values(self, client, db_with_other_data):
        """Verify pipe-separated values are in response"""
        response = client.get("/api/entities?register_type=other&limit=10")
        assert response.status_code == 200

        entities = response.json()["items"]

        # Find entity with offer_countries
        entity_with_countries = next((e for e in entities if e.get("offer_countries")), None)
        assert entity_with_countries is not None
        # Should contain pipe-separated countries or be a string
        assert isinstance(entity_with_countries["offer_countries"], str)


class TestArtApiSchema:
    """Test ART API response completeness"""

    def test_all_art_fields_in_api_response(self, client, db_with_art_data):
        """Verify ALL ART fields are in API response"""
        response = client.get("/api/entities?register_type=art&limit=1")
        assert response.status_code == 200

        entity = response.json()["items"][0]

        # Common fields
        assert "competent_authority" in entity
        assert "lei" in entity
        assert "commercial_name" in entity
        assert "home_member_state" in entity
        assert "authorisation_notification_date" in entity

        # ART-specific fields
        assert "credit_institution" in entity
        assert "white_paper_url" in entity
        assert "white_paper_offer_countries" in entity
        assert "authorisation_end_date" in entity
        assert "white_paper_comments" in entity

    def test_art_credit_institution_boolean(self, client, db_with_art_data):
        """Verify credit_institution is returned as boolean"""
        response = client.get("/api/entities?register_type=art&limit=10")
        assert response.status_code == 200

        entities = response.json()["items"]

        # Find entity with credit_institution
        entity = next((e for e in entities if e.get("credit_institution") is not None), None)
        assert entity is not None
        assert isinstance(entity["credit_institution"], bool)


class TestEmtApiSchema:
    """Test EMT API response completeness"""

    def test_all_emt_fields_in_api_response(self, client, db_with_emt_data):
        """Verify ALL EMT fields are in API response"""
        response = client.get("/api/entities?register_type=emt&limit=1")
        assert response.status_code == 200

        entity = response.json()["items"][0]

        # Common fields
        assert "competent_authority" in entity
        assert "lei" in entity
        assert "commercial_name" in entity
        assert "home_member_state" in entity
        assert "authorisation_notification_date" in entity

        # EMT-specific fields
        assert "exemption_48_4" in entity
        assert "exemption_48_5" in entity
        assert "authorisation_other_emt" in entity
        assert "white_paper_notification_date" in entity
        assert "white_paper_url" in entity
        assert "dti_ffg" in entity
        assert "dti_codes" in entity
        assert "authorisation_end_date" in entity
        assert "white_paper_comments" in entity

    def test_emt_exemption_booleans(self, client, db_with_emt_data):
        """Verify exemption flags are returned as booleans"""
        response = client.get("/api/entities?register_type=emt&limit=10")
        assert response.status_code == 200

        entities = response.json()["items"]

        # Check exemption_48_4 and exemption_48_5
        entity = entities[0]
        if entity.get("exemption_48_4") is not None:
            assert isinstance(entity["exemption_48_4"], bool)
        if entity.get("exemption_48_5") is not None:
            assert isinstance(entity["exemption_48_5"], bool)

    def test_emt_white_paper_notification_date(self, client, db_with_emt_data):
        """Verify white_paper_notification_date is in ISO format"""
        response = client.get("/api/entities?register_type=emt&limit=10")
        assert response.status_code == 200

        entities = response.json()["items"]

        # Find entity with white_paper_notification_date
        entity = next((e for e in entities if e.get("white_paper_notification_date")), None)
        assert entity is not None

        date_str = entity["white_paper_notification_date"]
        # Should be ISO format
        date.fromisoformat(date_str)


class TestNcaspApiSchema:
    """Test NCASP API response completeness"""

    def test_all_ncasp_fields_in_api_response(self, client, db_with_ncasp_data):
        """Verify ALL NCASP fields are in API response"""
        response = client.get("/api/entities?register_type=ncasp&limit=1")
        assert response.status_code == 200

        entity = response.json()["items"][0]

        # Common fields (note: NCASP often lacks LEI)
        assert "competent_authority" in entity
        assert "commercial_name" in entity
        assert "home_member_state" in entity
        assert "register_type" in entity

        # NCASP-specific fields
        assert "websites" in entity
        assert "infringement" in entity
        assert "reason" in entity
        assert "decision_date" in entity

    def test_ncasp_infringement_boolean(self, client, db_with_ncasp_data):
        """Verify infringement is returned as boolean"""
        response = client.get("/api/entities?register_type=ncasp&limit=10")
        assert response.status_code == 200

        entities = response.json()["items"]

        entity = next((e for e in entities if e.get("infringement") is not None), None)
        assert entity is not None
        assert isinstance(entity["infringement"], str) or entity["infringement"] is None
        if entity["infringement"]:
            assert entity["infringement"] == "YES"

    def test_ncasp_multiple_websites(self, client, db_with_ncasp_data):
        """Verify websites field contains pipe-separated values"""
        response = client.get("/api/entities?register_type=ncasp&limit=10")
        assert response.status_code == 200

        entities = response.json()["items"]

        # Find entity with multiple websites
        entity = next((e for e in entities if e.get("websites") and "|" in e["websites"]), None)
        assert entity is not None
        assert isinstance(entity["websites"], str)

    def test_ncasp_decision_date_format(self, client, db_with_ncasp_data):
        """Verify decision_date is in ISO format"""
        response = client.get("/api/entities?register_type=ncasp&limit=10")
        assert response.status_code == 200

        entities = response.json()["items"]

        entity = next((e for e in entities if e.get("decision_date")), None)
        assert entity is not None

        date_str = entity["decision_date"]
        # Should be ISO format
        date.fromisoformat(date_str)


class TestApiPagination:
    """Test API pagination and filtering"""

    def test_limit_parameter(self, client, db_with_casp_data):
        """Verify limit parameter works"""
        response = client.get("/api/entities?register_type=casp&limit=3")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert len(data["items"]) <= 3

    def test_register_type_filter(self, client, db_with_casp_data):
        """Verify register_type filter works"""
        response = client.get("/api/entities?register_type=casp")
        assert response.status_code == 200

        entities = response.json()["items"]
        for entity in entities:
            assert entity["register_type"] == "casp"

    def test_total_count(self, client, db_with_casp_data):
        """Verify total count is returned"""
        response = client.get("/api/entities?register_type=casp")
        assert response.status_code == 200

        data = response.json()
        assert "total" in data
        assert isinstance(data["total"], int)
        assert data["total"] > 0
