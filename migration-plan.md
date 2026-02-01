# EKSPRESOWY Deployment Plan - 2026-02-01 (15:50-17:00)

**UWAGA:** To jest skrócona wersja oryginalnego planu, dostosowana do rozpoczęcia deployment o 15:20 zamiast 08:30.

**Data:** 2026-02-01 (dzisiaj, start: 15:50)
**Typ:** Major architectural refactor (system multi-register)
**Platformy:** Railway (backend) + Vercel (frontend)
**Czas:** 15:50-17:00 (1h 10min - NAPIĘTY HARMONOGRAM)

---

## 📊 Główne Wnioski

**Dobra wiadomość:** 50% przygotowań już zrobione!
- ✅ Migration 002 poprawiona (dti_ffg → VARCHAR)
- ✅ backend/start.sh istnieje (z error handling)
- ✅ API migration Gemini → Deepseek COMPLETED
- ✅ CSV files już w repo (15 plików tracked)
- ✅ Dockerfile zaktualizowany (używa start.sh)
- ✅ models.py, schemas.py, import_csv.py - wszystkie poprawki zrobione
- ✅ Frontend - 5 register tabs gotowe
- ✅ Testy - wszystkie 33 fixed

**Problem:** Oryginalny plan nieaktualny w kluczowych aspektach:
- ⚠️ Timeline zakłada start o 08:30, ale jest **15:50** (zostało tylko 1h 10min!)
- ⚠️ Wszędzie GEMINI_API_KEY zamiast DEEPSEEK_API_KEY
- ⚠️ Zakłada dodawanie CSV files, które są **już w repo**
- ⚠️ Zakłada tworzenie start.sh, który **już istnieje**
- ⚠️ Plan zakłada pełne testy (brak czasu)

**Stan deployment:**
- ❌ NIE rozpoczęty - llms-control NIE zmergowany do main
- ❌ Kod nie zacommitowany (11 plików + start.sh untracked)
- ✅ Większość zmian kodu gotowa - tylko commit + merge + deploy

**Realność ekspresowego deployment:**
- ⏱️ Możliwe w 1h 40min (napięty ale wykonalny harmonogram)
- ⚠️ Pominięte: backup DB, pełne testy E2E (zrobić jutro)
- ✅ Kluczowe: weryfikacja env vars PRZED merge

---

## ⚠️ UWAGA - Skrócony Plan

**Status przed startem (15:50):**
- ✅ 50% przygotowań już zrobione
- ✅ CSV files w repo (15 plików)
- ✅ Migration 002 poprawiona (dti_ffg VARCHAR)
- ✅ backend/start.sh istnieje
- ✅ Dockerfile zaktualizowany
- ✅ API migration: Gemini → Deepseek COMPLETED
- ❌ Kod nie zacommitowany (11 plików + start.sh)
- ❌ Nie zmergowano do main

**Pominięte (brak czasu):**
- ⏭️ Backup bazy danych (ryzyko - zrób jutro!)
- ⏭️ Pełne testy lokalne (tylko quick smoke test)
- ⏭️ Full E2E testing (zrób jutro post-deployment)

---

## Podsumowanie Zmian (Status: READY)

### ✅ Co Wdrażamy
- **Główna zmiana:** System jednego rejestru (CASP) → Architektura multi-register (5 rejestrów)
- **Zakres:** 102 pliki, +17,965 linii kodu
- **Baza danych:** Destrukcyjna migracja schematu (migration 002 - JUŻ POPRAWIONA)
- **Frontend:** Dodana zależność `react-router-dom` v6.30.3
- **Environment:** `DEEPSEEK_API_KEY` opcjonalny (tylko dla remediation features)

### ✅ KRYTYCZNE ZMIANY - Status

**✅ JUŻ ZROBIONE (do zacommitowania):**
- ✅ Migration 002: dti_ffg zmienione z BOOLEAN → VARCHAR (linie 225, 267)
- ✅ backend/start.sh: Auto-migrations script (ISTNIEJE, untracked)
- ✅ Dockerfile: Zaktualizowany do używania start.sh (linia 31)
- ✅ models.py: dti_ffg jako String (linie 273, 319)
- ✅ schemas.py: dti_ffg jako Optional[str] (linia 86)
- ✅ import_csv.py: Parsing dti_ffg jako string (linie 484, 530)
- ✅ routers/entities.py: Rozszerzony search (address, website, register-specific)
- ✅ Frontend App.jsx: 5 register tabs
- ✅ CSV files: JUŻ W REPO (15 plików)
- ✅ API Migration: Gemini → Deepseek COMPLETED

**❌ DO ZROBIENIA (15:50-17:00):**
- ❌ Commit + push changes
- ❌ Create PR
- ❌ Merge to main
- ❌ Monitor deployment
- ❌ Import danych
- ❌ Smoke tests

---

## TIMELINE EKSPRESOWY (15:50-17:00)

### 15:50-16:00: GIT WORKFLOW (10 min)

**Commit uncommitted changes:**

```bash
cd /Users/Kymyly/Desktop/GIT/mica-register

# Verify current branch
git branch  # Should show: * llms-control

# Add untracked start.sh
git add backend/start.sh

# Stage all modified files
git add Dockerfile
git add backend/app/models.py
git add backend/app/schemas.py
git add backend/app/import_csv.py
git add backend/app/routers/entities.py
git add backend/migrations/002_multi_register_migration.py
git add frontend/src/App.jsx
git add frontend/src/components/DataTable.jsx
git add frontend/src/config/registerColumns.js
git add update_production.sh
git rm IMPLEMENTATION_SUMMARY.md  # Already deleted

# Verify staged files
git status

# Commit
git commit -m "$(cat <<'EOF'
Deploy: Multi-register architecture ready

Critical changes:
- Migration 002: dti_ffg BOOLEAN → VARCHAR (lines 225, 267)
- Startup script: Auto-migrations for Railway (backend/start.sh)
- Dockerfile: Uses startup script for auto-migrations
- API migration: Gemini → Deepseek COMPLETED
  - llm_client.py: DEEPSEEK_API_KEY environment variable
  - Model fallback: deepseek-reasoner → deepseek-chat
- Models/schemas: dti_ffg as String/Optional[str]
- Import CSV: dti_ffg parsed as string identifier
- Frontend: Multi-register tabs (CASP, OTHER, ART, EMT, NCASP)
- Routers: Enhanced search (address, website, register-specific fields)
- Tests: All 33 tests fixed

Ready for production deployment.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"

# Push to origin
git push origin llms-control
```

**✅ Checkpoint:** Verify push succeeded (git log, GitHub)

---

### 16:00-16:05: VERIFY .dockerignore (5 min)

⚠️ **KRYTYCZNE:** Upewnij się że CSV files nie są ignorowane w Docker build

```bash
# Check if .dockerignore exists
cat .dockerignore 2>/dev/null || echo "No .dockerignore (OK - all files copied)"

# If .dockerignore exists, verify it doesn't exclude data/
grep -E "^data/|^\*\.csv" .dockerignore && echo "⚠️ WARNING: .dockerignore blocks CSV files!" || echo "✅ OK"

# If blocked: Remove data/ from .dockerignore or add exception:
# !data/cleaned/**
```

**Railway needs CSV files w kontenerze** - bez tego import failuje z "CSV not found"

### 16:05-16:10: QUICK LOCAL TEST (5 min - SKRÓCONY)

```bash
cd /Users/Kymyly/Desktop/GIT/mica-register

# Fresh SQLite DB
rm -f backend/database.db

# Test startup script (migrations + uvicorn)
cd backend
bash start.sh &
BACKEND_PID=$!

# Wait for startup
sleep 5

# Quick smoke tests
curl http://localhost:8000/
# Expected: {"message": "MiCA Register API"} or similar

curl http://localhost:8000/api/entities?register_type=casp | jq '. | length'
# Expected: 0 (empty - no data imported yet)

curl http://localhost:8000/api/services | jq '. | length'
# Expected: 10 (services a-j)

# Check logs for migrations
# Should see: "🔧 Running database migrations..." "✅ All migrations completed successfully"

# Kill backend
kill $BACKEND_PID
cd ..
```

**✅ Checkpoint:** No errors, migrations ran successfully

**⏭️ SKIP (brak czasu):**
- Frontend test
- Full import test
- E2E tests

---

### 16:10-16:18: CREATE PR + VERIFY ENV VARS (8 min)

**⚠️ KRYTYCZNE: Verify environment variables PRZED merge!**

**Vercel Dashboard:**
1. Vercel → Project → Settings → Environment Variables
2. **WYMAGANE:** `VITE_API_URL` = `https://your-app.railway.app` (BEZ trailing slash)
3. Jeśli nie ustawione: **USTAW TERAZ** (przed merge!)

**Railway Dashboard:**
1. Railway → Project → Backend Service → Variables
2. **WYMAGANE:** `CORS_ORIGINS` = `https://your-app.vercel.app` (bez spacji)
3. **OPCJONALNE:** `DEEPSEEK_API_KEY` (nie GEMINI_API_KEY!) - backend startuje bez tego
   - Pobierz z: https://platform.deepseek.com/api_keys

**Create PR (via GitHub CLI - fastest):**

```bash
gh pr create \
  --title "Deploy: Multi-register architecture (5 ESMA MiCA registers)" \
  --body "$(cat <<'EOF'
## EKSPRESOWY DEPLOYMENT (15:20-17:00)

### Summary
Refactor from single-register (CASP) to multi-register architecture for all 5 ESMA MiCA registers.

### Critical Changes
- **Database:** Multi-register schema (base Entity + 5 extension tables)
- **Migration 002:** dti_ffg BOOLEAN → VARCHAR (FIXED)
- **API Migration:** Gemini → Deepseek (COMPLETED)
- **Backend:** register_type routing, enhanced search (address, website, register-specific)
- **Frontend:** Tab navigation (5 registers), register-specific columns
- **Dependencies:** react-router-dom v6.30.3

### Auto-Deployment Features
- **Railway:** Auto-migrations via backend/start.sh (runs migration 001 + 002 on startup)
- **Vercel:** SPA routing configured

### Environment Variables Status
✅ VERIFIED BEFORE MERGE:
- Railway: `DATABASE_URL` (auto-set by PostgreSQL service)
- Railway: `CORS_ORIGINS` (set to Vercel URL)
- Railway: `DEEPSEEK_API_KEY` (OPTIONAL - not GEMINI_API_KEY!)
- Vercel: `VITE_API_URL` (set to Railway backend URL)

### Testing Status
✅ Local migrations tested (SQLite)
✅ Startup script tested
⏭️ Full E2E tests (post-deployment tomorrow)

### Breaking Changes
- LEI uniqueness removed (now scoped to register_type)
- API requires register_type parameter (defaults to CASP for compatibility)

### Success Criteria
- All 5 registers accessible via API
- Frontend shows 5 tabs
- Data import successful (~984 entities total; ART może być 0 jeśli CSV puste)
- No console/API errors

Deployment ready for immediate merge.
EOF
)" \
  --base main \
  --head llms-control
```

**Lub via GitHub UI:**
1. GitHub → "Pull Requests" → "New Pull Request"
2. Base: `main`, Compare: `llms-control`
3. Copy title + body z powyższego

**✅ Checkpoint:** PR created, link saved

---

### 16:18-16:20: MERGE TO MAIN (2 min)

**⏰ TIMING: Merguj tylko jeśli env vars zweryfikowane!**

**Via GitHub CLI (fastest):**
```bash
gh pr merge --merge --auto
```

**Lub via GitHub UI:**
- Click "Merge Pull Request"
- Wybierz "Create a merge commit" (nie squash)
- Confirm merge

**To triggeruje:**
- ✅ Railway auto-build (backend) - trwa 5-10 min
- ✅ Vercel auto-build (frontend) - trwa 3-5 min

**✅ Checkpoint:**
- [ ] main branch updated (git log)
- [ ] Railway build started (check dashboard)
- [ ] Vercel build started (check dashboard)

---

### 16:20-16:35: MONITOR BUILDS (15 min)

**Railway Backend Build:**

1. Railway → Project → Backend Service → "Deployments"
2. Obserwuj build logs (5-10 min)

**Oczekiwany output:**
```
Building...
[+] Building 45.3s (12/12) FINISHED
Installing Python dependencies...
✓ Successfully built
Deploying...

🔧 Running database migrations...
Running migration 001: Performance indexes...
✅ Migration 001 completed
Running migration 002: Multi-register schema...
✅ Added register_type column
✅ Created extension tables
✅ Migration 002 completed
✅ All migrations completed successfully

🚀 Starting FastAPI application...
INFO: Started server process
INFO: Application startup complete
INFO: Uvicorn running on http://0.0.0.0:8000
```

⚠️ **WAŻNE - Migracje Idempotentne:**
- Migracje uruchamiają się **przy KAŻDYM restarcie** kontenera Railway
- Migrations 001 i 002 **MUSZĄ być idempotentne** (sprawdzają `if not exists` przed tworzeniem)
- Obecne migracje SĄ idempotentne - ale jeśli dodasz nowe, upewnij się że też są!
- Jeśli migracja nie jest idempotentna → użyj `railway run python migrations/XXX.py` TYLKO RAZ ręcznie

**Jeśli migrations failują:**
```bash
# Fallback: Manual migrations via Railway CLI
railway login
railway link
railway run python migrations/001_add_performance_indexes.py
railway run python migrations/002_multi_register_migration.py
railway restart
```

**Vercel Frontend Build:**

1. Vercel → Project → "Deployments"
2. Obserwuj build (3-5 min)

**Oczekiwany output:**
```
Running build command: npm run build
✓ built in 25s
✓ 125 modules transformed
dist/index.html           0.52 kB
dist/assets/index-abc.js  245.67 kB

Deployment ready
Production: https://your-app.vercel.app
```

**Verify env vars w build logs:**
- Search for "VITE_API_URL" → powinno pokazać Railway URL

**✅ Checkpoint:**
- [ ] Railway deployment successful (status: "Active")
- [ ] Vercel deployment successful (status: "Production")
- [ ] Backend logs: "Uvicorn running"
- [ ] Migrations logs: "✅ All migrations completed"

---

### 16:35-17:00: IMPORT DANYCH + VERIFY (25 min)

⚠️ **SECURITY WARNING - Import Endpoint:**
Jeśli masz endpoint `/api/admin/import-all` w kodzie:
- Jest on **PUBLICZNY** (brak autentykacji!)
- **TODO POST-DEPLOYMENT:** Zabezpieczyć przed produkcją:
  - Opcja 1: Dodać Basic Auth / secret token w header
  - Opcja 2: Usunąć endpoint z produkcji (tylko CLI import)
  - Opcja 3: Whitelisting IP (Railway, admin IP)
- **NA DZIŚ:** Import robimy via CLI (bezpieczniejsze)

**Weryfikacja że CSV są dostępne:**

```bash
railway login
railway link

# Check filesystem
railway shell
ls -lh data/cleaned/casp/
ls -lh data/cleaned/other/
ls -lh data/cleaned/art/
ls -lh data/cleaned/emt/
ls -lh data/cleaned/ncasp/
# Should show CSV files
exit
```

**Import wszystkich rejestrów (via Railway CLI - ZALECANE):**

```bash
# Via Railway shell (no timeout)
railway shell
python backend/import_all_registers.py
# ↑ Ten skrypt importuje z data/cleaned/**/*.csv do PostgreSQL
# Wait for completion (may take 10-20 min)
exit
```

**Oczekiwany output:**
```
INFO: Importing CASP... 149 entities
INFO: Importing OTHER... 705 entities
INFO: Importing ART... 1 entities
INFO: Importing EMT... 32 entities
INFO: Importing NCASP... 102 entities
Total: 984 entities (ART może być 0 jeśli CSV puste)
```

**Weryfikacja importu (API calls):**

```bash
# Set backend URL
BACKEND_URL="https://your-app.railway.app"

# Test każdego rejestru
curl "$BACKEND_URL/api/entities?register_type=casp" | jq '. | length'    # Expected: ~149
curl "$BACKEND_URL/api/entities?register_type=other" | jq '. | length'   # Expected: ~705
curl "$BACKEND_URL/api/entities?register_type=art" | jq '. | length'     # Expected: ~1
curl "$BACKEND_URL/api/entities?register_type=emt" | jq '. | length'     # Expected: ~32
curl "$BACKEND_URL/api/entities?register_type=ncasp" | jq '. | length'   # Expected: ~102

# Total check
echo "Total entities:"
curl -s "$BACKEND_URL/api/entities?register_type=casp" | jq '. | length' > /tmp/counts.txt
curl -s "$BACKEND_URL/api/entities?register_type=other" | jq '. | length' >> /tmp/counts.txt
curl -s "$BACKEND_URL/api/entities?register_type=art" | jq '. | length' >> /tmp/counts.txt
curl -s "$BACKEND_URL/api/entities?register_type=emt" | jq '. | length' >> /tmp/counts.txt
curl -s "$BACKEND_URL/api/entities?register_type=ncasp" | jq '. | length' >> /tmp/counts.txt
awk '{sum+=$1} END {print sum}' /tmp/counts.txt
# Expected: ~984 (ART może być 0)
```

**✅ Checkpoint:**
- [ ] CASP: ~149 entities
- [ ] OTHER: ~705 entities
- [ ] ART: ~0 entity (jeśli CSV puste)
- [ ] EMT: ~32 entities
- [ ] NCASP: ~102 entities
- [ ] **Total: ~984 entities** (ART może być 0)

---

### 16:35-17:00: SMOKE TESTS (25 min)

**Frontend Smoke Tests:**

**Odwiedź:** `https://your-app.vercel.app`

**Podstawowe testy:**
- [ ] **Strona się ładuje** (brak białego ekranu)
- [ ] **5 zakładek widocznych:** CASP, OTHER, ART, EMT, NCASP
- [ ] **CASP tab (default):**
  - [ ] ~149 entities wyświetlonych
  - [ ] Filtry widoczne (Home Member State, Services, Date)
  - [ ] Sortowanie działa (kliknij nagłówek kolumny)
  - [ ] Modal encji otwiera się (kliknij wiersz)
  - [ ] Copy buttons działają (LEI, address)
- [ ] **OTHER tab:**
  - [ ] ~705 entities wyświetlonych
  - [ ] DTI FFG wyświetla się jako STRING (np. "1SL20Z9P1", NIE "Yes/No")
  - [ ] White Paper URL wyświetla się
  - [ ] Filtry działają
- [ ] **Przełączanie zakładek:**
  - [ ] ART → ~0 entity (jeśli CSV puste)
  - [ ] EMT → ~32 entities
  - [ ] NCASP → ~102 entities

**Network tab (F12):**
- [ ] **API calls do Railway backend:** `https://your-app.railway.app/api/entities?register_type=...`
- [ ] **Brak błędów CORS**
- [ ] **Brak 404/500 errors**

**Console tab (F12):**
- [ ] **Brak błędów JavaScript**
- [ ] **Brak warning "VITE_API_URL not set"**

**Backend API Tests:**

```bash
BACKEND_URL="https://your-app.railway.app"

# Test root endpoint
curl "$BACKEND_URL/"
# Expected: 200 OK

# Test services
curl "$BACKEND_URL/api/services" | jq '. | length'
# Expected: 10

# Test filter counts
curl "$BACKEND_URL/api/filter-counts?register_type=casp" | jq '.home_member_states | length'
# Expected: >= 0

# Test nowego rozszerzonego search (NOWA FUNKCJONALNOŚĆ)
curl "$BACKEND_URL/api/entities?register_type=casp&search=crypto" | jq '. | length'
# Expected: >= 0 (no errors)

# Test search w register-specific fields
curl "$BACKEND_URL/api/entities?register_type=other&search=white" | jq '. | length'
# Expected: >= 0

# Test pagination
curl "$BACKEND_URL/api/entities?register_type=other&page=1&limit=10" | jq '. | length'
# Expected: 10

# Test CORS
curl -I -X OPTIONS "$BACKEND_URL/api/entities" \
  -H "Origin: https://your-app.vercel.app" \
  -H "Access-Control-Request-Method: GET"
# Expected: Access-Control-Allow-Origin header present
```

**✅ Checkpoint:** Wszystkie smoke tests passed

---

## Environment Variables (VERIFY BEFORE MERGE!)

**Railway:**
- `DATABASE_URL` - ✅ Auto-set by Railway PostgreSQL service
- `CORS_ORIGINS` - ⚠️ **KRYTYCZNE:** Ustaw WSZYSTKIE domeny produkcyjne (nie tylko Vercel!)
  ```
  https://micaregister.com,https://www.micaregister.com,https://micaregister.eu,https://www.micaregister.eu,https://mica-register.vercel.app
  ```
  **Dlaczego:** Użytkownicy wchodzą przez custom domeny - bez tego CORS errors!

- `DEEPSEEK_API_KEY` - OPTIONAL (nie GEMINI_API_KEY! Deepseek migration completed)

**Vercel:**
- `VITE_API_URL` - ⚠️ **KRYTYCZNE:** Ustaw backend URL
  - **Jeśli masz custom domain** na Railway (np. `api.micaregister.com`): Użyj tego!
  - **Jeśli nie:** Użyj Railway auto-domain: `https://mica-register-production.up.railway.app`

- ⚠️ **WAŻNE - Vercel Environment:**
  - Ustaw w **Production** environment (nie Preview!)
  - Vercel: Settings → Environment Variables → Environment: **Production** ✓
  - Preview builds używają innych env vars - upewnij się że ustawiasz Production

⚠️ **Timing:** Set BEFORE merge, or redeploy after setting!
⚠️ **Vite caveat:** Env vars są wbudowane w build time (nie runtime) - każda zmiana wymaga redeploy

---

## ROLLBACK PLAN (jeśli potrzeba)

**Kiedy rollback:**
- Migracja bazy danych failuje (corrupted schema)
- Backend nie startuje (crash loop)
- Krytyczne bugi (data loss, security issue)
- Frontend nie może połączyć się z backend (CORS errors)

**Code Rollback:**

```bash
# Znajdź merge commit
git log --oneline -5

# Revert merge (tworzy nowy commit)
git revert -m 1 <merge-commit-hash>
git push origin main

# Railway i Vercel auto-deploy revert
```

**⚠️ WARNING:** Database rollback może stracić zmigrowane dane. Jeśli deployment failuje przed importem, rollback jest bezpieczny.

---

## KRYTERIA SUKCESU

**Deployment jest sukcesem gdy:**
1. ✅ Backend responds do wszystkich 5 register APIs
2. ✅ Frontend pokazuje wszystkie 5 register tabs
3. ✅ Data loads correctly (~984 entities total; ART może być 0)
4. ✅ Filters, sorting, modals działają
5. ✅ No console errors, no API errors
6. ✅ Rozszerzony search działa (address, website, register-specific)
7. ✅ DTI FFG wyświetla się jako string (nie Yes/No)
8. ✅ No errors w Railway/Vercel logs

---

## KRYTYCZNE ZMIANY vs Oryginalny Plan

**✅ COMPLETED:**
- GEMINI_API_KEY → DEEPSEEK_API_KEY migration
- CSV files już w repo (nie trzeba dodawać)
- backend/start.sh już istnieje
- Migration 002 już poprawiona
- dti_ffg już jako VARCHAR/String

**⏭️ POMINIĘTE (brak czasu):**
- Backup bazy danych Railway (RYZYKO - zrób jutro!)
- Pełne testy lokalne (tylko quick smoke test)
- Full E2E testing (zrób jutro post-deployment)
- Tag git (pre-deployment backup)

**⚠️ TIMELINE:**
- Oryginalny: 08:30-17:00 (8.5h)
- Rzeczywisty: 15:20-17:00 (1h 40min)
- Skrócony o: 6h 50min

---

## POST-DEPLOYMENT (jutro 2026-02-02)

**TODO po deployment:**
1. ⬜ **KRYTYCZNE - Zabezpiecz import endpoint** (jeśli istnieje `/api/admin/import-all`):
   - Dodaj Basic Auth lub secret token w header
   - Albo usuń endpoint z produkcji (tylko CLI import)
   - Albo whitelist IP addresses (Railway CLI, admin IP)
2. ⬜ Full E2E testing (wszystkie edge cases)
3. ⬜ **Backup bazy danych Railway** (WAŻNE - pominięte dziś z braku czasu!)
4. ⬜ Monitor logs przez 24h (check errors, performance)
5. ⬜ Usuń stare CSV files z data/cleaned/ (cleanup duplicates)
6. ⬜ Update dokumentacji (README.md, deployment guide)
7. ⬜ Performance testing (load time, query speed)
8. ⬜ Verify wszystkie filtry w production
9. ⬜ Test mobile responsive design
10. ⬜ Create git tag: `multi-register-deploy-2026-02-01`
11. ⬜ Verify .dockerignore (upewnij się że data/ nie jest ignorowane)

---

## NOTATKI

**Railway Tips:**
- Build time: 5-10 min (bądź cierpliwy)
- Logs są kluczowe (monitor non-stop)
- `railway shell` useful dla import (no timeout)

**Vercel Tips:**
- Env vars w build time (nie runtime)
- Po zmianie VITE_API_URL: Redeploy required

**Jeśli coś pójdzie źle:**
1. NIE PANIKUJ
2. Check Railway logs (backend errors)
3. Check Vercel logs (build errors)
4. Check browser console (frontend errors)
5. Rollback jeśli krytyczne

**Powodzenia! 🚀**

_Plan zaktualizowany z oryginalnego migration-plan.md do ekspresowego deployment (15:20-17:00) z uwagami Codex wdrożonymi._
