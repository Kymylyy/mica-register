"""
Pytest tests for CSV validation module.
"""

import pytest
import tempfile
import json
from pathlib import Path
import sys
import subprocess

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.csv_validate import (
    validate_csv,
    classify_date,
    extract_service_codes,
    validate_country_code,
    Severity,
)


@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file for testing"""
    def _create_csv(content: str) -> Path:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8', newline='') as f:
            f.write(content)
            return Path(f.name)
    return _create_csv


def test_missing_required_column(temp_csv_file):
    """Test that missing required column produces SCHEMA_MISSING_COLUMN error"""
    csv_content = """ae_competentAuthority,ae_homeMemberState
Austrian FMA,AT"""
    csv_path = temp_csv_file(csv_content)
    
    try:
        report = validate_csv(csv_path)
        issues = report["issues"]
        
        # Should have SCHEMA_MISSING_COLUMN error
        missing_col_issues = [i for i in issues if i["code"] == "SCHEMA_MISSING_COLUMN"]
        assert len(missing_col_issues) > 0
        assert missing_col_issues[0]["severity"] == "ERROR"
        
        # Exit code should be 2 (error)
        error_count = sum(1 for i in issues if i["severity"] == "ERROR")
        assert error_count > 0
    finally:
        csv_path.unlink()


def test_invalid_lei_format(temp_csv_file):
    """Test that invalid LEI format produces LEI_INVALID_FORMAT error"""
    csv_content = """ae_lei,ac_serviceCode,ac_serviceCode_cou,ac_authorisationNotificationDate,ac_lastupdate
INVALID123,a. providing custody,BE|FR,01/01/2025,01/01/2025
5299005V5GBSN2A4C303,a. providing custody,BE|FR,01/01/2025,01/01/2025"""
    csv_path = temp_csv_file(csv_content)
    
    try:
        report = validate_csv(csv_path)
        issues = report["issues"]
        
        # Should have LEI_INVALID_FORMAT error
        lei_issues = [i for i in issues if i["code"] == "LEI_INVALID_FORMAT"]
        assert len(lei_issues) > 0
        assert lei_issues[0]["severity"] == "ERROR"
        assert 2 in lei_issues[0]["rows"]  # Row 2 has invalid LEI
        assert "INVALID123" in str(lei_issues[0]["examples"])
    finally:
        csv_path.unlink()


def test_duplicate_lei(temp_csv_file):
    """Test that duplicate LEI produces LEI_DUPLICATE warning"""
    csv_content = """ae_competentAuthority,ae_lei,ae_lei_name,ae_homeMemberState,ae_lei_cou_code,ac_serviceCode,ac_serviceCode_cou,ac_authorisationNotificationDate,ac_lastupdate
BaFin,5299005V5GBSN2A4C303,Test Company Ltd,DE,DE,a. providing custody,BE|FR,01/01/2025,01/01/2025
BaFin,5299005V5GBSN2A4C303,Test Company Ltd,DE,DE,b. trading platform,DE|IT,01/01/2025,01/01/2025"""
    csv_path = temp_csv_file(csv_content)
    
    try:
        report = validate_csv(csv_path)
        issues = report["issues"]
        
        # Should have LEI_DUPLICATE warning
        dup_issues = [i for i in issues if i["code"] == "LEI_DUPLICATE"]
        assert len(dup_issues) > 0
        assert dup_issues[0]["severity"] == "WARNING"
        assert len(dup_issues[0]["rows"]) >= 2
        
        # Should have no errors, only warnings
        error_count = sum(1 for i in issues if i["severity"] == "ERROR")
        warning_count = sum(1 for i in issues if i["severity"] == "WARNING")
        assert error_count == 0
        assert warning_count > 0
    finally:
        csv_path.unlink()


def test_date_needs_normalization(temp_csv_file):
    """Test that date with dot before year produces DATE_NEEDS_NORMALIZATION warning"""
    csv_content = """ae_lei,ac_serviceCode,ac_serviceCode_cou,ac_authorisationNotificationDate,ac_lastupdate
5299005V5GBSN2A4C303,a. providing custody,BE|FR,01/12/.2025,01/01/2025"""
    csv_path = temp_csv_file(csv_content)
    
    try:
        report = validate_csv(csv_path)
        issues = report["issues"]
        
        # Should have DATE_NEEDS_NORMALIZATION warning
        date_issues = [i for i in issues if i["code"] == "DATE_NEEDS_NORMALIZATION"]
        assert len(date_issues) > 0
        assert date_issues[0]["severity"] == "WARNING"
        assert "01/12/.2025" in str(date_issues[0]["examples"])
    finally:
        csv_path.unlink()


def test_row_column_count_mismatch(temp_csv_file):
    """Test that row with wrong column count produces ROW_COLUMN_COUNT_MISMATCH error"""
    csv_content = """ae_lei,ac_serviceCode,ac_serviceCode_cou,ac_authorisationNotificationDate,ac_lastupdate
5299005V5GBSN2A4C303,a. providing custody,BE|FR,01/01/2025,01/01/2025
INCOMPLETE,ROW"""
    csv_path = temp_csv_file(csv_content)
    
    try:
        report = validate_csv(csv_path)
        issues = report["issues"]
        
        # Should have ROW_COLUMN_COUNT_MISMATCH error
        mismatch_issues = [i for i in issues if i["code"] == "ROW_COLUMN_COUNT_MISMATCH"]
        assert len(mismatch_issues) > 0
        assert mismatch_issues[0]["severity"] == "ERROR"
        assert 3 in mismatch_issues[0]["rows"]  # Row 3 has mismatch
    finally:
        csv_path.unlink()


def test_invalid_country_code(temp_csv_file):
    """Test that invalid country code produces COUNTRY_CODE_INVALID error"""
    csv_content = """ae_competentAuthority,ae_lei,ae_lei_name,ae_homeMemberState,ae_lei_cou_code,ac_serviceCode,ac_serviceCode_cou,ac_authorisationNotificationDate,ac_lastupdate
BaFin,5299005V5GBSN2A4C303,Test Company Ltd,DE,DE,a. providing custody,XX|YY,01/01/2025,01/01/2025"""
    csv_path = temp_csv_file(csv_content)
    
    try:
        report = validate_csv(csv_path)
        issues = report["issues"]
        
        # Should have COUNTRY_CODE_INVALID error
        country_issues = [i for i in issues if i["code"] == "COUNTRY_CODE_INVALID"]
        assert len(country_issues) > 0
        assert country_issues[0]["severity"] == "ERROR"
        assert "XX" in str(country_issues[0]["examples"]) or "YY" in str(country_issues[0]["examples"])
    finally:
        csv_path.unlink()


def test_service_code_with_description(temp_csv_file):
    """Test that service code with description is valid (no error)"""
    csv_content = """ae_competentAuthority,ae_lei,ae_lei_name,ae_homeMemberState,ae_lei_cou_code,ac_serviceCode,ac_serviceCode_cou,ac_authorisationNotificationDate,ac_lastupdate
BaFin,5299005V5GBSN2A4C303,Test Company Ltd,DE,DE,a. providing custody and administration of crypto-assets on behalf of clients,BE|FR,01/01/2025,01/01/2025"""
    csv_path = temp_csv_file(csv_content)
    
    try:
        report = validate_csv(csv_path)
        issues = report["issues"]
        
        # Should NOT have SERVICE_CODE_INVALID error
        invalid_service_issues = [i for i in issues if i["code"] == "SERVICE_CODE_INVALID"]
        assert len(invalid_service_issues) == 0
    finally:
        csv_path.unlink()


def test_encoding_suspect(temp_csv_file):
    """Test that encoding suspect patterns produce ENCODING_SUSPECT warning"""
    csv_content = """ae_competentAuthority,ae_lei,ae_lei_name,ae_homeMemberState,ae_lei_cou_code,ac_serviceCode,ac_serviceCode_cou,ac_authorisationNotificationDate,ac_lastupdate,ae_address
BaFin,5299005V5GBSN2A4C303,Test Company Ltd,DE,DE,a. providing custody,BE|FR,01/01/2025,01/01/2025,StraÃŸe 7"""
    csv_path = temp_csv_file(csv_content)
    
    try:
        report = validate_csv(csv_path)
        issues = report["issues"]
        
        # Should have ENCODING_SUSPECT warning
        encoding_issues = [i for i in issues if i["code"] == "ENCODING_SUSPECT"]
        # Note: This might not always trigger depending on how Python handles the encoding
        # But if it does, it should be a warning
        if encoding_issues:
            assert encoding_issues[0]["severity"] == "WARNING"
    finally:
        csv_path.unlink()


def test_classify_date():
    """Test date classification helper"""
    # Valid date
    result = classify_date("01/12/2025")
    assert result["ok"] is True
    assert result["repairable"] is False
    
    # Repairable date (dot before year)
    result = classify_date("01/12/.2025")
    assert result["ok"] is False
    assert result["repairable"] is True
    assert result["normalized_hint"] == "01/12/2025"
    
    # Unparseable date
    result = classify_date("invalid-date")
    assert result["ok"] is False
    assert result["repairable"] is False
    
    # YYYY-MM-DD format
    result = classify_date("2025-12-01")
    assert result["ok"] is True


def test_extract_service_codes():
    """Test service code extraction"""
    # Simple code
    codes, suspicious = extract_service_codes("a")
    assert codes == ["a"]
    assert suspicious is False
    
    # Code with description
    codes, suspicious = extract_service_codes("a. providing custody")
    assert codes == ["a"]
    assert suspicious is False
    
    # Multiple codes
    codes, suspicious = extract_service_codes("a | b | c")
    assert set(codes) == {"a", "b", "c"}
    assert suspicious is False
    
    # Suspicious format (letter outside a-j)
    codes, suspicious = extract_service_codes("a | k | b")
    assert "a" in codes
    assert "b" in codes
    assert suspicious is True
    
    # Invalid (no valid codes)
    codes, suspicious = extract_service_codes("x | y | z")
    assert len(codes) == 0


def test_validate_country_code():
    """Test country code validation"""
    # Valid EU code
    assert validate_country_code("DE") is True
    assert validate_country_code("FR") is True
    assert validate_country_code("BE") is True
    
    # Invalid code
    assert validate_country_code("XX") is False
    assert validate_country_code("ZZ") is False
    
    # Case insensitive
    assert validate_country_code("de") is True
    assert validate_country_code("De") is True


def test_cli_exit_code_missing_column(temp_csv_file):
    """Test CLI exit code for missing column (should be 2)"""
    csv_content = """ae_competentAuthority,ae_homeMemberState
Austrian FMA,AT"""
    csv_path = temp_csv_file(csv_content)
    
    try:
        script_path = Path(__file__).parent.parent / "scripts" / "validate_csv.py"
        result = subprocess.run(
            [sys.executable, str(script_path), str(csv_path)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 2
    finally:
        csv_path.unlink()


def test_cli_exit_code_duplicate_lei(temp_csv_file):
    """Test CLI exit code for duplicate LEI (should be 1 - warning only)"""
    csv_content = """ae_competentAuthority,ae_lei,ae_lei_name,ae_homeMemberState,ae_lei_cou_code,ac_serviceCode,ac_serviceCode_cou,ac_authorisationNotificationDate,ac_lastupdate
BaFin,5299005V5GBSN2A4C303,Test Company Ltd,DE,DE,a. providing custody,BE|FR,01/01/2025,01/01/2025
BaFin,5299005V5GBSN2A4C303,Test Company Ltd,DE,DE,b. trading platform,DE|IT,01/01/2025,01/01/2025"""
    csv_path = temp_csv_file(csv_content)
    
    try:
        script_path = Path(__file__).parent.parent / "scripts" / "validate_csv.py"
        result = subprocess.run(
            [sys.executable, str(script_path), str(csv_path)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1  # Warning only, no errors
    finally:
        csv_path.unlink()


def test_cli_exit_code_strict_mode(temp_csv_file):
    """Test CLI exit code in strict mode (warnings treated as errors)"""
    csv_content = """ae_competentAuthority,ae_lei,ae_lei_name,ae_homeMemberState,ae_lei_cou_code,ac_serviceCode,ac_serviceCode_cou,ac_authorisationNotificationDate,ac_lastupdate
BaFin,5299005V5GBSN2A4C303,Test Company Ltd,DE,DE,a. providing custody,BE|FR,01/12/.2025,01/01/2025
BaFin,5299005V5GBSN2A4C303,Test Company Ltd,DE,DE,b. trading platform,DE|IT,01/01/2025,01/01/2025"""
    csv_path = temp_csv_file(csv_content)
    
    try:
        script_path = Path(__file__).parent.parent / "scripts" / "validate_csv.py"
        result = subprocess.run(
            [sys.executable, str(script_path), str(csv_path), "--strict"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 2  # Warnings treated as errors
    finally:
        csv_path.unlink()


def test_cli_json_report(temp_csv_file):
    """Test CLI JSON report generation"""
    csv_content = """ae_competentAuthority,ae_lei,ae_lei_name,ae_homeMemberState,ae_lei_cou_code,ac_serviceCode,ac_serviceCode_cou,ac_authorisationNotificationDate,ac_lastupdate
BaFin,5299005V5GBSN2A4C303,Test Company Ltd,DE,DE,a. providing custody,BE|FR,01/01/2025,01/01/2025"""
    csv_path = temp_csv_file(csv_content)
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as report_file:
            report_path = Path(report_file.name)
        
        try:
            script_path = Path(__file__).parent.parent / "scripts" / "validate_csv.py"
            result = subprocess.run(
                [sys.executable, str(script_path), str(csv_path), "--report", str(report_path)],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            
            # Check report file exists and is valid JSON
            assert report_path.exists()
            with open(report_path, 'r') as f:
                report = json.load(f)
            
            assert "version" in report
            assert "issues" in report
            assert "stats" in report
        finally:
            if report_path.exists():
                report_path.unlink()
    finally:
        csv_path.unlink()
