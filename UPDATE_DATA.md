# Instrukcja aktualizacji danych z ESMA

Ten dokument opisuje krok po kroku, jak zaktualizować dane na stronie WWW, gdy ESMA opublikuje nowy plik CSV z rejestrem CASP.

## 📋 Wymagania

- Dostęp do repozytorium GitHub
- Dostęp do Railway dashboard (backend)
- Dostęp do Vercel dashboard (frontend) - opcjonalnie, jeśli chcesz sprawdzić deployment

## 🔄 Proces aktualizacji

### Krok 1: Pobierz nowy plik CSV z ESMA

1. Pobierz najnowszy plik CSV z [ESMA Register](https://www.esma.europa.eu/press-news/esma-news/esma-publishes-first-list-crypto-asset-service-providers-casps-authorised-under-mica)
2. Zapisz plik w głównym katalogu projektu jako `2025MMDD.csv` (np. `20251204.csv`)

### Krok 2: Przygotuj plik CSV

1. Otwórz nowy plik CSV w edytorze
2. Sprawdź czy format jest zgodny z poprzednim (te same kolumny)
3. Sprawdź czy nie ma błędów w datach (np. `01/12/.2025` zamiast `01/12/2025`)
   - Jeśli znajdziesz błędy, napraw je ręcznie

### Krok 3: Zastąp stary plik CSV

```bash
# Skopiuj nowy plik CSV do głównego pliku
cp 2025MMDD.csv casp-register.csv
```

**Uwaga:** Zastąp `2025MMDD.csv` rzeczywistą nazwą pliku.

### Krok 4: Zaktualizuj datę w frontendzie

1. Otwórz plik `frontend/src/App.jsx`
2. Znajdź linię z "Last updated:"
3. Zaktualizuj datę na datę z nowego pliku CSV

```jsx
// Przykład:
{' '}• Last updated: 4 December 2025
```

### Krok 5: Sprawdź czy są błędy w CSV

Przed commitem sprawdź czy:
- Wszystkie daty są w formacie `DD/MM/YYYY`
- Nie ma błędów z dodatkowymi kropkami (np. `01/12/.2025`)
- Funkcja `parse_date` w `backend/app/import_csv.py` automatycznie naprawi niektóre błędy, ale lepiej sprawdzić ręcznie

### Krok 6: Commit i push na GitHub

```bash
# Dodaj zmienione pliki
git add casp-register.csv frontend/src/App.jsx

# Zrób commit
git commit -m "Update CSV data to ESMA register from [DATA] and update last updated date"

# Push na GitHub
git push origin main
```

**Uwaga:** Zastąp `[DATA]` rzeczywistą datą (np. "4 December 2025")

### Krok 7: Poczekaj na automatyczny deployment

Po pushu na GitHub:
- **Railway** automatycznie zbuduje nowy obraz Docker z nowym CSV
- **Vercel** automatycznie zaktualizuje frontend

Czas deploymentu: zwykle 2-5 minut.

### Krok 8: Wywołaj import danych na Railway

**To jest najważniejszy krok!** Railway ma nowy CSV w kontenerze, ale dane w bazie nie aktualizują się automatycznie.

#### Opcja A: Użyj skryptu (zalecane)

```bash
./update_production.sh https://mica-register-production.up.railway.app
```

#### Opcja B: Bezpośrednio przez curl

```bash
curl -X POST https://mica-register-production.up.railway.app/api/admin/import
```

#### Opcja C: Przez przeglądarkę (tylko sprawdzenie)

Otwórz w przeglądarce (ale to nie zadziała dla POST, użyj curl):
```
https://mica-register-production.up.railway.app/api/admin/import
```

**Oczekiwana odpowiedź:**
```json
{
  "message": "Data imported successfully",
  "csv_path": "/app/casp-register.csv",
  "entities_count": 102
}
```

### Krok 9: Sprawdź czy wszystko działa

1. Otwórz stronę WWW
2. Sprawdź czy liczba entities się zgadza (powinna być widoczna w headerze)
3. Sprawdź czy data "Last updated" jest zaktualizowana
4. Sprawdź kilka rekordów czy dane się zgadzają

## 🐛 Rozwiązywanie problemów

### Problem: Nadal widzę starą liczbę entities

**Rozwiązanie:**
1. Sprawdź czy import się udał (krok 8)
2. Wyczyść cache przeglądarki (Ctrl+Shift+R / Cmd+Shift+R)
3. Sprawdź w trybie incognito
4. Sprawdź w Railway logs czy nie było błędów

### Problem: Błąd podczas importu

**Rozwiązanie:**
1. Sprawdź Railway logs:
   - Railway dashboard → Twój projekt → Deployments → Ostatni deployment → Logs
2. Sprawdź czy plik CSV jest poprawny (format, encoding)
3. Sprawdź czy wszystkie daty są w poprawnym formacie

### Problem: Frontend nie pokazuje nowej daty

**Rozwiązanie:**
1. Sprawdź czy Vercel zakończył deployment:
   - Vercel dashboard → Twój projekt → Deployments
2. Sprawdź czy commit został wypushowany
3. Sprawdź czy zmiana w `App.jsx` została zapisana

### Problem: Railway nie ma nowego CSV

**Rozwiązanie:**
1. Sprawdź czy plik `casp-register.csv` został dodany do commita
2. Sprawdź czy Dockerfile kopiuje plik CSV (linia 19 w `Dockerfile`)
3. Zrób redeploy na Railway (Settings → Redeploy)

## 📝 Checklist przed aktualizacją

- [ ] Pobrano nowy plik CSV z ESMA
- [ ] Sprawdzono format i błędy w CSV
- [ ] Zastąpiono `casp-register.csv` nowym plikiem
- [ ] Zaktualizowano datę w `frontend/src/App.jsx`
- [ ] Zrobiono commit i push na GitHub
- [ ] Poczekano na deployment Railway i Vercel
- [ ] Wywołano endpoint `/api/admin/import` na Railway
- [ ] Sprawdzono czy strona WWW pokazuje nowe dane

## 🔗 Przydatne linki

- **Railway Dashboard:** https://railway.app
- **Vercel Dashboard:** https://vercel.com
- **ESMA Register:** https://www.esma.europa.eu/press-news/esma-news/esma-publishes-first-list-crypto-asset-service-providers-casps-authorised-under-mica
- **Railway API URL:** https://mica-register-production.up.railway.app

## 📞 Kontakt / Wsparcie

Jeśli masz problemy z aktualizacją:
1. Sprawdź logi w Railway
2. Sprawdź logi w Vercel
3. Sprawdź czy wszystkie kroki zostały wykonane

---

**Ostatnia aktualizacja instrukcji:** 4 grudnia 2025

