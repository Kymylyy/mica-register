"""
Integration tests for CSV → Database import.

Verifies that ALL fields from CSV are correctly imported to the database,
including proper parsing of dates, booleans, pipe-separated values, and service codes.
"""

import pytest
import pandas as pd
from datetime import date

from backend.app.import_csv import import_csv_to_db
from backend.app.models import Entity
from backend.app.config.registers import RegisterType


class TestCaspCsvImport:
    """Test CASP CSV import completeness"""

    def test_all_casp_fields_imported(self, db_session, casp_sample_csv):
        """Verify ALL CASP fields from CSV are imported to database"""
        import_csv_to_db(db_session, str(casp_sample_csv), RegisterType.CASP)

        entity = db_session.query(Entity).filter(
            Entity.register_type == RegisterType.CASP
        ).first()

        assert entity is not None

        # Common fields
        assert entity.competent_authority is not None
        assert entity.lei is not None
        assert entity.commercial_name is not None
        assert entity.home_member_state is not None
        assert entity.authorisation_notification_date is not None

        # CASP-specific fields
        assert entity.casp_entity is not None
        assert entity.casp_entity.website_platform is not None

    def test_casp_service_parsing(self, db_session, casp_sample_csv):
        """Verify service codes are properly parsed from pipe-separated values"""
        import_csv_to_db(db_session, str(casp_sample_csv), RegisterType.CASP)

        entity = db_session.query(Entity).filter(
            Entity.lei == "5299001HFNLCLQMF3X50"
        ).first()

        assert entity is not None
        assert len(entity.casp_entity.services) > 0

        # Check service codes are normalized (should be 'a', 'e', not full description)
        service_codes = {s.code for s in entity.casp_entity.services}
        assert 'a' in service_codes
        assert 'e' in service_codes

    def test_casp_passport_countries_parsing(self, db_session, casp_sample_csv):
        """Verify passport countries are properly parsed"""
        import_csv_to_db(db_session, str(casp_sample_csv), RegisterType.CASP)

        entity = db_session.query(Entity).filter(
            Entity.lei == "5299001HFNLCLQMF3X50"
        ).first()

        assert entity is not None
        assert entity.casp_entity is not None
        assert len(entity.casp_entity.passport_countries) > 0

        country_codes = {c.country_code for c in entity.casp_entity.passport_countries}
        assert 'BE' in country_codes
        assert 'FR' in country_codes
        assert 'NL' in country_codes

    def test_casp_date_parsing(self, db_session, casp_sample_csv):
        """Verify dates are properly parsed from DD/MM/YYYY format"""
        import_csv_to_db(db_session, str(casp_sample_csv), RegisterType.CASP)

        entity = db_session.query(Entity).filter(
            Entity.lei == "5299001HFNLCLQMF3X50"
        ).first()

        assert entity is not None
        assert entity.authorisation_notification_date == date(2025, 1, 15)

    def test_casp_authorisation_end_date(self, db_session, casp_sample_csv):
        """Verify authorisation_end_date is properly imported"""
        import_csv_to_db(db_session, str(casp_sample_csv), RegisterType.CASP)

        # Entity with end date
        entity = db_session.query(Entity).filter(
            Entity.lei == "549300VQCFXP8VPUWM89"
        ).first()

        assert entity is not None
        assert entity.authorisation_end_date == date(2025, 12, 31)

    def test_casp_property_access(self, db_session, casp_sample_csv):
        """Verify CASP fields are accessible through Entity properties"""
        import_csv_to_db(db_session, str(casp_sample_csv), RegisterType.CASP)

        entity = db_session.query(Entity).filter(
            Entity.lei == "5299001HFNLCLQMF3X50"
        ).first()

        # These should work through properties defined in Entity model
        assert entity.website_platform is not None
        assert entity.services is not None
        assert entity.passport_countries is not None

    def test_casp_multiple_entities(self, db_session, casp_sample_csv):
        """Verify multiple CASP entities are imported"""
        import_csv_to_db(db_session, str(casp_sample_csv), RegisterType.CASP)

        entities = db_session.query(Entity).filter(
            Entity.register_type == RegisterType.CASP
        ).all()

        # CSV should have 3 entities
        assert len(entities) == 3


class TestOtherCsvImport:
    """Test OTHER CSV import completeness"""

    def test_all_other_fields_imported(self, db_session, other_sample_csv):
        """Verify ALL OTHER fields from CSV are imported to database"""
        import_csv_to_db(db_session, str(other_sample_csv), RegisterType.OTHER)

        entity = db_session.query(Entity).filter(
            Entity.register_type == RegisterType.OTHER
        ).first()

        assert entity is not None

        # Common fields (note: OTHER often has lei_name instead of commercial_name)
        assert entity.competent_authority is not None
        assert entity.lei_name is not None
        assert entity.home_member_state is not None

        # OTHER-specific fields
        assert entity.other_entity is not None

    def test_other_lei_casp_linkage(self, db_session, other_sample_csv):
        """Verify LEI_CASP and LEI_NAME_CASP are imported"""
        import_csv_to_db(db_session, str(other_sample_csv), RegisterType.OTHER)

        entity = db_session.query(Entity).filter(
            Entity.lei_name == "Tether Operations Limited"
        ).first()

        assert entity is not None
        assert entity.other_entity.lei_casp == "5299001HFNLCLQMF3X50"
        assert entity.other_entity.lei_name_casp == "Binance Europe Services Ltd."

    def test_other_pipe_separated_fields(self, db_session, other_sample_csv):
        """Verify offer_countries and dti_codes are properly parsed"""
        import_csv_to_db(db_session, str(other_sample_csv), RegisterType.OTHER)

        entity = db_session.query(Entity).filter(
            Entity.lei_name == "Tether Operations Limited"
        ).first()

        assert entity is not None
        assert entity.other_entity.offer_countries is not None
        assert "DE" in entity.other_entity.offer_countries
        assert entity.other_entity.dti_codes is not None
        assert "DTI-001" in entity.other_entity.dti_codes

    def test_other_boolean_field(self, db_session, other_sample_csv):
        """Verify DTI/FFG boolean is properly parsed"""
        import_csv_to_db(db_session, str(other_sample_csv), RegisterType.OTHER)

        # Entity with DTI/FFG = YES
        entity_yes = db_session.query(Entity).filter(
            Entity.lei_name == "Tether Operations Limited"
        ).first()
        assert entity_yes.other_entity.dti_ffg == "YES"

        # Entity with DTI/FFG = NO
        entity_no = db_session.query(Entity).filter(
            Entity.lei_name == "Circle Internet Financial"
        ).first()
        assert entity_no.other_entity.dti_ffg == "NO" or entity_no.other_entity.dti_ffg == ""

    def test_other_without_lei(self, db_session, other_sample_csv):
        """Verify OTHER entities without LEI are imported (common case)"""
        import_csv_to_db(db_session, str(other_sample_csv), RegisterType.OTHER)

        # MakerDAO and Uniswap don't have LEI in the sample
        entities_without_lei = db_session.query(Entity).filter(
            Entity.register_type == RegisterType.OTHER,
            Entity.lei.is_(None)
        ).all()

        assert len(entities_without_lei) >= 2


class TestArtCsvImport:
    """Test ART CSV import completeness"""

    def test_all_art_fields_imported(self, db_session, art_sample_csv):
        """Verify ALL ART fields from CSV are imported to database"""
        import_csv_to_db(db_session, str(art_sample_csv), RegisterType.ART)

        entity = db_session.query(Entity).filter(
            Entity.register_type == RegisterType.ART
        ).first()

        assert entity is not None

        # Common fields
        assert entity.competent_authority is not None
        assert entity.lei is not None
        assert entity.commercial_name is not None
        assert entity.home_member_state is not None
        assert entity.authorisation_notification_date is not None

        # ART-specific fields
        assert entity.art_entity is not None
        assert entity.art_entity.white_paper_url is not None

    def test_art_credit_institution_flag(self, db_session, art_sample_csv):
        """Verify credit_institution boolean is properly parsed"""
        import_csv_to_db(db_session, str(art_sample_csv), RegisterType.ART)

        # Entity with credit_institution = YES
        entity_yes = db_session.query(Entity).filter(
            Entity.lei == "5299001HFNLCLQMF3X50"
        ).first()
        assert entity_yes.art_entity.credit_institution is True

        # Entity with credit_institution = NO
        entity_no = db_session.query(Entity).filter(
            Entity.lei == "969500CX1Y60EXKXQH23"
        ).first()
        assert entity_no.art_entity.credit_institution is False

    def test_art_white_paper_fields(self, db_session, art_sample_csv):
        """Verify white paper URL and offer countries are imported"""
        import_csv_to_db(db_session, str(art_sample_csv), RegisterType.ART)

        entity = db_session.query(Entity).filter(
            Entity.lei == "5299001HFNLCLQMF3X50"
        ).first()

        assert entity is not None
        assert entity.art_entity.white_paper_url == "https://binance.com/eur-whitepaper.pdf"
        assert entity.art_entity.white_paper_offer_countries is not None
        assert "DE" in entity.art_entity.white_paper_offer_countries

    def test_art_authorisation_end_date(self, db_session, art_sample_csv):
        """Verify authorisation_end_date is imported for ART"""
        import_csv_to_db(db_session, str(art_sample_csv), RegisterType.ART)

        entity = db_session.query(Entity).filter(
            Entity.lei == "969500CX1Y60EXKXQH23"
        ).first()

        assert entity is not None
        assert entity.art_entity.authorisation_end_date == date(2026, 12, 31)


class TestEmtCsvImport:
    """Test EMT CSV import completeness"""

    def test_all_emt_fields_imported(self, db_session, emt_sample_csv):
        """Verify ALL EMT fields from CSV are imported to database"""
        import_csv_to_db(db_session, str(emt_sample_csv), RegisterType.EMT)

        entity = db_session.query(Entity).filter(
            Entity.register_type == RegisterType.EMT
        ).first()

        assert entity is not None

        # Common fields
        assert entity.competent_authority is not None
        assert entity.lei is not None
        assert entity.commercial_name is not None
        assert entity.home_member_state is not None
        assert entity.authorisation_notification_date is not None

        # EMT-specific fields
        assert entity.emt_entity is not None

    def test_emt_exemption_flags(self, db_session, emt_sample_csv):
        """Verify exemption_48_4 and exemption_48_5 booleans are properly parsed"""
        import_csv_to_db(db_session, str(emt_sample_csv), RegisterType.EMT)

        # Entity with exemption_48_4 = YES, exemption_48_5 = NO
        entity = db_session.query(Entity).filter(
            Entity.lei == "5299001HFNLCLQMF3X50"
        ).first()
        assert entity.emt_entity.exemption_48_4 is True
        assert entity.emt_entity.exemption_48_5 is False

        # Entity with both exemptions = YES
        entity_both = db_session.query(Entity).filter(
            Entity.lei == "549300VQCFXP8VPUWM89"
        ).first()
        assert entity_both.emt_entity.exemption_48_4 is True
        assert entity_both.emt_entity.exemption_48_5 is True

    def test_emt_authorisation_other_emt(self, db_session, emt_sample_csv):
        """Verify authorisation_other_emt text field is imported"""
        import_csv_to_db(db_session, str(emt_sample_csv), RegisterType.EMT)

        entity = db_session.query(Entity).filter(
            Entity.lei == "5299001HFNLCLQMF3X50"
        ).first()

        assert entity is not None
        assert entity.emt_entity.authorisation_other_emt == "Credit institution under CRD"

    def test_emt_white_paper_notification_date(self, db_session, emt_sample_csv):
        """Verify white_paper_notification_date is properly parsed"""
        import_csv_to_db(db_session, str(emt_sample_csv), RegisterType.EMT)

        entity = db_session.query(Entity).filter(
            Entity.lei == "5299001HFNLCLQMF3X50"
        ).first()

        assert entity is not None
        assert entity.emt_entity.white_paper_notification_date == date(2024, 12, 15)

    def test_emt_dti_fields(self, db_session, emt_sample_csv):
        """Verify DTI/FFG and DTI codes are imported"""
        import_csv_to_db(db_session, str(emt_sample_csv), RegisterType.EMT)

        entity = db_session.query(Entity).filter(
            Entity.lei == "5299001HFNLCLQMF3X50"
        ).first()

        assert entity is not None
        assert entity.emt_entity.dti_ffg == "YES"
        assert entity.emt_entity.dti_codes is not None
        assert "EMT-001" in entity.emt_entity.dti_codes


class TestNcaspCsvImport:
    """Test NCASP CSV import completeness"""

    def test_all_ncasp_fields_imported(self, db_session, ncasp_sample_csv):
        """Verify ALL NCASP fields from CSV are imported to database"""
        import_csv_to_db(db_session, str(ncasp_sample_csv), RegisterType.NCASP)

        entity = db_session.query(Entity).filter(
            Entity.register_type == RegisterType.NCASP
        ).first()

        assert entity is not None

        # Common fields (note: NCASP often lacks LEI)
        assert entity.competent_authority is not None
        assert entity.commercial_name is not None
        assert entity.home_member_state is not None

        # NCASP-specific fields
        assert entity.ncasp_entity is not None
        assert entity.ncasp_entity.infringement is not None
        assert entity.ncasp_entity.reason is not None

    def test_ncasp_multiple_websites(self, db_session, ncasp_sample_csv):
        """Verify multiple websites are properly parsed"""
        import_csv_to_db(db_session, str(ncasp_sample_csv), RegisterType.NCASP)

        entity = db_session.query(Entity).filter(
            Entity.commercial_name == "Luxembourg Ponzi Scheme"
        ).first()

        assert entity is not None
        assert entity.ncasp_entity.websites is not None
        # Should have 3 websites pipe-separated
        assert entity.ncasp_entity.websites.count("|") >= 2

    def test_ncasp_infringement_flag(self, db_session, ncasp_sample_csv):
        """Verify infringement field is imported (stored as string in DB)"""
        import_csv_to_db(db_session, str(ncasp_sample_csv), RegisterType.NCASP)

        entities = db_session.query(Entity).filter(
            Entity.register_type == RegisterType.NCASP
        ).all()

        # All NCASP entities in sample should have infringement = "YES"
        # Note: infringement is stored as String in DB model, not Boolean
        for entity in entities:
            assert entity.ncasp_entity.infringement == "YES"

    def test_ncasp_decision_date(self, db_session, ncasp_sample_csv):
        """Verify decision_date is properly parsed"""
        import_csv_to_db(db_session, str(ncasp_sample_csv), RegisterType.NCASP)

        entity = db_session.query(Entity).filter(
            Entity.commercial_name == "Crypto Scam Platform GmbH"
        ).first()

        assert entity is not None
        assert entity.ncasp_entity.decision_date == date(2025, 1, 15)

    def test_ncasp_without_lei(self, db_session, ncasp_sample_csv):
        """Verify NCASP entities without LEI are imported (very common case)"""
        import_csv_to_db(db_session, str(ncasp_sample_csv), RegisterType.NCASP)

        entities_without_lei = db_session.query(Entity).filter(
            Entity.register_type == RegisterType.NCASP,
            Entity.lei.is_(None)
        ).all()

        # Most NCASP entities don't have LEI (fixture has 2 without LEI)
        assert len(entities_without_lei) >= 2
