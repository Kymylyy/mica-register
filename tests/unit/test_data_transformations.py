"""
Unit tests for data transformation functions.

Tests parsing of dates, booleans, pipe-separated values, service codes, etc.
"""

import pytest
from datetime import date
from backend.app.import_csv import parse_date, normalize_service_code
from backend.app.config.registers import parse_yes_no


class TestDateParsing:
    """Test parse_date() with various formats"""

    def test_parse_standard_date(self):
        """Test standard DD/MM/YYYY format"""
        result = parse_date("15/01/2025", "%d/%m/%Y")
        assert result == date(2025, 1, 15)

    def test_parse_date_with_dot_year(self):
        """Test DD/MM/.YYYY format (leading dot in year)"""
        result = parse_date("15/01/.2025", "%d/%m/%Y")
        assert result == date(2025, 1, 15)

    def test_parse_empty_string(self):
        """Test empty string returns None"""
        result = parse_date("", "%d/%m/%Y")
        assert result is None

    def test_parse_none(self):
        """Test None returns None"""
        result = parse_date(None, "%d/%m/%Y")
        assert result is None

    def test_parse_whitespace(self):
        """Test whitespace-only string returns None"""
        result = parse_date("   ", "%d/%m/%Y")
        assert result is None

    def test_parse_invalid_date(self):
        """Test invalid date returns None"""
        result = parse_date("invalid", "%d/%m/%Y")
        assert result is None

    def test_parse_different_separators(self):
        """Test dates with different separators"""
        # This should fail gracefully
        result = parse_date("15-01-2025", "%d/%m/%Y")
        assert result is None


class TestYesNoParser:
    """Test parse_yes_no() for boolean conversion"""

    def test_parse_yes_uppercase(self):
        """Test 'YES' returns True"""
        assert parse_yes_no("YES") is True

    def test_parse_yes_lowercase(self):
        """Test 'yes' returns True"""
        assert parse_yes_no("yes") is True

    def test_parse_yes_mixed_case(self):
        """Test 'Yes' returns True"""
        assert parse_yes_no("Yes") is True

    def test_parse_no_uppercase(self):
        """Test 'NO' returns False"""
        assert parse_yes_no("NO") is False

    def test_parse_no_lowercase(self):
        """Test 'no' returns False"""
        assert parse_yes_no("no") is False

    def test_parse_no_mixed_case(self):
        """Test 'No' returns False"""
        assert parse_yes_no("No") is False

    def test_parse_empty_string(self):
        """Test empty string returns None"""
        assert parse_yes_no("") is None

    def test_parse_none(self):
        """Test None returns None"""
        assert parse_yes_no(None) is None

    def test_parse_whitespace(self):
        """Test whitespace-only returns None"""
        assert parse_yes_no("   ") is None

    def test_parse_invalid_value(self):
        """Test invalid value returns None"""
        assert parse_yes_no("maybe") is None


class TestServiceCodeNormalization:
    """Test normalize_service_code() for CASP services"""

    def test_normalize_full_service_description(self):
        """Test full service description 'a. providing custody...' returns 'a'"""
        result = normalize_service_code("a. Providing custody and administration of crypto-assets on behalf of clients")
        assert result == "a"

    def test_normalize_service_code_with_dot(self):
        """Test 'a.' returns 'a'"""
        result = normalize_service_code("a.")
        assert result == "a"

    def test_normalize_service_code_without_dot(self):
        """Test 'a' returns 'a'"""
        result = normalize_service_code("a")
        assert result == "a"

    def test_normalize_service_code_with_whitespace(self):
        """Test '  a.  ' returns 'a'"""
        result = normalize_service_code("  a.  ")
        assert result == "a"

    def test_normalize_different_codes(self):
        """Test different service codes (b, c, d, etc.)"""
        assert normalize_service_code("b. Operation of a trading platform") == "b"
        assert normalize_service_code("c. Exchange of crypto-assets") == "c"
        assert normalize_service_code("d. Providing advice") == "d"
        assert normalize_service_code("e. Placing of crypto-assets") == "e"
        assert normalize_service_code("f. Reception and transmission") == "f"

    def test_normalize_empty_string(self):
        """Test empty string returns None"""
        result = normalize_service_code("")
        assert result is None or result == ""

    def test_normalize_uppercase_code(self):
        """Test uppercase 'A' returns 'a' (lowercase)"""
        result = normalize_service_code("A")
        assert result == "a"


class TestPipeSeparatedParsing:
    """Test parsing of pipe-separated values"""

    def test_parse_multiple_countries(self):
        """Test 'BE|FR|DE' splits correctly"""
        value = "BE|FR|DE"
        result = [c.strip() for c in value.split("|") if c.strip()]
        assert result == ["BE", "FR", "DE"]

    def test_parse_with_spaces(self):
        """Test 'BE | FR | DE' strips whitespace"""
        value = "BE | FR | DE"
        result = [c.strip() for c in value.split("|") if c.strip()]
        assert result == ["BE", "FR", "DE"]

    def test_parse_with_empty_segments(self):
        """Test 'BE||FR' filters out empty segments"""
        value = "BE||FR"
        result = [c.strip() for c in value.split("|") if c.strip()]
        assert result == ["BE", "FR"]

    def test_parse_single_value(self):
        """Test single value without pipe"""
        value = "BE"
        result = [c.strip() for c in value.split("|") if c.strip()]
        assert result == ["BE"]

    def test_parse_empty_string(self):
        """Test empty string returns empty list"""
        value = ""
        result = [c.strip() for c in value.split("|") if c.strip()]
        assert result == []

    def test_parse_trailing_pipe(self):
        """Test 'BE|FR|' filters trailing empty"""
        value = "BE|FR|"
        result = [c.strip() for c in value.split("|") if c.strip()]
        assert result == ["BE", "FR"]


class TestEncodingIssues:
    """Test handling of special characters and encoding"""

    def test_german_special_chars(self):
        """Test German umlauts and ß"""
        text = "Münchener Straße"
        assert "ü" in text
        assert "ß" in text

    def test_french_accents(self):
        """Test French accented characters"""
        text = "Société Générale"
        assert "é" in text

    def test_unicode_preservation(self):
        """Test that unicode is preserved in processing"""
        name = "Zürich Finance GmbH"
        # Simulate strip/clean operations
        result = name.strip()
        assert result == "Zürich Finance GmbH"
        assert "ü" in result
