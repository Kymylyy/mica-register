# Jak znaleźć Shell w Railway Dashboard

## Lokalizacja Shell w Railway Dashboard:

### Metoda 1: W Service View (Najczęściej tutaj)
1. **Kliknij na kafelek "mica-register"** (nie Postgres)
2. Zobaczysz widok z zakładkami na górze:
   - **Deployments**
   - **Metrics** 
   - **Logs**
   - **Settings**
   - **Variables**
3. **Sprawdź prawy górny róg** - powinien być przycisk:
   - **"Connect"** lub
   - **"Shell"** lub
   - **"Terminal"** lub
   - Ikona terminala/console

### Metoda 2: W Settings
1. Kliknij na kafelek "mica-register"
2. Przejdź do zakładki **"Settings"**
3. Przewiń w dół - szukaj sekcji:
   - **"Connect"** lub
   - **"Shell Access"** lub
   - **"Terminal"**

### Metoda 3: W Deployments
1. Kliknij na kafelek "mica-register"
2. Przejdź do zakładki **"Deployments"**
3. Kliknij na **najnowszy deployment** (ten z zielonym checkmarkiem)
4. W szczegółach deploymentu szukaj:
   - **"Shell"** lub
   - **"Connect"** lub
   - **"Terminal"**

### Metoda 4: Menu trzech kropek (...)
1. Kliknij na kafelek "mica-register"
2. Szukaj ikony **trzech kropek (...)** w prawym górnym rogu
3. Kliknij - powinno być menu z opcją **"Shell"** lub **"Connect"**

### Metoda 5: W Logs
1. Kliknij na kafelek "mica-register"
2. Przejdź do zakładki **"Logs"**
3. W prawym górnym rogu może być przycisk **"Shell"** lub **"Terminal"**

---

## Jeśli nadal nie widzisz Shell:

**Użyj Railway CLI** (najprostsze rozwiązanie):

```bash
# 1. Zainstaluj Railway CLI
npm i -g @railway/cli

# 2. Zaloguj się
railway login

# 3. Połącz z projektem (wybierz "mica-register" z listy)
railway link

# 4. Uruchom import
railway run python import_data.py
```

---

## Co zobaczysz w Shell:

Po otwarciu Shell zobaczysz terminal z promptem podobnym do:
```
/app $ 
```

Wtedy uruchom:
```bash
python import_data.py
```

