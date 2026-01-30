"""
Unit tests for SQLAlchemy models.

Tests Entity properties and register-specific entity relationships.
"""

import pytest
from datetime import date
from backend.app.models import (
    Entity, CaspEntity, OtherEntity, ArtEntity, EmtEntity, NcaspEntity,
    Service, PassportCountry
)
from backend.app.config.registers import RegisterType


class TestEntityBaseModel:
    """Test base Entity model"""

    def test_entity_creation(self, db_session):
        """Test creating a basic Entity"""
        entity = Entity(
            register_type=RegisterType.CASP,
            competent_authority="BaFin",
            lei="5299001HFNLCLQMF3X50",
            commercial_name="Test CASP",
            home_member_state="DE",
            authorisation_date=date(2025, 1, 15)
        )
        db_session.add(entity)
        db_session.commit()

        assert entity.id is not None
        assert entity.register_type == RegisterType.CASP
        assert entity.commercial_name == "Test CASP"

    def test_entity_without_lei(self, db_session):
        """Test Entity without LEI (common in OTHER and NCASP)"""
        entity = Entity(
            register_type=RegisterType.OTHER,
            competent_authority="AMF",
            lei_name="Company Without LEI",
            home_member_state="FR",
            authorisation_date=date(2024, 6, 1)
        )
        db_session.add(entity)
        db_session.commit()

        assert entity.lei is None
        assert entity.lei_name == "Company Without LEI"


class TestCaspEntityModel:
    """Test CASP-specific entity and properties"""

    def test_casp_entity_with_services(self, db_session):
        """Test CASP entity with services"""
        entity = Entity(
            register_type=RegisterType.CASP,
            competent_authority="BaFin",
            lei="5299001HFNLCLQMF3X50",
            commercial_name="Test CASP",
            home_member_state="DE",
            authorisation_date=date(2025, 1, 15)
        )

        casp_entity = CaspEntity(
            entity=entity,
            passporting=True,
            website_platform="https://test-casp.de"
        )

        service = Service(
            casp_entity=casp_entity,
            code="a",
            description="Providing custody and administration"
        )

        db_session.add(entity)
        db_session.add(casp_entity)
        db_session.add(service)
        db_session.commit()

        # Test relationships
        assert entity.casp_entity is not None
        assert len(entity.casp_entity.services) == 1
        assert entity.casp_entity.services[0].code == "a"

    def test_casp_entity_property_website_platform(self, db_session):
        """Test Entity.website_platform property for CASP"""
        entity = Entity(
            register_type=RegisterType.CASP,
            competent_authority="BaFin",
            lei="5299001HFNLCLQMF3X50",
            commercial_name="Test CASP",
            home_member_state="DE",
            authorisation_date=date(2025, 1, 15)
        )

        casp_entity = CaspEntity(
            entity=entity,
            website_platform="https://test-casp.de"
        )

        db_session.add(entity)
        db_session.add(casp_entity)
        db_session.commit()

        # Access property through Entity
        assert entity.website_platform == "https://test-casp.de"

    def test_casp_passport_countries(self, db_session):
        """Test CASP passport countries relationship"""
        entity = Entity(
            register_type=RegisterType.CASP,
            competent_authority="BaFin",
            lei="5299001HFNLCLQMF3X50",
            commercial_name="Test CASP",
            home_member_state="DE",
            authorisation_date=date(2025, 1, 15)
        )

        casp_entity = CaspEntity(
            entity=entity,
            passporting=True
        )

        countries = [
            PassportCountry(casp_entity=casp_entity, country_code="BE"),
            PassportCountry(casp_entity=casp_entity, country_code="FR"),
            PassportCountry(casp_entity=casp_entity, country_code="NL")
        ]

        db_session.add(entity)
        db_session.add(casp_entity)
        db_session.add_all(countries)
        db_session.commit()

        # Test relationships
        assert len(entity.casp_entity.passport_countries) == 3
        country_codes = {c.country_code for c in entity.casp_entity.passport_countries}
        assert country_codes == {"BE", "FR", "NL"}

    def test_casp_authorisation_end_date(self, db_session):
        """Test CASP authorisation_end_date through property"""
        entity = Entity(
            register_type=RegisterType.CASP,
            competent_authority="BaFin",
            lei="5299001HFNLCLQMF3X50",
            commercial_name="Test CASP",
            home_member_state="DE",
            authorisation_date=date(2025, 1, 15)
        )

        casp_entity = CaspEntity(
            entity=entity,
            authorisation_end_date=date(2026, 12, 31)
        )

        db_session.add(entity)
        db_session.add(casp_entity)
        db_session.commit()

        # Access through property
        assert entity.authorisation_end_date == date(2026, 12, 31)


class TestOtherEntityModel:
    """Test OTHER-specific entity"""

    def test_other_entity_with_linked_casp(self, db_session):
        """Test OTHER entity with LEI_CASP linkage"""
        entity = Entity(
            register_type=RegisterType.OTHER,
            competent_authority="BaFin",
            lei_name="Tether Operations",
            home_member_state="DE",
            authorisation_date=date(2025, 1, 15)
        )

        other_entity = OtherEntity(
            entity=entity,
            lei_casp="5299001HFNLCLQMF3X50",
            lei_name_casp="Binance Europe Services Ltd.",
            white_paper_url="https://tether.to/wp.pdf",
            offer_countries="DE|FR|IT",
            dti_ffg=True,
            dti_codes="DTI-001|DTI-002"
        )

        db_session.add(entity)
        db_session.add(other_entity)
        db_session.commit()

        assert entity.other_entity is not None
        assert entity.other_entity.lei_casp == "5299001HFNLCLQMF3X50"
        assert entity.other_entity.dti_ffg is True

    def test_other_entity_properties(self, db_session):
        """Test OTHER entity properties accessible through Entity"""
        entity = Entity(
            register_type=RegisterType.OTHER,
            competent_authority="AMF",
            lei_name="Circle Internet",
            home_member_state="FR"
        )

        other_entity = OtherEntity(
            entity=entity,
            white_paper_url="https://circle.com/usdc",
            dti_ffg=False
        )

        db_session.add(entity)
        db_session.add(other_entity)
        db_session.commit()

        assert entity.white_paper_url == "https://circle.com/usdc"
        assert entity.dti_ffg is False


class TestArtEntityModel:
    """Test ART-specific entity"""

    def test_art_entity_credit_institution(self, db_session):
        """Test ART entity with credit institution flag"""
        entity = Entity(
            register_type=RegisterType.ART,
            competent_authority="BaFin",
            lei="5299001HFNLCLQMF3X50",
            commercial_name="Binance EUR Stablecoin",
            home_member_state="DE",
            authorisation_date=date(2025, 1, 15)
        )

        art_entity = ArtEntity(
            entity=entity,
            credit_institution=True,
            white_paper_url="https://binance.com/eur-wp.pdf",
            white_paper_offer_countries="DE|FR|IT|NL"
        )

        db_session.add(entity)
        db_session.add(art_entity)
        db_session.commit()

        assert entity.credit_institution is True
        assert entity.white_paper_offer_countries == "DE|FR|IT|NL"


class TestEmtEntityModel:
    """Test EMT-specific entity"""

    def test_emt_entity_exemptions(self, db_session):
        """Test EMT entity with exemption flags"""
        entity = Entity(
            register_type=RegisterType.EMT,
            competent_authority="BaFin",
            lei="5299001HFNLCLQMF3X50",
            commercial_name="German E-Money Token",
            home_member_state="DE",
            authorisation_date=date(2025, 1, 15)
        )

        emt_entity = EmtEntity(
            entity=entity,
            exemption_48_4=True,
            exemption_48_5=False,
            authorisation_other_emt="Credit institution under CRD",
            white_paper_notification_date=date(2024, 12, 15),
            dti_ffg=True,
            dti_codes="EMT-001|EMT-002"
        )

        db_session.add(entity)
        db_session.add(emt_entity)
        db_session.commit()

        assert entity.exemption_48_4 is True
        assert entity.exemption_48_5 is False
        assert entity.authorisation_other_emt == "Credit institution under CRD"


class TestNcaspEntityModel:
    """Test NCASP-specific entity"""

    def test_ncasp_entity_infringement(self, db_session):
        """Test NCASP entity with infringement details"""
        entity = Entity(
            register_type=RegisterType.NCASP,
            competent_authority="BaFin",
            commercial_name="Crypto Scam Platform",
            home_member_state="DE"
        )

        ncasp_entity = NcaspEntity(
            entity=entity,
            websites="https://scam.de|https://scam.com",
            infringement=True,
            reason="Unauthorized crypto-asset services provision",
            decision_date=date(2025, 1, 15)
        )

        db_session.add(entity)
        db_session.add(ncasp_entity)
        db_session.commit()

        assert entity.infringement is True
        assert entity.reason == "Unauthorized crypto-asset services provision"
        assert entity.decision_date == date(2025, 1, 15)
        assert "scam.de" in entity.websites

    def test_ncasp_without_lei(self, db_session):
        """Test NCASP entity without LEI (common case)"""
        entity = Entity(
            register_type=RegisterType.NCASP,
            competent_authority="AMF",
            commercial_name="Fake Exchange",
            home_member_state="FR"
        )

        ncasp_entity = NcaspEntity(
            entity=entity,
            websites="https://fake.fr",
            infringement=True,
            reason="Operating without authorization"
        )

        db_session.add(entity)
        db_session.add(ncasp_entity)
        db_session.commit()

        assert entity.lei is None
        assert entity.commercial_name == "Fake Exchange"
        assert entity.infringement is True
