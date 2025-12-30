# Instrukcja aktualizacji danych z ESMA

Ten dokument opisuje krok po kroku, jak zaktualizować dane na stronie WWW, gdy ESMA opublikuje nowy plik CSV z rejestrem CASP.

## 📋 Wymagania

- Dostęp do repozytorium GitHub
- Dostęp do Railway dashboard (backend)
- Dostęp do Vercel dashboard (frontend) - opcjonalnie, jeśli chcesz sprawdzić deployment
- Python 3.11+ (do uruchomienia skryptów walidacji i czyszczenia)

## 📁 Struktura katalogów

Projekt używa następującej struktury dla plików CSV:

```
data/
├── raw/              # Surowe pliki CSV pobrane z ESMA
│   └── CASP20251215.csv
└── cleaned/          # Oczyszczone pliki CSV gotowe do importu
    └── CASP20251215_clean.csv
```

**Ważne:** Endpoint importu automatycznie znajduje najnowszy plik `*_clean.csv` w katalogu `data/cleaned/`, więc nie musisz aktualizować kodu przy każdym nowym pliku.

## 🔄 Proces aktualizacji

### Krok 1: Pobierz nowy plik CSV z ESMA

1. Pobierz najnowszy plik CSV z [ESMA Register](https://www.esma.europa.eu/press-news/esma-news/esma-publishes-first-list-crypto-asset-service-providers-casps-authorised-under-mica)
2. Zapisz plik w katalogu `data/raw/` z nazwą zawierającą datę: `CASP20251215.csv` (format: `CASPYYYYMMDD.csv`)

```bash
# Przykład: jeśli pobrałeś plik 15 grudnia 2025
mv ~/Downloads/CASP_register.csv data/raw/CASP20251215.csv
```

### Krok 2: Walidacja pliku CSV (opcjonalne, ale zalecane)

Sprawdź czy plik nie ma błędów przed czyszczeniem:

```bash
# Z głównego katalogu projektu
python scripts/validate_csv.py data/raw/CASP20251215.csv
```

Skrypt pokaże:
- Błędy (ERROR) - wymagają naprawy przed importem
- Ostrzeżenia (WARNING) - mogą być automatycznie naprawione podczas czyszczenia

**Uwaga:** Jeśli są tylko ostrzeżenia, możesz przejść do następnego kroku - skrypt czyszczący automatycznie je naprawi.

### Krok 3: Oczyszczenie pliku CSV

Skrypt automatycznie naprawi wszystkie wykryte problemy (encoding, daty, białe znaki, duplikaty LEI, itp.):

```bash
# Z głównego katalogu projektu
python scripts/clean_csv.py --input data/raw/CASP20251215.csv --output data/cleaned/CASP20251215_clean.csv
```

To utworzy oczyszczony plik `CASP20251215_clean.csv` w katalogu `data/cleaned/`.

**Co jest naprawiane automatycznie:**
- Błędy encoding (np. `Stra�e` → `Straße`)
- Błędy w datach (np. `01/12/.2025` → `01/12/2025`)
- Białe znaki i spacje
- Duplikaty LEI (mergowane w jeden rekord)
- Problemy z formatem LEI
- Wielowierszowe pola
- Normalizacja kodów krajów i usług

**Opcjonalnie:** Możesz zapisać raport z czyszczenia:

```bash
python scripts/clean_csv.py --input data/raw/CASP20251215.csv --output data/cleaned/CASP20251215_clean.csv --report cleaning_report.json
```

### Krok 4: Zaktualizuj datę w frontendzie

1. Otwórz plik `frontend/src/App.jsx`
2. Znajdź linię z "Last updated:"
3. Zaktualizuj datę na datę z nowego pliku CSV

```jsx
// Przykład dla pliku z 15 grudnia 2025:
{' '}• Last updated: 15 December 2025
```

### Krok 5: Commit i push na GitHub

```bash
# Dodaj zmienione pliki
git add data/raw/CASP20251215.csv data/cleaned/CASP20251215_clean.csv frontend/src/App.jsx

# Zrób commit
git commit -m "Update CSV data to ESMA register from 15 December 2025"

# Push na GitHub
git push origin main
```

**Uwaga:** Zastąp datę w nazwie pliku i commicie rzeczywistą datą.

### Krok 6: Poczekaj na automatyczny deployment

Po pushu na GitHub:
- **Railway** automatycznie zbuduje nowy obraz Docker z nowym CSV w katalogu `data/cleaned/`
- **Vercel** automatycznie zaktualizuje frontend

Czas deploymentu: zwykle 2-5 minut.

Możesz sprawdzić status:
- Railway dashboard → Twój projekt → Deployments
- Vercel dashboard → Twój projekt → Deployments

### Krok 7: Wywołaj import danych na Railway

**To jest najważniejszy krok!** Railway ma nowy CSV w kontenerze, ale dane w bazie nie aktualizują się automatycznie.

Endpoint `/api/admin/import` automatycznie znajdzie najnowszy plik `*_clean.csv` w katalogu `data/cleaned/`.

#### Opcja A: Użyj skryptu (zalecane)

```bash
./update_production.sh https://mica-register-production.up.railway.app
```

#### Opcja B: Bezpośrednio przez curl

```bash
curl -X POST https://mica-register-production.up.railway.app/api/admin/import
```

**Oczekiwana odpowiedź:**
```json
{
  "message": "Data imported successfully",
  "csv_path": "/app/data/cleaned/CASP20251215_clean.csv",
  "entities_count": 118
}
```

**Ważne:** Sprawdź czy `csv_path` wskazuje na najnowszy plik i czy `entities_count` się zgadza.

### Krok 8: Sprawdź czy wszystko działa

1. Otwórz stronę WWW
2. Sprawdź czy liczba entities się zgadza (powinna być widoczna w headerze)
3. Sprawdź czy data "Last updated" jest zaktualizowana
4. Sprawdź kilka rekordów czy dane się zgadzają

## 🐛 Rozwiązywanie problemów

### Problem: Nadal widzę starą liczbę entities

**Rozwiązanie:**
1. Sprawdź czy import się udał (krok 7) - sprawdź odpowiedź endpointu
2. Sprawdź czy endpoint użył najnowszego pliku (sprawdź `csv_path` w odpowiedzi)
3. Wyczyść cache przeglądarki (Ctrl+Shift+R / Cmd+Shift+R)
4. Sprawdź w trybie incognito
5. Sprawdź w Railway logs czy nie było błędów

### Problem: Błąd podczas importu - "CSV file not found"

**Rozwiązanie:**
1. Sprawdź czy plik `*_clean.csv` został dodany do commita i jest w katalogu `data/cleaned/`
2. Sprawdź Railway logs:
   - Railway dashboard → Twój projekt → Deployments → Ostatni deployment → Logs
3. Sprawdź czy Dockerfile kopiuje katalog `data/` (linia 19 w `Dockerfile`)
4. Zrób redeploy na Railway (Settings → Redeploy)

### Problem: Błąd podczas importu - inne błędy

**Rozwiązanie:**
1. Sprawdź Railway logs:
   - Railway dashboard → Twój projekt → Deployments → Ostatni deployment → Logs
2. Sprawdź czy plik CSV jest poprawny (format, encoding)
3. Uruchom walidację lokalnie: `python scripts/validate_csv.py data/cleaned/CASP20251215_clean.csv`
4. Sprawdź czy wszystkie daty są w poprawnym formacie

### Problem: Frontend nie pokazuje nowej daty

**Rozwiązanie:**
1. Sprawdź czy Vercel zakończył deployment:
   - Vercel dashboard → Twój projekt → Deployments
2. Sprawdź czy commit został wypushowany
3. Sprawdź czy zmiana w `App.jsx` została zapisana i dodana do commita

### Problem: Endpoint używa starego pliku zamiast nowego

**Rozwiązanie:**
1. Sprawdź czy nowy plik `*_clean.csv` jest w katalogu `data/cleaned/` i ma najnowszą datę modyfikacji
2. Sprawdź czy plik został skopiowany do kontenera Docker (sprawdź Railway logs)
3. Endpoint wybiera plik na podstawie daty modyfikacji - upewnij się, że nowy plik jest najnowszy

## 📝 Checklist przed aktualizacją

- [ ] Pobrano nowy plik CSV z ESMA
- [ ] Plik zapisany w `data/raw/CASPYYYYMMDD.csv`
- [ ] (Opcjonalnie) Uruchomiono walidację: `python scripts/validate_csv.py data/raw/CASPYYYYMMDD.csv`
- [ ] Uruchomiono czyszczenie: `python scripts/clean_csv.py --input data/raw/CASPYYYYMMDD.csv --output data/cleaned/CASPYYYYMMDD_clean.csv`
- [ ] Sprawdzono czy plik `*_clean.csv` został utworzony w `data/cleaned/`
- [ ] Zaktualizowano datę w `frontend/src/App.jsx`
- [ ] Zrobiono commit i push na GitHub
- [ ] Poczekano na deployment Railway i Vercel (2-5 minut)
- [ ] Wywołano endpoint `/api/admin/import` na Railway
- [ ] Sprawdzono odpowiedź endpointu (czy użył najnowszego pliku i czy liczba entities się zgadza)
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
4. Sprawdź dokumentację skryptów w `docs/CSV_CLEANING.md` i `docs/CSV_VALIDATION.md`

---

**Ostatnia aktualizacja instrukcji:** 15 grudnia 2025
