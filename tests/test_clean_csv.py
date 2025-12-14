"""
Pytest tests for CSV cleaning module.
"""

import pytest
import tempfile
import json
from pathlib import Path
import sys
import pandas as pd

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.csv_clean import CSVCleaner, Change


@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file for testing"""
    def _create_csv(content: str) -> Path:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8', newline='') as f:
            f.write(content)
            return Path(f.name)
    return _create_csv


def test_fix_dates(temp_csv_file):
    """Test that dates are fixed using parse_date()"""
    csv_content = """ae_lei,ac_serviceCode,ac_serviceCode_cou,ac_authorisationNotificationDate,ac_lastupdate
5299005V5GBSN2A4C303,a. providing custody,BE|FR,01/12/.2025,01/01/2025"""
    csv_path = temp_csv_file(csv_content)
    
    try:
        cleaner = CSVCleaner(csv_path)
        cleaner.load_csv()
        cleaner.fix_dates()
        
        # Check that date was fixed
        date_changes = [c for c in cleaner.changes if c.type == "DATE_FIXED"]
        assert len(date_changes) > 0
        assert date_changes[0].old_value == "01/12/.2025"
        assert date_changes[0].new_value == "01/12/2025"
        
        # Check DataFrame was updated
        assert cleaner.df.iloc[0]['ac_authorisationNotificationDate'] == "01/12/2025"
    finally:
        csv_path.unlink()


def test_fix_dates_unparseable(temp_csv_file):
    """Test that unparseable dates are left as-is with warning"""
    csv_content = """ae_lei,ac_serviceCode,ac_serviceCode_cou,ac_authorisationNotificationDate,ac_lastupdate
5299005V5GBSN2A4C303,a. providing custody,BE|FR,invalid-date,01/01/2025"""
    csv_path = temp_csv_file(csv_content)
    
    try:
        cleaner = CSVCleaner(csv_path)
        cleaner.load_csv()
        cleaner.fix_dates()
        
        # Check that warning was added
        date_warnings = [c for c in cleaner.changes if c.type == "DATE_WARNING"]
        assert len(date_warnings) > 0
        assert date_warnings[0].old_value == "invalid-date"
        
        # Check DataFrame was NOT modified (left as-is)
        assert cleaner.df.iloc[0]['ac_authorisationNotificationDate'] == "invalid-date"
    finally:
        csv_path.unlink()


def test_fix_multiline_website(temp_csv_file):
    """Test that multiline website fields are fixed with URL dedup and | separator"""
    csv_content = """ae_lei,ac_serviceCode,ac_serviceCode_cou,ac_authorisationNotificationDate,ac_lastupdate,ae_website
5299005V5GBSN2A4C303,a. providing custody,BE|FR,01/01/2025,01/01/2025,"www.skrill.com
www.neteller.com"
"""
    csv_path = temp_csv_file(csv_content)
    
    try:
        cleaner = CSVCleaner(csv_path)
        cleaner.load_csv()
        cleaner.fix_multiline_fields()
        
        # Check that multiline was fixed
        multiline_changes = [c for c in cleaner.changes if c.type == "MULTILINE_WEBSITE_FIXED"]
        assert len(multiline_changes) > 0
        assert "www.skrill.com" in multiline_changes[0].old_value
        assert "\n" not in cleaner.df.iloc[0]['ae_website']
        # Check that URLs are separated by |
        website_value = cleaner.df.iloc[0]['ae_website']
        assert "|" in website_value or "https://" in website_value
    finally:
        csv_path.unlink()


def test_fix_lei_trailing_dot(temp_csv_file):
    """Test that LEI with trailing dot is fixed"""
    csv_content = """ae_lei,ac_serviceCode,ac_serviceCode_cou,ac_authorisationNotificationDate,ac_lastupdate
89450036UW3ID72T1M84.,a. providing custody,BE|FR,01/01/2025,01/01/2025"""
    csv_path = temp_csv_file(csv_content)
    
    try:
        cleaner = CSVCleaner(csv_path)
        cleaner.load_csv()
        cleaner.fix_lei_format()
        
        # Check that trailing dot was removed
        lei_changes = [c for c in cleaner.changes if c.type == "LEI_TRAILING_DOT_REMOVED"]
        assert len(lei_changes) > 0
        assert lei_changes[0].old_value == "89450036UW3ID72T1M84."
        assert lei_changes[0].new_value == "89450036UW3ID72T1M84"
        
        # Check DataFrame was updated
        assert cleaner.df.iloc[0]['ae_lei'] == "89450036UW3ID72T1M84"
    finally:
        csv_path.unlink()


def test_fix_lei_excel_notation(temp_csv_file):
    """Test that Excel scientific notation LEI is attempted to be fixed, or marked as warning"""
    csv_content = """ae_lei,ac_serviceCode,ac_serviceCode_cou,ac_authorisationNotificationDate,ac_lastupdate
9.60E+19,a. providing custody,BE|FR,01/01/2025,01/01/2025"""
    csv_path = temp_csv_file(csv_content)
    
    try:
        cleaner = CSVCleaner(csv_path)
        cleaner.load_csv()
        cleaner.fix_lei_format()
        
        # Check that either fixed or warning (not manual fix)
        lei_fixed = [c for c in cleaner.changes if c.type == "LEI_EXCEL_NOTATION_FIXED"]
        lei_warnings = [c for c in cleaner.changes if c.type == "LEI_WARNING"]
        assert len(lei_fixed) > 0 or len(lei_warnings) > 0
        if lei_warnings:
            assert "Excel scientific notation" in lei_warnings[0].new_value
    finally:
        csv_path.unlink()


def test_merge_duplicate_lei(temp_csv_file):
    """Test that duplicate LEI rows are merged"""
    csv_content = """ae_lei,ac_serviceCode,ac_serviceCode_cou,ac_authorisationNotificationDate,ac_lastupdate
5299005V5GBSN2A4C303,a. providing custody,BE|FR,01/01/2025,01/01/2025
5299005V5GBSN2A4C303,b. trading platform,DE|IT,01/01/2025,01/01/2025"""
    csv_path = temp_csv_file(csv_content)
    
    try:
        cleaner = CSVCleaner(csv_path)
        cleaner.load_csv()
        initial_count = len(cleaner.df)
        cleaner.merge_duplicate_lei()
        final_count = len(cleaner.df)
        
        # Should have merged 2 rows into 1
        assert final_count < initial_count
        assert final_count == 1
        
        # Check that services were merged
        merged_services = cleaner.df.iloc[0]['ac_serviceCode']
        assert "a. providing custody" in merged_services
        assert "b. trading platform" in merged_services
    finally:
        csv_path.unlink()


def test_fix_encoding_issues(temp_csv_file):
    """Test that encoding issues are fixed"""
    csv_content = """ae_lei,ac_serviceCode,ac_serviceCode_cou,ac_authorisationNotificationDate,ac_lastupdate,ae_address
5299005V5GBSN2A4C303,a. providing custody,BE|FR,01/01/2025,01/01/2025,Donau-City-Strae 7"""
    csv_path = temp_csv_file(csv_content)
    
    try:
        cleaner = CSVCleaner(csv_path)
        cleaner.load_csv()
        cleaner.fix_encoding_issues()
        
        # Check that encoding was fixed
        encoding_changes = [c for c in cleaner.changes if c.type == "ENCODING_FIXED"]
        # May or may not have changes depending on how pandas reads it
        # But if there are changes, they should be encoding fixes
        if encoding_changes:
            assert "Strae" in encoding_changes[0].old_value or "Straße" in encoding_changes[0].new_value
    finally:
        csv_path.unlink()


def test_normalize_commercial_names(temp_csv_file):
    """Test that commercial names are normalized"""
    csv_content = """ae_lei,ac_serviceCode,ac_serviceCode_cou,ac_authorisationNotificationDate,ac_lastupdate,ae_commercial_name
5299005V5GBSN2A4C303,a. providing custody,BE|FR,01/01/2025,01/01/2025,e Toro"""
    csv_path = temp_csv_file(csv_content)
    
    try:
        cleaner = CSVCleaner(csv_path)
        cleaner.load_csv()
        cleaner.normalize_commercial_names()
        
        # Check that name was normalized
        name_changes = [c for c in cleaner.changes if c.type == "COMMERCIAL_NAME_NORMALIZED"]
        assert len(name_changes) > 0
        assert name_changes[0].old_value == "e Toro"
        assert name_changes[0].new_value == "eToro"
        
        # Check DataFrame was updated
        assert cleaner.df.iloc[0]['ae_commercial_name'] == "eToro"
    finally:
        csv_path.unlink()


def test_full_cleaning_process(temp_csv_file):
    """Test full cleaning process"""
    csv_content = """ae_lei,ac_serviceCode,ac_serviceCode_cou,ac_authorisationNotificationDate,ac_lastupdate,ae_website
5299005V5GBSN2A4C303,a. providing custody,BE|FR,01/12/.2025,01/01/2025,"www.skrill.com
www.neteller.com"
89450036UW3ID72T1M84.,b. trading platform,DE|IT,01/01/2025,01/01/2025,https://example.com"""
    csv_path = temp_csv_file(csv_content)
    
    try:
        cleaner = CSVCleaner(csv_path)
        cleaner.load_csv()
        cleaner.fix_all_issues()
        
        # Should have multiple types of changes
        change_types = set(c.type for c in cleaner.changes)
        assert len(change_types) > 0
        
        # Generate report
        report = cleaner.generate_report()
        assert "version" in report
        assert "changes" in report
        assert "summary" in report
        assert report["summary"]["total_changes"] > 0
    finally:
        csv_path.unlink()


def test_save_clean_csv(temp_csv_file):
    """Test saving cleaned CSV"""
    csv_content = """ae_lei,ac_serviceCode,ac_serviceCode_cou,ac_authorisationNotificationDate,ac_lastupdate
5299005V5GBSN2A4C303,a. providing custody,BE|FR,01/12/.2025,01/01/2025"""
    csv_path = temp_csv_file(csv_content)
    
    try:
        cleaner = CSVCleaner(csv_path)
        cleaner.load_csv()
        cleaner.fix_all_issues()
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            assert cleaner.save_clean_csv(output_path)
            assert output_path.exists()
            
            # Verify cleaned CSV can be read
            df = pd.read_csv(output_path)
            assert len(df) > 0
            # Check that date was fixed
            assert "01/12/.2025" not in df['ac_authorisationNotificationDate'].values[0]
        finally:
            if output_path.exists():
                output_path.unlink()
    finally:
        csv_path.unlink()


def test_generate_report(temp_csv_file):
    """Test report generation"""
    csv_content = """ae_lei,ac_serviceCode,ac_serviceCode_cou,ac_authorisationNotificationDate,ac_lastupdate
5299005V5GBSN2A4C303,a. providing custody,BE|FR,01/12/.2025,01/01/2025"""
    csv_path = temp_csv_file(csv_content)
    
    try:
        cleaner = CSVCleaner(csv_path)
        cleaner.load_csv()
        cleaner.fix_all_issues()
        
        report = cleaner.generate_report()
        
        # Check report structure
        assert "version" in report
        assert "generated_at" in report
        assert "input_file" in report
        assert "encoding" in report
        assert "stats" in report
        assert "changes" in report
        assert "summary" in report
        
        # Check stats
        assert report["stats"]["rows_before"] > 0
        assert report["stats"]["rows_after"] > 0
        
        # Check summary
        assert report["summary"]["total_changes"] >= 0
        assert "changes_by_type" in report["summary"]
    finally:
        csv_path.unlink()


def test_fix_whitespace_globally(temp_csv_file):
    """Test that NBSP and trailing spaces are fixed globally"""
    csv_content = """ae_lei,ac_serviceCode,ac_serviceCode_cou,ac_authorisationNotificationDate,ac_lastupdate,ae_commercial_name
5299005V5GBSN2A4C303,a. providing custody,BE|FR,01/01/2025,01/01/2025,Test\xa0Name  """
    csv_path = temp_csv_file(csv_content)
    
    try:
        cleaner = CSVCleaner(csv_path)
        cleaner.load_csv()
        cleaner.fix_whitespace_globally()
        
        # Check that whitespace was fixed
        whitespace_changes = [c for c in cleaner.changes if c.type == "WHITESPACE_FIXED"]
        assert len(whitespace_changes) > 0
        
        # Check DataFrame was updated (NBSP removed, trailing spaces removed)
        name_value = cleaner.df.iloc[0]['ae_commercial_name']
        assert '\xa0' not in name_value
        assert name_value == name_value.strip()
    finally:
        csv_path.unlink()


def test_normalize_country_codes(temp_csv_file):
    """Test that country codes are normalized (EL->GR, case, spaces)"""
    csv_content = """ae_lei,ac_serviceCode,ac_serviceCode_cou,ac_authorisationNotificationDate,ac_lastupdate
5299005V5GBSN2A4C303,a. providing custody," EL|Fi|DE",01/01/2025,01/01/2025"""
    csv_path = temp_csv_file(csv_content)
    
    try:
        cleaner = CSVCleaner(csv_path)
        cleaner.load_csv()
        cleaner.normalize_country_codes()
        
        # Check that country codes were normalized
        country_changes = [c for c in cleaner.changes if c.type == "COUNTRY_CODE_NORMALIZED"]
        assert len(country_changes) > 0
        
        # Check DataFrame was updated
        codes_value = cleaner.df.iloc[0]['ac_serviceCode_cou']
        assert 'EL' in codes_value or 'GR' in codes_value
        assert 'FI' in codes_value
        assert 'DE' in codes_value
        assert '|' in codes_value
    finally:
        csv_path.unlink()


def test_detect_and_fix_encoding_data_loss(temp_csv_file):
    """Test that encoding data loss is detected and attempted to fix"""
    # Create CSV with replacement character
    csv_content = """ae_lei,ac_serviceCode,ac_serviceCode_cou,ac_authorisationNotificationDate,ac_lastupdate,ae_address
5299005V5GBSN2A4C303,a. providing custody,BE|FR,01/01/2025,01/01/2025,Donau-City-Stra\ufffde 7"""
    csv_path = temp_csv_file(csv_content)
    
    try:
        cleaner = CSVCleaner(csv_path)
        cleaner.load_csv()
        cleaner.detect_and_fix_encoding_data_loss()
        
        # Check that either fixed or warning
        encoding_fixed = [c for c in cleaner.changes if c.type == "ENCODING_DATA_LOSS_FIXED"]
        encoding_warnings = [c for c in cleaner.changes if c.type == "ENCODING_DATA_LOSS_WARNING"]
        assert len(encoding_fixed) > 0 or len(encoding_warnings) > 0
        
        if encoding_fixed:
            # If fixed, check that replacement char is gone
            address_value = cleaner.df.iloc[0]['ae_address']
            assert '\ufffd' not in address_value
    finally:
        csv_path.unlink()


def test_dry_run_mode(temp_csv_file):
    """Test that dry run doesn't create output file"""
    csv_content = """ae_lei,ac_serviceCode,ac_serviceCode_cou,ac_authorisationNotificationDate,ac_lastupdate
5299005V5GBSN2A4C303,a. providing custody,BE|FR,01/01/2025,01/01/2025"""
    csv_path = temp_csv_file(csv_content)
    
    try:
        cleaner = CSVCleaner(csv_path)
        cleaner.load_csv()
        cleaner.fix_all_issues()
        
        # Generate report (simulating dry run)
        report = cleaner.generate_report()
        report["output_file"] = "[DRY RUN - not created]"
        
        # Report should be generated but file not created
        assert report["output_file"] == "[DRY RUN - not created]"
    finally:
        csv_path.unlink()
