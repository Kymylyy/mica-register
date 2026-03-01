# MiCA Register

Public web app for browsing ESMA MiCA registers in one searchable interface.

[![CI](https://github.com/Kymylyy/mica-register/actions/workflows/ci.yml/badge.svg)](https://github.com/Kymylyy/mica-register/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Live app: [www.micaregister.com](https://www.micaregister.com)  
Backend API docs (recommended custom domain): `https://api.micaregister.com/docs`

## What It Does

- Aggregates all 5 ESMA MiCA registers in one UI:
  - CASP (Crypto-Asset Service Providers)
  - OTHER (White papers for other crypto-assets)
  - ART (Asset-Referenced Token Issuers)
  - EMT (E-Money Token Issuers)
  - NCASP (Non-compliant entities)
- Fast filtering by name, country, LEI, services, dates, and register-specific fields
- Shareable entity deep links (for example `/casp/{entity_id}`) that open details directly
- Home Member State filtering falls back to LEI country when ESMA country is missing
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
git clone https://github.com/Kymylyy/mica-register.git
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

- `VITE_API_URL` (e.g. `https://api.micaregister.com` in production)

See `.env.example` and `frontend/.env.example` for local templates.

## Deployment

### Railway (backend)

- Connect repository to Railway
- Ensure PostgreSQL service is attached
- Set required env vars (`DATABASE_URL`, `CORS_ORIGINS`, `ADMIN_API_TOKEN`)
- Add custom domain (recommended): `api.micaregister.com`
- Optional cron: run `python scripts/run_railway_cron_update.py`

### Vercel (frontend)

- Import `frontend` project
- Set `VITE_API_URL` to your API domain (recommended: `https://api.micaregister.com`)
- Build command: `npm run build`
- Output directory: `dist`
- Build output includes static prerendered pages for `/`, `/casp`, `/other`, `/art`, `/emt`, and `/ncasp`, plus entity detail pages (for example `/casp/{id}`) based on the latest API snapshot available during build.
- `sitemap.xml` and `robots.txt` are generated during prerender from the same route set (including entity detail URLs when available at build time).
- `micaregister.com` is redirected permanently (301) to `www.micaregister.com`.
- Detail prerender validation: by default it fails on CI/Vercel (`PRERENDER_DETAIL_FAILURE_MODE=error`) and warns locally (`warn`) when detail pages cannot be generated or are below `PRERENDER_MIN_DETAIL_PAGES` (default `1`).

## Public Feeds API

Per-register feeds (public):

- `GET /api/feeds` (index with feed links + docs + OpenAPI URL on current host)
- `GET /api/feeds/{register}.json`
- `GET /api/feeds/{register}.csv`

Where `{register}` is one of: `casp`, `other`, `art`, `emt`, `ncasp`.

Operational behavior:

- Feed responses are cached in API process memory for 300 seconds.
- Feed responses include `ETag` and `Cache-Control` headers for conditional requests and client/proxy caching.
- Feed endpoints are rate limited to 30 requests per 60 seconds per client IP.

## Quality Checks

Frontend:

- `cd frontend && npm run lint`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run test -- --run`
- `cd frontend && npm run build`

Backend:

- `python3 -m pytest`

CI runs the same checks on every pull request and push.

## Data Source

Primary source: ESMA MiCA register publications.

Before redistributing data snapshots from `data/`, confirm legal/licensing requirements for your use case.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

See [SECURITY.md](SECURITY.md) for vulnerability reporting and secret handling expectations.

## License

MIT. See [LICENSE](LICENSE).
