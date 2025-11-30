# Deployment Checklist

## ✅ Backend (Railway) - Deployment Done!

### 1. Add PostgreSQL Database
- [ ] W Railway dashboard, kliknij **"New"** → **"Database"** → **"PostgreSQL"**
- [ ] Railway automatycznie ustawi `DATABASE_URL` environment variable
- [ ] Sprawdź czy `DATABASE_URL` jest widoczny w Settings → Variables

### 2. Configure Environment Variables
W Railway project → Settings → Variables, dodaj:

- [ ] **`CORS_ORIGINS`** = URL Twojego frontendu z Vercel
  - Przykład: `https://mica-register.vercel.app`
  - Jeśli masz kilka domen, oddziel je przecinkami: `https://app1.vercel.app,https://app2.vercel.app`

### 3. Import Initial Data
Po dodaniu PostgreSQL, musisz zaimportować dane z CSV:

**Opcja A: Railway CLI (Rekomendowane)**
```bash
# Zainstaluj Railway CLI jeśli jeszcze nie masz
npm i -g @railway/cli

# Zaloguj się
railway login

# Połącz z projektem
railway link

# Uruchom import (musisz mieć casp-register.csv w root directory)
railway run python backend/import_data.py
```

**Opcja B: Railway Dashboard**
- [ ] W Railway dashboard, otwórz service → **"Deployments"** → wybierz najnowszy deployment
- [ ] Kliknij **"View Logs"** → **"Shell"** (jeśli dostępne)
- [ ] Lub użyj **"Connect"** → **"Shell"** w service settings
- [ ] W shellu uruchom:
  ```bash
  cd /app
  python import_data.py
  ```

**Opcja C: Admin Endpoint (Dla przyszłości)**
- [ ] Możesz stworzyć admin endpoint `/api/admin/import` do importu danych przez API

### 4. Verify Backend is Working
- [ ] Sprawdź czy backend URL działa: `https://your-app.railway.app`
- [ ] Sprawdź API docs: `https://your-app.railway.app/docs`
- [ ] Sprawdź czy endpoint `/api/entities` zwraca dane (po imporcie)

---

## 🎨 Frontend (Vercel) - To Do

### 1. Connect Repository to Vercel
- [ ] Idź na [vercel.com](https://vercel.com) i zaloguj się
- [ ] Kliknij **"New Project"**
- [ ] Importuj repozytorium `mica-register`
- [ ] **WAŻNE:** Ustaw **Root Directory** na `frontend`
- [ ] Framework Preset: **Vite** (powinien być wykryty automatycznie)
- [ ] Kliknij **"Deploy"**

### 2. Configure Environment Variables
W Vercel project → Settings → Environment Variables, dodaj:

- [ ] **`VITE_API_URL`** = URL Twojego backendu z Railway
  - Przykład: `https://mica-register-production.up.railway.app`
  - **WAŻNE:** Bez końcowego slasha `/`

### 3. Redeploy Frontend
- [ ] Po dodaniu environment variable, Vercel automatycznie zrobi redeploy
- [ ] Lub kliknij **"Deployments"** → **"Redeploy"**

### 4. Verify Frontend is Working
- [ ] Sprawdź czy frontend URL działa
- [ ] Sprawdź czy API calls działają (otwórz DevTools → Network)
- [ ] Sprawdź czy dane się ładują z backendu

---

## 🔄 Update CORS in Railway

Po deploymencie frontendu na Vercel:

- [ ] Wróć do Railway → Settings → Variables
- [ ] Zaktualizuj **`CORS_ORIGINS`** z dokładnym URL frontendu z Vercel
- [ ] Railway automatycznie zrestartuje service

---

## ✅ Final Verification

- [ ] Backend API działa: `https://your-backend.railway.app/docs`
- [ ] Frontend działa: `https://your-frontend.vercel.app`
- [ ] Frontend łączy się z backendem (sprawdź w DevTools)
- [ ] Dane się ładują w tabeli
- [ ] Filtry działają
- [ ] Modal z detalami działa

---

## 🐛 Troubleshooting

### Backend nie działa:
- Sprawdź logs w Railway dashboard
- Sprawdź czy `DATABASE_URL` jest ustawione
- Sprawdź czy port jest poprawny (Railway używa zmiennej PORT)

### Frontend nie łączy się z backendem:
- Sprawdź czy `VITE_API_URL` jest ustawione w Vercel
- Sprawdź CORS errors w DevTools → Console
- Sprawdź czy `CORS_ORIGINS` w Railway zawiera URL frontendu
- Sprawdź Network tab w DevTools - czy requesty idą do dobrego URL

### Baza danych pusta:
- Sprawdź czy import się powiódł (sprawdź logs)
- Sprawdź czy `DATABASE_URL` wskazuje na właściwą bazę
- Uruchom import ponownie

---

## 📝 Notes

- Railway automatycznie restartuje service po zmianie environment variables
- Vercel automatycznie redeployuje po zmianie environment variables
- Po każdym pushu do main branch, oba serwisy automatycznie się redeployują

