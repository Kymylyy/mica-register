# MiCA Register

Public web app for browsing ESMA MiCA registers in one searchable interface.

## What It Does

- Aggregates all 5 ESMA MiCA registers in one UI:
  - CASP (Crypto-Asset Service Providers)
  - OTHER (White papers for other crypto-assets)
  - ART (Asset-Referenced Token Issuers)
  - EMT (E-Money Token Issuers)
  - NCASP (Non-compliant entities)
- Fast filtering by name, country, LEI, services, dates, and register-specific fields
- Backend API for search, filtering, and admin imports
- Data update scripts for download, validation, cleaning, and import

## Tech Stack

- Backend: FastAPI, SQLAlchemy, Alembic-style migrations
- Frontend: React + Vite
- Database: PostgreSQL (production) or SQLite (local)
- Deploy: Railway (backend) + Vercel (frontend)

## Quick Start

### 1. Clone

```bash
git clone <your-repo-url>
cd mica-register
```

### 2. Backend setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

Optional database config:

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/mica_register"
```

If `DATABASE_URL` is not set, local SQLite is used.

### 3. Import data

```bash
python3 backend/app/import_csv.py --all
```

### 4. Run backend

```bash
cd backend
uvicorn app.main:app --reload
```

Backend URL: `http://localhost:8000`

### 5. Run frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend URL: `http://localhost:5173`

## Environment Variables

Backend:

- `DATABASE_URL` (required in production)
- `CORS_ORIGINS` (comma-separated allowed origins)
- `ADMIN_API_TOKEN` (or `ADMIN_TOKEN`) for `/api/admin/*`
- `DEEPSEEK_API_KEY` (optional, only for LLM remediation flows)

Frontend:

- `VITE_API_URL` (e.g. Railway backend URL in production)

See `.env.example` and `frontend/.env.example` for local templates.

## Deployment

### Railway (backend)

- Connect repository to Railway
- Ensure PostgreSQL service is attached
- Set required env vars (`DATABASE_URL`, `CORS_ORIGINS`, `ADMIN_API_TOKEN`)
- Optional cron: run `python scripts/run_railway_cron_update.py`

### Vercel (frontend)

- Import `frontend` project
- Set `VITE_API_URL` to your Railway backend URL
- Build command: `npm run build`
- Output directory: `dist`

## Data Source

Primary source: ESMA MiCA register publications.

Before redistributing data snapshots from `data/`, confirm legal/licensing requirements for your use case.

## Contributing

1. Create a branch from `main`
2. Run checks locally (`frontend` lint/test + backend tests)
3. Open a PR

## License

MIT. See [LICENSE](LICENSE).
