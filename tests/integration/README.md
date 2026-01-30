# Integration Tests

## Automated Tests

Testy automatyczne pytest (uruchamiane przez CI/CD):
- Standardowe pliki `test_*.py` w tym katalogu
- Uruchamiane automatycznie przez pytest

Uruchom:
```bash
# Wszystkie testy integracyjne
pytest tests/integration/ -v

# Konkretny test
pytest tests/integration/test_specific.py -v
```

## Manual Test Scripts

Skrypty testowe do ręcznego uruchomienia (NIE są zbierane przez pytest):
- `manual_casp_import.py` - Ręczny test pełnego pipeline'u importu CASP (clean → import → verify)
- `manual_casp_structure.py` - Ręczny test struktury po refaktorze (imports, schema, models)

### Dlaczego "manual_*.py"?

Pliki `manual_*.py` to skrypty diagnostyczne/testowe, które:
- Wykonują operacje na prawdziwej bazie danych
- Importują duże ilości danych
- Mają długi czas wykonania
- Wymagają ręcznej weryfikacji wyników

Nie używają nazewnictwa `test_*.py`, aby pytest ich automatycznie nie zbierał.

### Uruchomienie

```bash
# Manual CASP import test (pełny pipeline)
python tests/integration/manual_casp_import.py

# Manual CASP structure test (weryfikacja modeli)
python tests/integration/manual_casp_structure.py
```

## Dodawanie Nowych Testów

**Automatyczne testy:** Użyj nazwy `test_*.py` i pytest automatycznie je znajdzie.

**Manualne skrypty:** Użyj nazwy `manual_*.py` aby uniknąć automatycznego uruchamiania.
