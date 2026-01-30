# MiCA Register - Testing Quick Start Guide

Quick reference for running tests in the MiCA Register project.

## Prerequisites

### Backend
```bash
pip install pytest pytest-cov httpx faker deepdiff
```

### Frontend
```bash
cd frontend
npm install -D vitest @testing-library/react @testing-library/jest-dom @vitest/ui jsdom msw
```

## Running Tests

### Backend Tests (Python/Pytest)

```bash
# From project root (/Users/Kymyly/Desktop/GIT/mica-register)

# Run ALL tests
pytest

# Run specific test file
pytest tests/unit/test_data_transformations.py

# Run specific test class
pytest tests/integration/test_csv_to_db.py::TestCaspCsvImport

# Run specific test function
pytest tests/integration/test_csv_to_db.py::TestCaspCsvImport::test_all_casp_fields_imported

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=backend/app --cov-report=html

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run critical field completeness test
pytest tests/integration/test_field_completeness.py -v
```

### Frontend Tests (Vitest)

```bash
# From frontend directory
cd frontend

# Run ALL tests
npm test

# Run ALL tests (one-time, no watch)
npm test -- --run

# Run specific test file
npm test -- src/__tests__/unit/utils/registerColumns.test.js

# Run with UI (interactive browser-based)
npm run test:ui

# Run with coverage
npm run test:coverage

# Watch mode (auto-rerun on changes)
npm test -- --watch

# Run tests matching pattern
npm test -- --grep "CASP"
```

## Common Test Commands

### Quick Smoke Test (Run This First!)

```bash
# Backend - run unit tests (fast)
pytest tests/unit/ -v

# Frontend - run all tests
cd frontend && npm test -- --run
```

### Full Test Suite (CI-like)

```bash
# Backend with coverage
pytest tests/ --cov=backend/app --cov-report=html --cov-report=term

# Frontend with coverage
cd frontend && npm run test:coverage
```

### Test Specific Register

```bash
# Backend - CASP only
pytest tests/integration/test_csv_to_db.py::TestCaspCsvImport -v

# Backend - Field completeness for CASP
pytest tests/integration/test_field_completeness.py::test_csv_to_api_completeness[casp] -v
```

### Debug Failing Test

```bash
# Backend - show full traceback
pytest tests/integration/test_field_completeness.py -vv --tb=long

# Backend - stop on first failure
pytest tests/ -x

# Backend - show print statements
pytest tests/unit/test_data_transformations.py -s
```

## Expected Output

### ✅ Successful Backend Test Run

```
========================= test session starts ==========================
platform darwin -- Python 3.11.1, pytest-8.1.1
collected 84 items

tests/unit/test_data_transformations.py .................... [ 26%]
tests/unit/test_models.py ..................                 [ 46%]
tests/integration/test_csv_to_db.py .........................[ 76%]
tests/integration/test_db_to_api.py ...................      [ 99%]
tests/integration/test_field_completeness.py ......         [100%]

========================= 84 passed in 5.23s ===========================
```

### ✅ Successful Frontend Test Run

```
 ✓ src/__tests__/unit/utils/registerColumns.test.js (17 tests) 12ms

 Test Files  1 passed (1)
      Tests  17 passed (17)
   Start at  09:16:51
   Duration  801ms
```

## Troubleshooting

### ❌ Pandas Import Error (Backend)

**Error**:
```
ImportError: ... (have 'x86_64', need 'arm64e' or 'arm64')
```

**Fix**:
```bash
pip uninstall pandas
pip install --no-cache-dir pandas
```

### ❌ Module Not Found (Backend)

**Error**:
```
ModuleNotFoundError: No module named 'backend'
```

**Fix**: Make sure you're running from project root:
```bash
cd /Users/Kymyly/Desktop/GIT/mica-register
pytest
```

### ❌ Cannot Find Module '@/...' (Frontend)

**Error**:
```
Cannot find module '@/config/registerColumns'
```

**Fix**: Check `vitest.config.js` has correct path alias. Already configured in this project.

### ❌ ResizeObserver Not Defined (Frontend)

**Error**:
```
ReferenceError: ResizeObserver is not defined
```

**Fix**: Already fixed in `src/__tests__/setup.js` with mock.

## Test Files Overview

### Backend Tests

| File | Tests | Purpose |
|------|-------|---------|
| `test_data_transformations.py` | 23 | Date/boolean/service parsing |
| `test_models.py` | 17 | SQLAlchemy model properties |
| `test_csv_to_db.py` | 25 | CSV import to database |
| `test_db_to_api.py` | 19 | Database to API exposure |
| `test_field_completeness.py` ⭐ | 6 | **CRITICAL: Full pipeline** |

### Frontend Tests

| File | Tests | Purpose |
|------|-------|---------|
| `registerColumns.test.js` | 17 | Column configuration completeness |

## Coverage Reports

### View Coverage (After Running Tests)

**Backend**:
```bash
# Generate HTML report
pytest --cov=backend/app --cov-report=html

# Open in browser
open htmlcov/index.html
```

**Frontend**:
```bash
# Generate coverage
npm run test:coverage

# Open in browser
open coverage/index.html
```

## Integration with IDE

### VS Code

Add to `.vscode/settings.json`:
```json
{
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "vitest.enable": true
}
```

Then use Testing sidebar (beaker icon) to run tests.

### PyCharm

1. Right-click on `tests/` folder
2. Select "Run 'pytest in tests'"
3. Or use green play buttons next to test functions

## Continuous Testing

### Watch Mode (Auto-run on changes)

**Frontend**:
```bash
cd frontend
npm test -- --watch
```

**Backend** (using pytest-watch, if installed):
```bash
pip install pytest-watch
ptw tests/
```

## Quick Test Checklist

Before committing code, run:

- [ ] `pytest tests/unit/` - Unit tests (fast)
- [ ] `pytest tests/integration/test_field_completeness.py` - Critical completeness
- [ ] `cd frontend && npm test -- --run` - Frontend tests

All tests passing? ✅ Ready to commit!

## Test Development

### Add a New Test

```python
# tests/unit/test_my_feature.py
import pytest

def test_my_feature():
    """Test description"""
    # Arrange
    input_data = "test"

    # Act
    result = my_function(input_data)

    # Assert
    assert result == expected_output
```

### Run New Test

```bash
pytest tests/unit/test_my_feature.py -v
```

## Getting Help

- **Full documentation**: See `tests/README.md`
- **Implementation summary**: See `TESTING_SUMMARY.md`
- **This quick start**: `TESTING_QUICK_START.md`

---

**Last Updated**: 2026-01-30
