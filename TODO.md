# TODO: LLM-Assisted Remediation for ESMA CSV Pipeline

## 🎯 Cel

Zaprojektować i zaimplementować komponent "LLM-assisted remediation" dla pipeline normalizacji CSV ESMA. Deterministic cleaning obsługuje typowe przypadki; LLM proponuje poprawki tylko dla rzadkich edge cases z rygorystycznymi guardrails i pełną audytowalnością.

## 📋 Kontekst Repozytorium

- Istniejący importer CSV: `backend/app/import_csv.py` (parse_date, normalize_service_code, merge_entities_by_lei, fix_address_website_parsing, fix_encoding_issues)
- Moduł walidacji: `backend/app/csv_validate.py` (encoding detection, validation)
- Deterministic cleaning: `backend/app/csv_clean.py` (CSVCleaner) produkuje clean.csv + report

## 🏗️ High-Level Pipeline

```
1) download/raw.csv (out of scope)
2) validate(raw) -> report
3) deterministic_clean(raw) -> clean.csv + clean_report.json
4) validate(clean) -> report
5) if validate(clean) still has issues: generate remediation_tasks.json
6) LLM gets remediation_tasks (minimal context), returns remediation_patch.json (proposals)
7) apply_patch(clean.csv, remediation_patch.json) -> clean_llm.csv + llm_apply_report.json
8) validate(clean_llm) MUST pass or abort
9) output final clean.csv (or clean_llm.csv) + full audit reports
```

## 📐 Design Requirements

### Zasady Projektowe

- **Determinism**: Deterministic cleaning jest source of truth. LLM jest opcjonalny i działa tylko gdy są nierozwiązane problemy.
- **Safety**: LLM NIE MOŻE przepisywać dowolnych pól. Dozwolone transformacje muszą być explicit i enforced przez kod.
- **Auditability**: Każda zmiana proponowana przez LLM musi być zalogowana: row identifier, column, old->new, reason, confidence, model metadata.
- **Minimal data sharing**: Nigdy nie wysyłaj całego CSV do LLM. Tylko minimal context per task (single row + selected columns + short excerpt).
- **Output constraints**: Output LLM musi być JSON zgodny z naszym schematem. Walidujemy schema strictly przed zastosowaniem.
- **Apply policy**: Domyślnie zmiany wymagają manual approval LUB możemy auto-apply tylko "low-risk" transformations (configurable).
- **Provider-agnostic**: Design jako interface. Przykład: Gemini API, ale keep it pluggable.
- **Tests**: Unit tests dla: task generation, schema validation, patch application, "guardrails block forbidden edits".

### Edge Cases (Examples)

- **Encoding data loss**: replacement char '' present (e.g., "Strae") -> propose best guess "Straße" BUT mark as low confidence and require manual approval by default.
- **Country codes normalization**: "EL" -> "GR", lower-case "Fi" -> "FI", stripping spaces.
- **Website fixes**: split multiline, add scheme if missing (optional), dedup.
- **Dates**: weird but "repairable" patterns that deterministic cleaner didn't normalize.
- **Address/website column bleed**: that deterministic rules couldn't resolve.

### Forbidden / High-Risk Changes (MUST ENFORCE)

- ❌ **LEI values**: Do not allow LLM to change LEI values except trivial safe trimming (e.g. trailing dot) — and even then prefer deterministic.
- ❌ **New entities**: Do not allow LLM to invent new entities, services, or countries beyond normalization/mapping.
- ❌ **Freeform rewriting**: Do not allow freeform rewriting of legal names/authority names/addresses except minimal encoding repair (and even that is restricted).

## 📦 Deliverables

### A) Design Document

**Plik**: `docs/LLM_REMEDIATION_DESIGN.md`

**Zawartość**:
- Pipeline stages and decision points
- Data minimization strategy
- Allowed transformations policy (table)
- Schemas for tasks and patches
- Failure modes and how we abort safely
- How to run locally (CLI commands)
- Row identification strategy (stable keys vs row numbers)
- Context construction for LLM (which columns, length caps)
- Confidence handling and auto-apply policy

### B) JSON Schemas / Pydantic Models

**Pliki**:
- `backend/app/remediation/schemas.py` - Pydantic models
- `backend/app/remediation/json_schemas/` - JSON Schema files (optional, for validation)

**Wymagane schematy**:

1. **`remediation_tasks.json`** schema:
   - `task_id`: string (UUID)
   - `task_type`: enum (ENCODING_FIX, COUNTRY_NORMALIZE, WEBSITE_FIX, DATE_FIX, ADDRESS_FIX)
   - `row_identifier`: object (stable key: LEI + authority + service_country, or synthetic row_id)
   - `column`: string
   - `current_value`: string (max length: 1000)
   - `issue_description`: string
   - `context`: object (minimal row data: selected columns only, capped lengths)
   - `severity`: enum (ERROR, WARNING)
   - `metadata`: object (validation report reference, row number hint)

2. **`remediation_patch.json`** schema:
   - `patch_id`: string (UUID)
   - `generated_at`: ISO datetime
   - `model_provider`: string (e.g., "gemini", "openai")
   - `model_name`: string (e.g., "gemini-1.5-pro")
   - `tasks`: array of:
     - `task_id`: string (references remediation_tasks)
     - `proposed_value`: string (max length: 1000)
     - `confidence`: float (0.0-1.0)
     - `reasoning`: string (max length: 500)
     - `transformation_type`: enum (must match allowed transformations)
     - `risk_level`: enum (LOW, MEDIUM, HIGH)
   - `metadata`: object (token usage, latency, etc.)

### C) Module Structure

**Struktura katalogów**:
```
backend/app/remediation/
├── __init__.py
├── schemas.py              # Pydantic models for tasks and patches
├── tasks.py                # Generate tasks from validation report + CSV row access
├── policy.py               # Allowed transformations + enforcement (guardrails)
├── llm_client.py           # Provider interface; Gemini example stub
├── patch.py                # Apply patch safely to CSV; produces apply report
└── row_identifier.py       # Stable row identification logic

scripts/
├── generate_remediation_tasks.py    # CLI: CSV + validation report -> tasks.json
├── apply_remediation_patch.py       # CLI: CSV + patch.json -> clean_llm.csv + report
└── run_llm_remediation.py           # CLI: tasks.json -> LLM -> patch.json (optional stub)

tests/
├── test_remediation_tasks.py        # Test task generation
├── test_remediation_policy.py      # Test guardrails and forbidden edits
├── test_remediation_patch.py       # Test patch application and audit logging
├── test_remediation_llm_client.py  # Test LLM client interface (mocked)
└── fixtures/
    └── remediation_test_data.csv   # Small CSV fixtures for testing
```

### D) Implementation Details

#### Row Identification Strategy

**Problem**: Nie możemy polegać na row numbers jeśli merge/dedup.

**Rozwiązanie**: Użyj stable composite key:
- Primary: `ae_lei` (jeśli unikalny)
- Fallback: `ae_lei + ae_competentAuthority + ac_serviceCode_cou` (dla duplikatów LEI)
- Last resort: `synthetic_row_id` generowany podczas cleaning (hash z kluczowych pól)

**Implementacja**: `backend/app/remediation/row_identifier.py`

#### Context Construction for LLM

**Zasady**:
- Tylko potrzebne kolumny dla danego task type
- Max length per column: 500 chars
- Max total context: 2000 chars
- Include: problem column + related columns (np. dla encoding: address, commercial_name)

**Przykład dla ENCODING_FIX**:
```json
{
  "context": {
    "ae_commercial_name": "Bitpanda GmbH",
    "ae_address": "Stella-Klein-Lw-Weg 17, 1020 Vienna",
    "ae_lei": "5493007WZ7IFULIL8G21"
  }
}
```

#### Confidence Handling

- `confidence >= 0.9`: Auto-apply allowed (if policy allows)
- `confidence 0.7-0.9`: Manual review recommended
- `confidence < 0.7`: Manual review required

#### CLI Commands

```bash
# Generate remediation tasks
python scripts/generate_remediation_tasks.py \
  data/cleaned/CASP20251208_clean.csv \
  validation_report.json \
  --out remediation_tasks.json

# Run LLM remediation (optional stub)
python scripts/run_llm_remediation.py \
  remediation_tasks.json \
  --provider gemini \
  --api-key $GEMINI_API_KEY \
  --out remediation_patch.json \
  --auto-apply-low-risk

# Apply remediation patch
python scripts/apply_remediation_patch.py \
  data/cleaned/CASP20251208_clean.csv \
  remediation_patch.json \
  --out data/cleaned/CASP20251208_clean_llm.csv \
  --report llm_apply_report.json \
  --require-approval  # or --auto-apply-low-risk

# Full pipeline (with LLM step optional)
python scripts/run_full_pipeline.py \
  data/raw/CASP20251208.csv \
  --clean \
  --llm-remediation \
  --provider gemini
```

### E) Test Plan

**Test Cases**:

1. **Task Generation** (`test_remediation_tasks.py`):
   - ✅ Task generation identifies correct cells from validation report
   - ✅ Context is minimal (only needed columns)
   - ✅ Row identifiers are stable (survive merge/dedup)
   - ✅ Tasks are filtered by severity (only ERROR/WARNING)

2. **Policy Enforcement** (`test_remediation_policy.py`):
   - ✅ Forbidden edit (LEI change) is rejected
   - ✅ Forbidden edit (new entity) is rejected
   - ✅ Allowed transformation (encoding fix) passes
   - ✅ Risk level calculation is correct

3. **Patch Application** (`test_remediation_patch.py`):
   - ✅ Patch apply updates correct row/column
   - ✅ Audit log contains all required fields
   - ✅ Invalid patch JSON fails fast (schema validation)
   - ✅ Confidence-based auto-apply works

4. **LLM Client** (`test_remediation_llm_client.py`):
   - ✅ Interface is provider-agnostic
   - ✅ Context is properly formatted
   - ✅ Response is validated against schema
   - ✅ Error handling (API failures, rate limits)

5. **Integration** (`test_remediation_integration.py`):
   - ✅ Full pipeline works without LLM (graceful degradation)
   - ✅ Full pipeline works with LLM
   - ✅ Validation after LLM remediation passes
   - ✅ Abort on validation failure works

## 🔄 Cron Job Integration

### Cel
Automatyzacja procesu aktualizacji danych CSV z ESMA z pełnym pipeline (walidacja → cleaning → LLM remediation → import).

### Design

**Plik**: `scripts/cron_update_data.sh`

**Workflow**:
1. Download najnowszego CSV z ESMA (lub użyj istniejącego w `data/raw/`)
2. Walidacja → `validation_report.json`
3. Deterministic cleaning → `clean.csv` + `clean_report.json`
4. Walidacja cleaned → `validation_clean_report.json`
5. Jeśli są błędy: generuj `remediation_tasks.json`
6. Jeśli są tasks i LLM enabled: uruchom LLM remediation → `remediation_patch.json`
7. Zastosuj patch (z approval policy) → `clean_llm.csv` + `llm_apply_report.json`
8. Finalna walidacja → MUSI przejść lub abort
9. Import do bazy danych (lokalnie lub przez API endpoint)
10. Notyfikacja (email/Slack/webhook) z raportem

### Konfiguracja

**Plik**: `config/remediation_config.yaml` (lub `.env`):

```yaml
llm:
  enabled: true
  provider: "gemini"  # or "openai", "anthropic"
  api_key_env: "GEMINI_API_KEY"
  auto_apply_confidence_threshold: 0.9
  max_tasks_per_run: 50
  
policy:
  require_manual_approval: true
  auto_apply_low_risk: false
  allowed_transformations:
    - ENCODING_FIX
    - COUNTRY_NORMALIZE
    - WEBSITE_FIX
  
cron:
  schedule: "0 2 * * *"  # Daily at 2 AM
  timezone: "Europe/Warsaw"
  notification:
    enabled: true
    webhook_url: "https://hooks.slack.com/..."
    email: "admin@example.com"
```

### Cron Job Setup

**Dla Linux/macOS (crontab)**:
```bash
# Edit crontab
crontab -e

# Add line (runs daily at 2 AM)
0 2 * * * cd /path/to/mica-register && /path/to/venv/bin/python scripts/cron_update_data.sh >> logs/cron.log 2>&1
```

**Dla Railway/Vercel**:
- Użyj Railway Cron Jobs lub GitHub Actions
- GitHub Actions workflow: `.github/workflows/update_data.yml`

**Plik**: `.github/workflows/update_data.yml`:
```yaml
name: Update ESMA Data

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
  workflow_dispatch:  # Manual trigger

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
      - name: Run update pipeline
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: |
          bash scripts/cron_update_data.sh
      - name: Commit and push if changed
        run: |
          git config --global user.name 'GitHub Actions'
          git config --global user.email 'actions@github.com'
          git add data/
          git diff --staged --quiet || (git commit -m "Auto-update: $(date +%Y-%m-%d)" && git push)
```

## 📝 Implementation Phases

### Phase 1: Design & Schemas (Priority: High)
- [ ] Create `docs/LLM_REMEDIATION_DESIGN.md`
- [ ] Define Pydantic models in `backend/app/remediation/schemas.py`
- [ ] Create JSON Schema files for validation
- [ ] Document allowed transformations policy table

### Phase 2: Core Modules (Priority: High)
- [ ] Implement `backend/app/remediation/row_identifier.py`
- [ ] Implement `backend/app/remediation/tasks.py` (task generation)
- [ ] Implement `backend/app/remediation/policy.py` (guardrails)
- [ ] Implement `backend/app/remediation/patch.py` (patch application)

### Phase 3: LLM Integration (Priority: Medium)
- [ ] Create `backend/app/remediation/llm_client.py` (interface)
- [ ] Implement Gemini provider stub
- [ ] Implement context construction
- [ ] Implement response validation

### Phase 4: CLI Scripts (Priority: High)
- [ ] `scripts/generate_remediation_tasks.py`
- [ ] `scripts/apply_remediation_patch.py`
- [ ] `scripts/run_llm_remediation.py` (stub)
- [ ] `scripts/run_full_pipeline.py` (optional)

### Phase 5: Tests (Priority: High)
- [ ] Test fixtures (small CSV files)
- [ ] `tests/test_remediation_tasks.py`
- [ ] `tests/test_remediation_policy.py`
- [ ] `tests/test_remediation_patch.py`
- [ ] `tests/test_remediation_llm_client.py` (mocked)
- [ ] Integration tests

### Phase 6: Cron Job (Priority: Medium)
- [ ] `scripts/cron_update_data.sh`
- [ ] `config/remediation_config.yaml`
- [ ] `.github/workflows/update_data.yml` (GitHub Actions)
- [ ] Notification system (webhook/email)

## 🎯 Success Criteria

- ✅ Pipeline działa bez LLM (graceful degradation)
- ✅ LLM remediation jest opcjonalny i bezpieczny
- ✅ Wszystkie zmiany są audytowane
- ✅ Guardrails blokują forbidden edits
- ✅ Testy pokrywają wszystkie critical paths
- ✅ Cron job automatycznie aktualizuje dane
- ✅ Dokumentacja jest kompletna

## ⏱️ Szacowany czas

- **Phase 1-2**: 8-12 godzin (design + core modules)
- **Phase 3**: 4-6 godzin (LLM integration)
- **Phase 4**: 4-6 godzin (CLI scripts)
- **Phase 5**: 6-8 godzin (tests)
- **Phase 6**: 4-6 godzin (cron job)

**Total**: ~26-38 godzin

## 🔗 Powiązane pliki

- `backend/app/import_csv.py` - istniejąca logika importu
- `backend/app/csv_validate.py` - walidacja CSV
- `backend/app/csv_clean.py` - deterministic cleaning
- `scripts/validate_csv.py` - CLI walidacji
- `scripts/clean_csv.py` - CLI czyszczenia
- `UPDATE_DATA.md` - dokumentacja procesu aktualizacji

---

**Status**: 🟡 In Planning  
**Last Updated**: 2025-01-XX  
**Owner**: TBD
