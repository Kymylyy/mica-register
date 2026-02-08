# Updating MiCA Register Data

This document describes how to update the MiCA register data from ESMA.

## Quick Start (Recommended)

Update all registers with one command:

```bash
python scripts/update_all_registers.py --all
```

This will:
1. ✅ Check ESMA for updates
2. ✅ Download new CSVs (if needed)
3. ✅ Validate and clean data
4. ✅ Import to database (non-destructive by default)
5. ✅ Update frontend date

Done! Review the summary and commit changes.

## Command Options

### Update all registers
```bash
python scripts/update_all_registers.py --all
```

### Update specific registers
```bash
python scripts/update_all_registers.py --registers casp,art,emt
```

### Force redownload even if up to date
```bash
python scripts/update_all_registers.py --all --force
```

### Skip validation/cleaning (use existing cleaned files)
```bash
python scripts/update_all_registers.py --all --skip-cleaning
```

### Prefer `_clean.csv` over `_clean_llm.csv`
```bash
python scripts/update_all_registers.py --all --no-use-clean-llm
```

### Dry run (preview only, no changes)
```bash
python scripts/update_all_registers.py --all --dry-run
```

### Drop database before import (DESTRUCTIVE!)
```bash
# ⚠️  WARNING: This drops all existing data
python scripts/update_all_registers.py --all --drop-db
```

## Import Only (Skip Download/Validation)

If you already have cleaned CSV files and just want to import them:

```bash
# Import all registers from latest cleaned files
python backend/import_all_registers.py

# Drop database first (use with caution!)
python backend/import_all_registers.py --drop-db
```

## File Structure

The update process uses a standardized directory structure:

```
data/
├── raw/                  # Downloaded CSVs
│   ├── casp/
│   │   └── CASP20260130.csv
│   ├── art/
│   ├── emt/
│   ├── ncasp/
│   └── other/
└── cleaned/              # Validated and cleaned CSVs
    ├── casp/
    │   └── CASP20260130_clean.csv
    ├── art/
    ├── emt/
    ├── ncasp/
    └── other/
```

Files are automatically detected by:
- Register type (CASP, ART, EMT, NCASP, OTHER)
- Date in filename (YYYYMMDD format)
- Cleaned status (_clean or _clean_llm suffix)

## Manual Workflow (Individual Steps)

If you need to run steps separately:

### 1. Check for updates
```bash
python scripts/check_esma_update.py
```

### 2. Download new CSVs
```bash
python scripts/update_esma_data.py --registers casp,art,emt,ncasp,other
```

### 3. Validate CSV
```bash
python scripts/validate_csv.py data/raw/casp/CASP20260130.csv
```

### 4. Clean CSV
```bash
python scripts/clean_csv.py --input data/raw/casp/CASP20260130.csv
```

### 5. Import to database
```bash
python backend/import_all_registers.py
```

## Important Notes

### Non-Destructive by Default

The import process is **non-destructive by default**:
- Existing data is replaced **per-register** only
- Other registers remain untouched
- Database tables are NOT dropped unless `--drop-db` is explicitly used

This protects against accidental data loss during development and production updates.

### _clean_llm Files

If you have both `_clean.csv` and `_clean_llm.csv` files for the same date:
- The system prefers `_clean_llm` by default (LLM-enhanced cleaning)
- Use `--no-use-clean-llm` to prefer `_clean` files instead
- For different dates, the newest date always wins regardless of suffix

### ESMA Date Unavailable

If ESMA update date cannot be retrieved, `update_all_registers.py` skips register updates and exits with code `2`.
This prevents non-deterministic file naming and unintended imports in automated runs (for example cron jobs).

### Docker Support

All scripts automatically detect if running in Docker and adjust paths accordingly:
- Local: `/Users/.../mica-register/data/`
- Docker: `/app/data/`

## After Updating

1. **Review changes**
   - Check the summary output
   - Verify entity counts match expectations
   - Review the detailed report in `reports/updates/`

2. **Test locally**
   ```bash
   # Start backend
   cd backend && uvicorn app.main:app --reload

   # Start frontend (in another terminal)
   cd frontend && npm run dev
   ```

3. **Commit changes**
   ```bash
   git add data/ frontend/src/App.jsx
   git commit -m "Update ESMA data to [date]"
   git push
   ```

4. **Deploy**
   - Follow your deployment process
   - For Docker: rebuild and restart containers

## Troubleshooting

### "No CSV found" errors
- Check that files are in the correct subdirectories (e.g., `data/raw/casp/`)
- Verify filenames match the pattern: `{PREFIX}{YYYYMMDD}.csv` or `{PREFIX}{YYYYMMDD}_clean.csv`
- Test files (with `-test` in name) are ignored

### Import fails with validation errors
- Run validation separately to see detailed issues:
  ```bash
  python scripts/validate_csv.py data/raw/casp/CASP20260130.csv
  ```
- Clean the CSV to fix issues:
  ```bash
  python scripts/clean_csv.py --input data/raw/casp/CASP20260130.csv
  ```

### Database already exists warning
- This is normal! By default, existing data is replaced per-register
- Only use `--drop-db` if you want to completely reset the database

## Configuration

All register configurations (URLs, column mappings, etc.) are centralized in:
- `backend/app/config/registers.py` - Single source of truth for all settings

## Production Updates

For production deployments:
1. Test the update in a staging environment first
2. Backup the production database before updating
3. Use the master update script for consistency
4. Monitor logs for any errors
5. Keep the `--drop-db` flag ONLY for full resets (rare)

The production import endpoint (`/api/admin/import`) is separate and currently CASP-only.
For multi-register production updates, use the CLI scripts described above.
