# TODO: Automatyzacja procesu aktualizacji danych ESMA

## 🎯 Cel

Zamknięcie całej logiki sprawdzania strony WWW ESMA, pobierania pliku CSV, przeprowadzenia walidacji, czyszczenia i importu do bazy danych w jeden zautomatyzowany proces, który będzie można uruchomić jako cron job.

## 📋 Zakres zadania

### 1. Sprawdzanie strony ESMA i pobieranie pliku

- [ ] Implementacja sprawdzania strony ESMA pod kątem nowych aktualizacji
- [ ] Automatyczne wykrywanie nowego pliku CSV (porównanie dat publikacji)
- [ ] Pobieranie najnowszego pliku CSV z ESMA
- [ ] Zapisywanie pliku w `data/raw/` z odpowiednią nazwą (format: `CASPYYYYMMDD.csv`)

### 2. Pełny pipeline przetwarzania

- [ ] Walidacja surowego pliku CSV → `reports/validation/raw/`
- [ ] Deterministic cleaning → `data/cleaned/` + `reports/cleaning/`
- [ ] Walidacja wyczyszczonego pliku → `reports/validation/clean/`
- [ ] (Opcjonalnie) LLM Remediation dla pozostałych błędów:
  - Generowanie zadań remediacji → `reports/remediation/tasks/`
  - Uruchomienie LLM remediation → `reports/remediation/patches/`
  - Zastosowanie patch'a → `data/cleaned/` + `reports/remediation/apply/`
- [ ] Finalna walidacja → `reports/validation/final/` (MUSI przejść)
- [ ] Import do bazy danych (lokalnie lub przez API endpoint)

### 3. Skrypt automatyzacji

- [x] Utworzenie głównego skryptu `scripts/update_esma_data.py` (lub `.sh`)
- [x] Integracja wszystkich kroków pipeline'u (sprawdzanie ESMA, pobieranie, walidacja, cleaning, LLM)
- [x] Obsługa błędów i logowanie
- [ ] Automatyczny commit i push do GitHub
- [ ] Automatyczne wywołanie Railway API importu
- [ ] Notyfikacje (email/Slack/webhook) z raportem
- [ ] Konfiguracja przez plik `.env` lub `config.yaml`

### 4. Cron Job Setup

- [ ] Konfiguracja dla Linux/macOS (crontab)
- [ ] Konfiguracja dla Railway (Railway Cron Jobs)
- [ ] Konfiguracja dla GitHub Actions (`.github/workflows/update_esma_data.yml`)
- [ ] Dokumentacja konfiguracji cron job

### 5. Testy i dokumentacja

- [ ] Testy jednostkowe dla poszczególnych kroków
- [ ] Testy integracyjne dla pełnego pipeline'u
- [ ] Dokumentacja w `UPDATE_DATA.md`
- [ ] Przykłady konfiguracji cron job

## 🔧 Wymagania techniczne

### Zależności

- Python 3.11+
- Biblioteki do web scraping (np. `requests`, `beautifulsoup4`)
- Wszystkie istniejące zależności z `backend/requirements.txt`
- `python-dotenv` dla konfiguracji

### Konfiguracja

Plik `.env` powinien zawierać:
```env
# Database
DATABASE_URL=postgresql://user:password@host:port/database

# LLM Remediation (opcjonalne)
GEMINI_API_KEY=your_api_key_here

# ESMA Configuration
ESMA_REGISTER_URL=https://www.esma.europa.eu/...
ESMA_CSV_DOWNLOAD_URL=...

# Notifications (opcjonalne)
SLACK_WEBHOOK_URL=...
EMAIL_NOTIFICATION=admin@example.com

# Cron Job Configuration
CRON_SCHEDULE=0 2 * * *  # Daily at 2 AM
TIMEZONE=Europe/Warsaw
```

### Struktura skryptu

```python
# scripts/update_esma_data.py
def main():
    # 1. Check ESMA for updates
    # 2. Download CSV if new version available
    # 3. Validate raw CSV
    # 4. Clean CSV
    # 5. Validate cleaned CSV
    # 6. (Optional) LLM Remediation
    # 7. Final validation
    # 8. Import to database
    # 9. Send notifications
    # 10. Log results
```

## 📝 Deliverables

1. **Skrypt automatyzacji**: `scripts/update_esma_data.py`
2. **Konfiguracja cron job**: `.github/workflows/update_esma_data.yml`
3. **Dokumentacja**: Zaktualizowany `UPDATE_DATA.md` z sekcją o automatyzacji
4. **Testy**: Testy dla pełnego pipeline'u
5. **Konfiguracja**: Przykłady konfiguracji dla różnych środowisk

## 🎯 Success Criteria

- ✅ Skrypt automatycznie sprawdza ESMA i pobiera nowy plik
- ✅ Pełny pipeline (walidacja → cleaning → LLM) działa automatycznie
- ⏳ Automatyczny commit/push i Railway import (w trakcie)
- ⏳ Cron job uruchamia się zgodnie z harmonogramem (planowane)
- ⏳ Notyfikacje są wysyłane po każdej aktualizacji (planowane)
- ✅ Wszystkie błędy są logowane i raportowane
- ✅ Pipeline kończy się sukcesem lub bezpiecznie przerywa w przypadku błędów

## ⏱️ Szacowany czas

- **Sprawdzanie ESMA i pobieranie**: 4-6 godzin
- **Integracja pipeline'u**: 3-4 godziny
- **Cron job setup**: 2-3 godziny
- **Testy i dokumentacja**: 3-4 godziny

**Total**: ~12-17 godzin

## 🔗 Powiązane pliki

- `scripts/validate_csv.py` - walidacja CSV
- `scripts/clean_csv.py` - czyszczenie CSV
- `scripts/generate_remediation_tasks.py` - generowanie zadań LLM
- `scripts/run_llm_remediation.py` - uruchomienie LLM remediation
- `scripts/apply_remediation_patch.py` - zastosowanie patch'a
- `backend/app/routers/entities.py` - endpoint `/api/admin/import`
- `UPDATE_DATA.md` - dokumentacja procesu aktualizacji

---

**Status**: 🟢 Partially Implemented (orchestration script ready, full automation pending)  
**Last Updated**: 2025-12-30  
**Priority**: High
