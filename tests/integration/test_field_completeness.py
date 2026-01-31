"""
⭐ CRITICAL TEST: Field Completeness across entire pipeline (CSV → DB → API)

This test verifies that NO DATA IS LOST in the complete data flow:
CSV → Database → API → Frontend

IMPORTANT: This is NOT a 1:1 string comparison!
- Dates: CSV has DD/MM/YYYY (e.g. "15/01/2025"), API has ISO (e.g. "2025-01-15")
- Services: CSV has pipe-separated (e.g. "a|e"), API has list of objects
- Booleans: CSV has "YES"/"NO", API has true/false
- Pipe-separated values: CSV has strings, API may have lists or strings

The test uses transformation functions to compare values correctly.
"""

import pytest
import pandas as pd
from datetime import date

from backend.app.import_csv import import_csv_to_db, normalize_service_code, parse_date
from backend.app.config.registers import (
    RegisterType,
    CASP_COLUMNS, OTHER_COLUMNS, ART_COLUMNS, EMT_COLUMNS, NCASP_COLUMNS,
    parse_yes_no
)


# Parametrize test for all 5 registers
@pytest.mark.parametrize("register_type,csv_fixture,column_mapping", [
    (RegisterType.CASP, "casp_sample_csv", CASP_COLUMNS),
    (RegisterType.OTHER, "other_sample_csv", OTHER_COLUMNS),
    (RegisterType.ART, "art_sample_csv", ART_COLUMNS),
    (RegisterType.EMT, "emt_sample_csv", EMT_COLUMNS),
    (RegisterType.NCASP, "ncasp_sample_csv", NCASP_COLUMNS),
])
def test_csv_to_api_completeness(
    db_session, client, register_type, csv_fixture, column_mapping, request
):
    """
    ⭐ CRITICAL: Test field completeness for CSV → DB → API pipeline

    Verifies that EVERY field from CSV reaches the API with proper transformation
    """
    csv_path = request.getfixturevalue(csv_fixture)

    # Read CSV (same way import does it)
    df = pd.read_csv(str(csv_path), encoding='utf-8-sig')
    assert len(df) > 0, f"CSV {csv_fixture} is empty"

    # Get first row for comparison
    csv_first_row = df.iloc[0]

    # Import to DB
    import_csv_to_db(db_session, str(csv_path), register_type)

    # Fetch through API
    response = client.get(f"/api/entities?register_type={register_type.value}&limit=1")
    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert len(data["items"]) > 0, f"No entities returned for {register_type.value}"

    api_entity = data["items"][0]

    # Verify EACH field from column_mapping
    missing_fields = []
    transformation_errors = []

    for csv_col, db_field in column_mapping.items():
        # Skip if column doesn't exist in CSV
        if csv_col not in df.columns:
            continue

        csv_value = csv_first_row[csv_col]

        # If CSV has value, API must also have it (with transformation)
        if pd.notna(csv_value) and str(csv_value).strip():
            api_value = api_entity.get(db_field)

            try:
                _assert_field_matches(
                    csv_value, api_value, csv_col, db_field, register_type
                )
            except AssertionError as e:
                transformation_errors.append(
                    f"Field {csv_col} → {db_field}: {str(e)}"
                )
        elif db_field in api_entity:
            # CSV has no value, but API returns the field (should be null/empty)
            # This is OK - we just want to track that the field exists
            pass

    # Report all errors at once for better debugging
    if transformation_errors:
        error_msg = "\n".join([
            f"Field completeness failures for {register_type.value}:",
            *transformation_errors
        ])
        pytest.fail(error_msg)

    if missing_fields:
        pytest.fail(
            f"Missing fields in API for {register_type.value}: {', '.join(missing_fields)}"
        )


def _assert_field_matches(csv_value, api_value, csv_col, api_field, register_type):
    """
    Compare CSV value with API value, accounting for transformations.

    NOT a simple string comparison!
    """
    # Handle dates: DD/MM/YYYY → YYYY-MM-DD
    if _is_date_field(api_field, csv_col):
        _assert_date_matches(csv_value, api_value, csv_col)
        return

    # Handle booleans: "YES"/"NO" → true/false
    if _is_boolean_field(api_field, register_type):
        _assert_boolean_matches(csv_value, api_value, api_field)
        return

    # Handle services (CASP only): "a|e" → [{"code":"a",...}, {"code":"e",...}]
    if api_field == 'services' and register_type == RegisterType.CASP:
        _assert_services_match(csv_value, api_value)
        return

    # Handle passport countries (CASP only): "BE|FR" → [{"country_code":"BE"}, ...]
    if api_field == 'passport_countries' and register_type == RegisterType.CASP:
        _assert_passport_countries_match(csv_value, api_value)
        return

    # Handle pipe-separated values that stay as strings or become lists
    if api_field in ['offer_countries', 'dti_codes', 'white_paper_offer_countries', 'websites']:
        _assert_pipe_separated_matches(csv_value, api_value, api_field)
        return

    # Regular string comparison (after normalization)
    assert api_value is not None, f"Field {api_field} is None but CSV had: '{csv_value}'"

    # Normalize and compare
    csv_normalized = str(csv_value).strip()
    api_normalized = str(api_value).strip() if api_value else ""

    assert csv_normalized == api_normalized, \
        f"Value mismatch: CSV='{csv_normalized}' vs API='{api_normalized}'"


def _is_date_field(api_field: str, csv_col: str) -> bool:
    """Check if field is a date field"""
    date_indicators = ['date', 'Date', 'lastupdate', 'last_update']
    return any(indicator in api_field for indicator in date_indicators) or \
           any(indicator in csv_col for indicator in date_indicators)


def _is_boolean_field(api_field: str, register_type: RegisterType) -> bool:
    """Check if field is a boolean field"""
    # Note: infringement in NCASP is stored as String in DB, not Boolean
    # Note: dti_ffg is String, not Boolean
    boolean_fields = {
        'credit_institution', 'exemption_48_4', 'exemption_48_5'
    }
    return api_field in boolean_fields


def _assert_date_matches(csv_value, api_value, csv_col):
    """Assert date values match after transformation"""
    if pd.isna(csv_value) or not str(csv_value).strip():
        return

    # Parse CSV date (DD/MM/YYYY format)
    csv_date = parse_date(str(csv_value), "%d/%m/%Y")

    if csv_date is None:
        # If parsing failed, CSV might have invalid date
        return

    # Parse API date (ISO format: YYYY-MM-DD)
    if api_value:
        api_date = date.fromisoformat(api_value) if isinstance(api_value, str) else api_value
        assert csv_date == api_date, \
            f"Date mismatch: CSV '{csv_value}' (parsed: {csv_date}) != API '{api_value}' (parsed: {api_date})"
    else:
        pytest.fail(f"CSV has date '{csv_value}' but API value is None/empty")


def _assert_boolean_matches(csv_value, api_value, api_field):
    """Assert boolean values match after transformation"""
    if pd.isna(csv_value) or not str(csv_value).strip():
        # CSV has no value, API should also be None/null
        return

    expected = parse_yes_no(str(csv_value))
    assert api_value == expected, \
        f"Boolean mismatch for {api_field}: CSV '{csv_value}' (expected: {expected}) != API {api_value}"


def _assert_services_match(csv_value, api_value):
    """Assert CASP services match after transformation"""
    if pd.isna(csv_value) or not str(csv_value).strip():
        return

    # Parse CSV: "a. description|e. description" → {"a", "e"}
    csv_codes = set()
    for service_str in str(csv_value).split('|'):
        if service_str.strip():
            code = normalize_service_code(service_str.strip())
            if code:
                csv_codes.add(code)

    # Parse API: [{"code": "a", ...}, {"code": "e", ...}] → {"a", "e"}
    if api_value:
        api_codes = {s['code'] for s in api_value}
        assert csv_codes == api_codes, \
            f"Services mismatch: CSV codes {csv_codes} != API codes {api_codes}"
    else:
        pytest.fail(f"CSV has services '{csv_value}' but API value is None/empty")


def _assert_passport_countries_match(csv_value, api_value):
    """Assert CASP passport countries match after transformation"""
    if pd.isna(csv_value) or not str(csv_value).strip():
        # No countries in CSV
        return

    # Parse CSV: "BE|FR|NL" → {"BE", "FR", "NL"}
    csv_countries = {c.strip() for c in str(csv_value).split('|') if c.strip()}

    # Parse API: [{"country_code": "BE"}, ...] → {"BE", "FR", "NL"}
    if api_value:
        api_countries = {c['country_code'] for c in api_value}
        assert csv_countries == api_countries, \
            f"Passport countries mismatch: CSV {csv_countries} != API {api_countries}"
    else:
        pytest.fail(f"CSV has countries '{csv_value}' but API value is None/empty")


def _assert_pipe_separated_matches(csv_value, api_value, api_field):
    """Assert pipe-separated values match (may be string or list in API)"""
    if pd.isna(csv_value) or not str(csv_value).strip():
        return

    # Parse CSV: "DE|FR|IT" → {"DE", "FR", "IT"}
    csv_items = {item.strip() for item in str(csv_value).split('|') if item.strip()}

    # API may return as string or list
    if isinstance(api_value, list):
        api_items = set(api_value)
    elif isinstance(api_value, str):
        api_items = {item.strip() for item in api_value.split('|') if item.strip()}
    else:
        # API value is None/null but CSV has value
        pytest.fail(f"CSV has pipe-separated '{csv_value}' but API value is None")

    assert csv_items == api_items, \
        f"Pipe-separated mismatch for {api_field}: CSV {csv_items} != API {api_items}"


# Additional tests for register-specific field availability

def test_casp_specific_fields_in_api(client, db_with_casp_data):
    """Verify all CASP-specific fields are available in API"""
    response = client.get("/api/entities?register_type=casp&limit=1")
    assert response.status_code == 200

    entity = response.json()["items"][0]

    # CASP-specific fields
    casp_fields = [
        'services',
        'passport_countries',
        'website_platform',
        'authorisation_end_date'
    ]

    for field in casp_fields:
        assert field in entity, f"CASP field '{field}' missing from API"


def test_other_specific_fields_in_api(client, db_with_other_data):
    """Verify all OTHER-specific fields are available in API"""
    response = client.get("/api/entities?register_type=other&limit=1")
    assert response.status_code == 200

    entity = response.json()["items"][0]

    # OTHER-specific fields
    other_fields = [
        'lei_casp',
        'lei_name_casp',
        'offer_countries',
        'white_paper_url',
        'dti_ffg',
        'dti_codes',
        'white_paper_comments'
    ]

    for field in other_fields:
        assert field in entity, f"OTHER field '{field}' missing from API"


def test_art_specific_fields_in_api(client, db_with_art_data):
    """Verify all ART-specific fields are available in API"""
    response = client.get("/api/entities?register_type=art&limit=1")
    assert response.status_code == 200

    entity = response.json()["items"][0]

    # ART-specific fields
    art_fields = [
        'credit_institution',
        'white_paper_url',
        'white_paper_offer_countries',
        'authorisation_end_date',
        'white_paper_comments'
    ]

    for field in art_fields:
        assert field in entity, f"ART field '{field}' missing from API"


def test_emt_specific_fields_in_api(client, db_with_emt_data):
    """Verify all EMT-specific fields are available in API"""
    response = client.get("/api/entities?register_type=emt&limit=1")
    assert response.status_code == 200

    entity = response.json()["items"][0]

    # EMT-specific fields
    emt_fields = [
        'exemption_48_4',
        'exemption_48_5',
        'authorisation_other_emt',
        'white_paper_notification_date',
        'white_paper_url',
        'dti_ffg',
        'dti_codes',
        'authorisation_end_date',
        'white_paper_comments'
    ]

    for field in emt_fields:
        assert field in entity, f"EMT field '{field}' missing from API"


def test_ncasp_specific_fields_in_api(client, db_with_ncasp_data):
    """Verify all NCASP-specific fields are available in API"""
    response = client.get("/api/entities?register_type=ncasp&limit=1")
    assert response.status_code == 200

    entity = response.json()["items"][0]

    # NCASP-specific fields
    ncasp_fields = [
        'websites',
        'infringement',
        'reason',
        'decision_date'
    ]

    for field in ncasp_fields:
        assert field in entity, f"NCASP field '{field}' missing from API"


def test_no_data_loss_across_multiple_entities(client, db_with_casp_data):
    """Verify field completeness across multiple entities (not just first)"""
    response = client.get("/api/entities?register_type=casp&limit=10")
    assert response.status_code == 200

    entities = response.json()["items"]
    assert len(entities) > 1, "Need multiple entities for this test"

    # All entities should have core fields
    for entity in entities:
        assert "competent_authority" in entity
        assert "home_member_state" in entity
        assert "register_type" in entity
        # CASP specific
        assert "services" in entity
        assert "passport_countries" in entity
