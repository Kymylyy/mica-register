# MiCA Register - Test Suite Documentation

This directory contains a comprehensive test suite for the MiCA Register application, verifying data completeness and correctness across the entire pipeline: **CSV → Database → API → Frontend**.

## Overview

The test suite verifies that:
1. **ALL fields** from CSV files are correctly imported to the database
2. **ALL fields** from the database are exposed through the API
3. **ALL fields** from the API are configurable on the frontend
4. **NO DATA LOSS** occurs anywhere in the pipeline
5. **Data transformations** (dates, booleans, pipe-separated values) are correct

## Test Structure

```
tests/
├── conftest.py                      # Pytest configuration and fixtures
├── fixtures/
│   └── test_csvs/                   # Sample CSV files (5-10 rows each)
│       ├── casp_sample.csv
│       ├── other_sample.csv
│       ├── art_sample.csv
│       ├── emt_sample.csv
│       └── ncasp_sample.csv
├── unit/                            # Unit tests
│   ├── test_data_transformations.py # Date parsing, boolean parsing, etc.
│   └── test_models.py               # SQLAlchemy model properties
└── integration/                     # Integration tests
    ├── test_csv_to_db.py            # CSV → Database import
    ├── test_db_to_api.py            # Database → API exposure
    └── test_field_completeness.py   # ⭐ CRITICAL: Full pipeline test
```

## Running Tests

### Backend Tests

```bash
# From project root
cd /Users/Kymyly/Desktop/GIT/mica-register

# Run all tests
python3 -m pytest tests/ -v

# Run specific test file
python3 -m pytest tests/unit/test_data_transformations.py -v

# Run critical completeness test
python3 -m pytest tests/integration/test_field_completeness.py -v

# Run with coverage
python3 -m pytest tests/ --cov=backend/app --cov-report=html --cov-report=term

# Run tests for specific register
python3 -m pytest tests/integration/test_csv_to_db.py::TestCaspCsvImport -v
```

### Frontend Tests

```bash
# From frontend directory
cd frontend

# Run all tests
npm test

# Run with UI
npm run test:ui

# Run with coverage
npm run test:coverage

# Run specific test file
npm test -- src/__tests__/unit/utils/registerColumns.test.js

# Watch mode (auto-rerun on changes)
npm test -- --watch
```

## Test Categories

### 1. Unit Tests - Data Transformations

**File**: `tests/unit/test_data_transformations.py`

Tests individual transformation functions:
- `parse_date()`: DD/MM/YYYY → date object, handles ".2025" format
- `parse_yes_no()`: "YES"/"NO" → boolean
- `normalize_service_code()`: "a. description" → "a"
- Pipe-separated value parsing: "BE|FR|DE" → ["BE", "FR", "DE"]
- Unicode/encoding preservation: German umlauts, French accents

### 2. Unit Tests - Models

**File**: `tests/unit/test_models.py`

Tests SQLAlchemy model properties:
- Entity base model creation
- CASP-specific properties (services, passport_countries, website_platform)
- OTHER-specific properties (lei_casp linkage, dti_ffg)
- ART-specific properties (credit_institution)
- EMT-specific properties (exemption_48_4, exemption_48_5)
- NCASP-specific properties (websites, infringement)

### 3. Integration Tests - CSV to Database

**File**: `tests/integration/test_csv_to_db.py`

Verifies CSV import to database for **all 5 registers**:

#### TestCaspCsvImport
- All CASP fields imported
- Service codes properly parsed (a-j)
- Passport countries properly parsed (pipe-separated)
- Dates properly parsed (DD/MM/YYYY)
- Entity properties accessible

#### TestOtherCsvImport
- All OTHER fields imported
- LEI_CASP linkage preserved
- Pipe-separated fields (offer_countries, dti_codes)
- Boolean fields (dti_ffg)
- Entities without LEI handled

#### TestArtCsvImport, TestEmtCsvImport, TestNcaspCsvImport
- Similar comprehensive coverage for each register

### 4. Integration Tests - Database to API

**File**: `tests/integration/test_db_to_api.py`

Verifies API exposure of **all database fields**:

#### TestCaspApiSchema
- All CASP fields in API response
- Services as list of objects
- Passport countries as list of objects
- Dates in ISO format (YYYY-MM-DD)
- Properties exposed through Entity

#### TestOtherApiSchema, TestArtApiSchema, TestEmtApiSchema, TestNcaspApiSchema
- Similar comprehensive coverage for each register

### 5. ⭐ Integration Tests - Field Completeness (CRITICAL)

**File**: `tests/integration/test_field_completeness.py`

**This is the MOST IMPORTANT test file** - it verifies the **entire pipeline** for all 5 registers.

#### What it tests:
```
CSV → Database → API
  ↓       ↓       ↓
Value → Import → Transform → Expose
```

#### Key Features:
- **Parametrized for all 5 registers**: Single test runs for CASP, OTHER, ART, EMT, NCASP
- **Uses column mappings as source of truth**: `CASP_COLUMNS`, `OTHER_COLUMNS`, etc.
- **Handles transformations correctly**:
  - Dates: `"15/01/2025"` (CSV) → `"2025-01-15"` (API)
  - Booleans: `"YES"` (CSV) → `true` (API)
  - Services: `"a|e"` (CSV) → `[{code:"a"}, {code:"e"}]` (API)
  - Pipe-separated: `"BE|FR"` → maintains set equality

#### Example Test Flow:
```python
1. Read CSV first row
2. Import to DB
3. Fetch through API
4. For each column in column_mapping:
   - CSV has value → API must have transformed value
   - Verify transformation is correct
   - Report any mismatches
```

### 6. Frontend Tests - Column Configuration

**File**: `frontend/src/__tests__/unit/utils/registerColumns.test.js`

Verifies that **all API fields** are configured in `registerColumns.js`:

#### Tests for each register:
- All fields from API are in column configuration
- Each column has required properties (id, label, description, visible)
- Default visibility is correct
- No duplicate column IDs

#### Example:
```javascript
test('all CASP fields are in registerColumns config', () => {
  const columns = getRegisterColumns('casp');
  expect(columns.map(c => c.id)).toContain('services');
  expect(columns.map(c => c.id)).toContain('passport_countries');
});
```

## Test Data (Fixtures)

### Sample CSV Files

Located in `tests/fixtures/test_csvs/`, each file contains 5-10 rows with:

**Important**: All sample CSVs must be **cleaned** (no BOM, proper UTF-8 encoding), as `import_csv_to_db()` expects cleaned input.

#### `casp_sample.csv`
- Multiple entities with various service codes (a, e, f, etc.)
- Entities with multiple passport countries
- Some with `authorisation_end_date`, some without
- Various dates to test parsing

#### `other_sample.csv`
- Entities with and without LEI (common in OTHER)
- LEI_CASP linkages to CASP entities
- Pipe-separated `offer_countries` and `dti_codes`
- Both `dti_ffg = YES` and `dti_ffg = NO`

#### `art_sample.csv`
- Entities with `credit_institution = YES` and `NO`
- White paper URLs and offer countries
- Some with `authorisation_end_date`

#### `emt_sample.csv`
- Various exemption combinations (48.4 and 48.5)
- DTI fields populated
- White paper notification dates

#### `ncasp_sample.csv`
- Entities without LEI (very common)
- Multiple websites (pipe-separated)
- Infringement details and decision dates

## Key Testing Principles

### 1. NOT 1:1 String Comparison

Field completeness tests **cannot** do simple string matching because:
- Dates are transformed: `DD/MM/YYYY` → `YYYY-MM-DD`
- Booleans are transformed: `"YES"` → `true`
- Services are transformed: `"a|e"` → `[{code:"a"}, {code:"e"}]`

### 2. Transformation Functions

Tests use dedicated helper functions:
- `_assert_date_matches()`: Compares dates after parsing
- `_assert_boolean_matches()`: Compares booleans after parsing
- `_assert_services_match()`: Compares service code sets
- `_assert_pipe_separated_matches()`: Compares pipe-separated values

### 3. Source of Truth

The test suite uses **`backend/app/config/registers.py`** as the authoritative source:
- `CASP_COLUMNS`, `OTHER_COLUMNS`, `ART_COLUMNS`, `EMT_COLUMNS`, `NCASP_COLUMNS`
- These define the exact CSV → DB field mappings
- Tests iterate over these to ensure completeness

## Coverage Goals

### Backend Coverage Targets:
- `import_csv.py`: **90%+**
- `models.py`: **85%+**
- `schemas.py`: **80%+**
- `routers/entities.py`: **80%+**
- Overall: **80%+**

### Frontend Coverage Targets:
- `registerColumns.js`: **90%+**
- `DataTable.jsx`: **70%+** (UI components harder to test)
- Overall: **70%+**

## Common Issues & Solutions

### Issue: Pandas Architecture Error
**Error**: `ImportError: ... (have 'x86_64', need 'arm64e' or 'arm64')`

**Solution**: Reinstall pandas for ARM architecture:
```bash
pip uninstall pandas
pip install --no-cache-dir pandas
```

### Issue: Test Fails with "Field Missing"
**Symptom**: Test reports field is missing from API

**Debug Steps**:
1. Check if field exists in CSV sample
2. Verify import in `import_csv.py`
3. Check model properties in `models.py`
4. Verify schema in `schemas.py`
5. Check API response with: `curl http://localhost:8000/api/entities?register_type=casp&limit=1`

### Issue: Date Transformation Fails
**Symptom**: Date mismatch in `test_field_completeness.py`

**Debug**:
- Check CSV date format (should be DD/MM/YYYY)
- Verify `parse_date()` handles `.2025` format
- Check API returns ISO format (YYYY-MM-DD)

### Issue: Frontend Tests Fail to Import
**Symptom**: `Cannot find module '@/...'`

**Solution**: Check `vitest.config.js` has correct path alias:
```javascript
resolve: {
  alias: {
    '@': path.resolve(__dirname, './src'),
  },
}
```

## Adding New Tests

### Adding a Test for a New Field

1. **Update CSV fixture** (`tests/fixtures/test_csvs/`):
   ```csv
   # Add column with sample data
   ```

2. **Run existing tests** to verify field is imported:
   ```bash
   pytest tests/integration/test_field_completeness.py -v
   ```

3. **If field is register-specific**, add assertion to appropriate test:
   ```python
   # In test_casp_specific_fields_in_api()
   assert 'new_field' in entity
   ```

### Adding a Test for a New Transformation

1. **Add unit test** in `test_data_transformations.py`:
   ```python
   def test_parse_new_format(self):
       result = parse_new_format("input")
       assert result == expected_output
   ```

2. **Add transformation handler** in `test_field_completeness.py`:
   ```python
   def _assert_new_field_matches(csv_value, api_value):
       # Transform and compare
       pass
   ```

## Maintenance

### When to Update Tests

1. **Adding a new field to a register**:
   - Update CSV sample with new field
   - Tests will automatically check it (parametrized)
   - Add to column config test if needed

2. **Changing field name**:
   - Update `registers.py` column mapping
   - Update CSV fixtures
   - Tests use column mapping, so will adapt automatically

3. **Adding a new register**:
   - Add sample CSV
   - Add to `conftest.py` fixtures
   - Parametrize existing tests with new register

### Test Data Maintenance

Sample CSVs should be updated when:
- ESMA changes CSV structure
- New fields are added
- Edge cases are discovered

Keep sample data **realistic** but **minimal** (5-10 rows).

## CI/CD Integration (Optional)

To add tests to CI/CD pipeline, create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r backend/requirements.txt
      - run: pip install pytest pytest-cov
      - run: pytest tests/ --cov=backend/app --cov-report=xml
      - uses: codecov/codecov-action@v3

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd frontend && npm ci
      - run: cd frontend && npm test -- --run
      - run: cd frontend && npm run test:coverage
```

## Resources

- **Pytest Documentation**: https://docs.pytest.org/
- **Vitest Documentation**: https://vitest.dev/
- **Testing Library**: https://testing-library.com/
- **SQLAlchemy Testing**: https://docs.sqlalchemy.org/en/20/orm/session_transaction.html

## Contact

For questions about the test suite, refer to:
- `tests/conftest.py` - Test configuration
- `tests/integration/test_field_completeness.py` - Core pipeline test
- This README

---

**Last Updated**: 2026-01-30
**Test Framework Versions**: pytest 8.1.1, vitest 3.2.4
**Python Version**: 3.11
**Node Version**: 18+
