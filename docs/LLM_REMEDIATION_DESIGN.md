# LLM Remediation Design Document

## Overview

LLM Remediation is an optional component of the ESMA CSV pipeline that uses Deepseek API to fix edge cases that cannot be handled by deterministic cleaning. It operates with strict guardrails, full auditability, and minimal data sharing.

## Pipeline Stages

```
1. Validate raw CSV → validation_report.json
2. Deterministic clean → clean.csv + clean_report.json
3. Validate cleaned CSV → validation_clean_report.json
4. Generate remediation tasks (if errors remain) → remediation_tasks.json
5. LLM remediation (optional) → remediation_patch.json
6. Apply patch → clean_llm.csv + llm_apply_report.json
7. Final validation → MUST pass or abort
8. Import to database
```

## Data Minimization Strategy

- **Never send entire CSV to LLM**
- Only send minimal context per task:
  - Problem column value
  - Related columns (max 500 chars each)
  - Total context max 2000 chars
- Context columns selected based on task type:
  - `ENCODING_FIX`: address, commercial_name, lei_name, competentAuthority, comments
  - `COUNTRY_NORMALIZE`: homeMemberState, serviceCode_cou
  - `WEBSITE_FIX`: website, commercial_name
  - `DATE_FIX`: authorisationNotificationDate, authorisationEndDate, lastupdate
  - `ADDRESS_FIX`: address, website, commercial_name

## Allowed Transformations

| Transformation Type | Risk Level | Auto-Apply | Description |
|-------------------|------------|------------|-------------|
| `ENCODING_FIX` | LOW | Yes (if confidence >= 0.9) | Fix encoding issues (e.g., "Strae" → "Straße") |
| `COUNTRY_NORMALIZE` | LOW | Yes (if confidence >= 0.9) | Normalize country codes (e.g., "EL" → "GR", "Fi" → "FI") |
| `WEBSITE_FIX` | LOW | Yes (if confidence >= 0.9) | Fix website formatting, multiline, add scheme |
| `DATE_FIX` | MEDIUM | No | Fix date formats that deterministic cleaner couldn't handle |
| `ADDRESS_FIX` | MEDIUM | No | Fix address/website parsing issues |

## Forbidden Edits

The following are **strictly forbidden** and will be rejected by guardrails:

- **LEI values**: Cannot be changed (except trivial trimming, which should be handled by deterministic cleaning)
- **New entities**: Cannot invent new entities, services, or countries
- **Freeform rewriting**: Cannot rewrite legal names, authority names, or addresses (except minimal encoding repair)

## Row Identification Strategy

Stable row identification that survives merge/dedup operations:

1. **Primary**: `ae_lei` (if unique)
2. **Fallback**: `ae_lei + ae_competentAuthority + ac_serviceCode_cou` (for duplicate LEI)
3. **Last resort**: `synthetic_id` (hash of key fields: lei_name, commercial_name, competentAuthority, homeMemberState, row_index)

## Deepseek Model Fallback

Models are tried in order until one succeeds:

1. `deepseek-reasoner` (first attempt - thinking mode, better for complex cases)
2. `deepseek-chat` (fallback - non-thinking mode, faster)

**Note:**
- `deepseek-reasoner` uses reasoning/thinking mode which provides better quality for complex data cleaning tasks
- `deepseek-chat` is faster and suitable for simpler transformations
- Both models use OpenAI-compatible API

If all models fail, the process aborts with an error.

## Confidence Handling

- `confidence >= 0.9`: Auto-apply allowed (if policy allows and `auto_apply_low_risk=True`)
- `confidence 0.7-0.9`: Manual review recommended
- `confidence < 0.7`: Manual review required (blocked by policy)

## API Key Configuration

- **Environment variable**: `DEEPSEEK_API_KEY`
- **Get API key from**: https://platform.deepseek.com/api_keys
- **Production**: Set in Railway/Vercel environment variables

## Schemas

### RemediationTask

```json
{
  "task_id": "uuid",
  "task_type": "ENCODING_FIX | COUNTRY_NORMALIZE | WEBSITE_FIX | DATE_FIX | ADDRESS_FIX",
  "row_identifier": {
    "lei": "string | null",
    "competent_authority": "string | null",
    "service_country": "string | null",
    "synthetic_id": "string | null"
  },
  "column": "string",
  "current_value": "string (max 1000 chars)",
  "issue_description": "string",
  "context": {
    "context": {
      "column_name": "value (max 500 chars per column, total max 2000 chars)"
    }
  },
  "severity": "ERROR | WARNING",
  "metadata": {}
}
```

### RemediationPatch

```json
{
  "patch_id": "uuid",
  "generated_at": "ISO datetime",
  "model_provider": "deepseek",
  "model_name": "deepseek-reasoner | deepseek-chat",
  "tasks": [
    {
      "task_id": "uuid",
      "proposed_value": "string (max 1000 chars)",
      "confidence": 0.0-1.0,
      "reasoning": "string (max 500 chars)",
      "transformation_type": "ENCODING_FIX | ...",
      "risk_level": "LOW | MEDIUM | HIGH"
    }
  ],
  "metadata": {
    "models_tried": ["deepseek-reasoner", "deepseek-chat"],
    "model_used": "deepseek-reasoner",
    "tasks_processed": 10,
    "tasks_total": 10
  }
}
```

## Failure Modes

1. **All models fail**: Process aborts, no patch generated
2. **Patch validation fails**: Rejected changes logged, process continues with valid changes
3. **Final validation fails**: Process aborts, original cleaned CSV is preserved
4. **API rate limits**: Retry with next model in fallback order

## CLI Commands

### Generate Tasks

```bash
python scripts/generate_remediation_tasks.py \
  data/cleaned/CASP20251215_clean.csv \
  validation_report.json \
  --out remediation_tasks.json \
  --max-tasks 50
```

### Run LLM Remediation

```bash
python scripts/run_llm_remediation.py \
  remediation_tasks.json \
  --out remediation_patch.json \
  --api-key $DEEPSEEK_API_KEY
```

### Apply Patch

```bash
python scripts/apply_remediation_patch.py \
  data/cleaned/CASP20251215_clean.csv \
  remediation_patch.json \
  remediation_tasks.json \
  --out data/cleaned/CASP20251215_clean_llm.csv \
  --report llm_apply_report.json \
  --require-approval  # or --auto-apply-low-risk
```

## Safety Features

1. **Guardrails**: Policy enforcement blocks forbidden edits
2. **Manual approval**: Default behavior requires approval for all changes
3. **Audit logging**: All changes logged with full metadata
4. **Schema validation**: Patch JSON validated before application
5. **Final validation**: Must pass validation after patch application
6. **Graceful degradation**: Pipeline works without LLM if disabled

## Testing

- Unit tests for task generation, policy enforcement, patch application
- Mocked Deepseek API responses for LLM client tests
- Integration tests for full pipeline
- Test guardrails block forbidden edits

## Configuration

Environment variables:
- `DEEPSEEK_API_KEY`: Deepseek API key (required)

Config file (optional): `config/remediation_config.yaml`
- `llm.enabled: true/false`
- `llm.auto_apply_confidence_threshold: 0.9`
- `llm.max_tasks_per_run: 50`
- `policy.require_manual_approval: true`
- `policy.auto_apply_low_risk: false`

