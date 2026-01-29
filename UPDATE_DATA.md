# Instrukcja aktualizacji danych z ESMA

Ten dokument opisuje krok po kroku, jak zaktualizować dane wszystkich 5 rejestrów MiCA z ESMA.

## 📋 Rejestry MiCA

Aplikacja obsługuje wszystkie 5 rejestrów ESMA MiCA:

1. **CASP** - Crypto-Asset Service Providers (Dostawcy usług krypto-aktywów)
2. **OTHER** - White Papers for other crypto-assets (Białe księgi dla innych krypto-aktywów)
3. **ART** - Asset-Referenced Token Issuers (Emitenci tokenów referencyjnych aktywów)
4. **EMT** - E-Money Token Issuers (Emitenci tokenów pieniądza elektronicznego)
5. **NCASP** - Non-Compliant Entities (Podmioty niezgodne z przepisami)

## 📋 Wymagania

- Dostęp do repozytorium GitHub
- Dostęp do Railway dashboard (backend) - opcjonalnie, dla produkcji
- Dostęp do Vercel dashboard (frontend) - opcjonalnie, dla produkcji
- Python 3.11+ (do uruchomienia skryptów aktualizacji i importu)

## 📁 Struktura katalogów

Projekt używa następującej struktury dla plików CSV (per rejestr):

```
data/
├── raw/                    # Surowe pliki CSV pobrane z ESMA
│   ├── casp/
│   │   └── CASP20260129.csv
│   ├── other/
│   │   └── OTHER20260129.csv
│   ├── art/
│   │   └── ART20260129.csv
│   ├── emt/
│   │   └── EMT20260129.csv
│   └── ncasp/
│       └── NCASP20260129.csv
└── cleaned/                # Oczyszczone pliki CSV (przyszłe wersje)
    ├── casp/
    ├── other/
    ├── art/
    ├── emt/
    └── ncasp/
```

**Ważne:**
- Każdy rejestr ma swój własny katalog w `data/raw/`
- Nazwy plików muszą zawierać prefiks rejestru: `CASP`, `OTHER`, `ART`, `EMT`, `NCASP`
- Format daty w nazwie pliku: `yyyymmdd` (np. `CASP20260129.csv`)

## 🔄 Proces aktualizacji

### Metoda A: Automatyczny skrypt orchestracji (Zalecane)

Najprostszy sposób - użyj skryptu, który automatycznie sprawdzi ESMA, pobierze pliki i zaktualizuje frontend:

```bash
# Aktualizuj wszystkie rejestry
python scripts/update_esma_data.py --all

# Aktualizuj konkretny rejestr
python scripts/update_esma_data.py --register casp
python scripts/update_esma_data.py --register other
python scripts/update_esma_data.py --register art
python scripts/update_esma_data.py --register emt
python scripts/update_esma_data.py --register ncasp

# Wymuś ponowne pobranie nawet jeśli plik istnieje
python scripts/update_esma_data.py --all --force
```

Skrypt automatycznie:
1. Sprawdzi czy ESMA zaktualizowała rejestr(y) (porówna daty)
2. Pobierze najnowsze pliki CSV z ESMA
3. Zapisze pliki do odpowiednich katalogów `data/raw/{register}/`
4. Zaktualizuje datę "Last updated" w frontendzie

**Po zakończeniu skryptu:**

1. **Importuj dane do bazy:**
   ```bash
   # Importuj wszystkie rejestry
   python backend/app/import_csv.py --all

   # Lub importuj konkretny rejestr
   python backend/app/import_csv.py --register casp
   python backend/app/import_csv.py --register other
   python backend/app/import_csv.py --register art
   python backend/app/import_csv.py --register emt
   python backend/app/import_csv.py --register ncasp
   ```

2. **Commit i push (opcjonalnie):**
   ```bash
   git add data/raw/ frontend/src/App.jsx
   git commit -m "Update ESMA data to 29 January 2026"
   git push
   ```

**Wymagania:**
- Python 3.11+
- Zainstalowane zależności: `pip install -r backend/requirements.txt`
- Playwright browsers: `python3 -m playwright install chromium` (do sprawdzania strony ESMA)

### Metoda B: Ręczny proces krok po kroku

Jeśli wolisz pełną kontrolę nad każdym krokiem:

### Krok 1: Pobierz nowe pliki CSV z ESMA

Pobierz najnowsze pliki CSV dla wybranych rejestrów:

**URL-e do pobrania:**
- **CASP:** https://www.esma.europa.eu/sites/default/files/2024-12/CASPS.csv
- **OTHER:** https://www.esma.europa.eu/sites/default/files/2024-12/OTHER.csv
- **ART:** https://www.esma.europa.eu/sites/default/files/2024-12/ARTZZ.csv
- **EMT:** https://www.esma.europa.eu/sites/default/files/2024-12/EMTWP.csv
- **NCASP:** https://www.esma.europa.eu/sites/default/files/2024-12/NCASP.csv

**Uwaga:** URL-e mogą się zmieniać w zależności od daty publikacji. Sprawdź stronę ESMA dla aktualnych linków.

Zapisz pliki w odpowiednich katalogach z nazwą zawierającą datę:

```bash
# Przykład: jeśli pobrałeś pliki 29 stycznia 2026
mv ~/Downloads/CASPS.csv data/raw/casp/CASP20260129.csv
mv ~/Downloads/OTHER.csv data/raw/other/OTHER20260129.csv
mv ~/Downloads/ARTZZ.csv data/raw/art/ART20260129.csv
mv ~/Downloads/EMTWP.csv data/raw/emt/EMT20260129.csv
mv ~/Downloads/NCASP.csv data/raw/ncasp/NCASP20260129.csv
```

### Krok 2: Importuj dane do bazy

```bash
# Z głównego katalogu projektu

# Importuj wszystkie rejestry
python backend/app/import_csv.py --all

# Lub importuj konkretne rejestry
python backend/app/import_csv.py --register casp
python backend/app/import_csv.py --register other
# itd.
```

Skrypt automatycznie:
- Znajdzie najnowszy plik CSV w katalogu rejestru
- Wyczyści stare dane tego rejestru z bazy
- Zaimportuje nowe dane
- Utworzy relacje (usługi, kraje passport dla CASP)
- Pokaże statystyki importu

**Przykładowy output:**
```
Processing CASP register...
Found CSV file: data/raw/casp/CASP20260129.csv
Cleared 132 existing CASP entities
Imported 135 entities
```

### Krok 3: Zaktualizuj datę w frontendzie

1. Otwórz plik `frontend/src/App.jsx`
2. Znajdź linię z "Last updated:"
3. Zaktualizuj datę na datę z nowego pliku CSV

```jsx
// Przykład dla pliku z 29 stycznia 2026:
{' '}• Last updated: 29 January 2026
```

**Uwaga:** Data "Last updated" jest wspólna dla wszystkich rejestrów. Jeśli aktualizujesz tylko jeden rejestr, użyj daty tej aktualizacji.

### Krok 4: Sprawdź czy wszystko działa

1. Uruchom backend:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. Uruchom frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. Otwórz http://localhost:5173
4. Przełączaj się między zakładkami rejestrów
5. Sprawdź czy liczba entities się zgadza dla każdego rejestru
6. Sprawdź kilka rekordów czy dane się zgadzają

### Krok 5: Commit i push na GitHub (opcjonalnie)

```bash
# Dodaj zmienione pliki
git add data/raw/ frontend/src/App.jsx

# Zrób commit
git commit -m "Update ESMA data to 29 January 2026"

# Push na GitHub
git push origin main
```

## 📊 Statystyki rejestrów (stan przykładowy)

Po importie możesz sprawdzić liczbę encji w każdym rejestrze:

```bash
# W konsoli Python (w środowisku backend)
python3 << EOF
from app.database import SessionLocal
from app.models import Entity
from app.config.registers import RegisterType

db = SessionLocal()
for reg_type in RegisterType:
    count = db.query(Entity).filter(Entity.register_type == reg_type).count()
    print(f"{reg_type.value.upper()}: {count} entities")
db.close()
EOF
```

**Przykładowy output:**
```
CASP: 132 entities
OTHER: 594 entities
ART: 0 entities
EMT: 17 entities
NCASP: 101 entities
Total: 844 entities
```

## 🔧 Szczegóły techniczne

### Import CSV - jak to działa

Skrypt `backend/app/import_csv.py` dla każdego rejestru:

1. **Znajduje najnowszy plik CSV** w katalogu `data/raw/{register}/`
2. **Czyści stare dane** dla tego rejestru (zachowuje inne rejestry)
3. **Parsuje CSV** z obsługą encoding issues (German characters, itp.)
4. **Normalizuje dane**:
   - Kody krajów (2-letter ISO)
   - Kody usług (a-j dla CASP)
   - Daty (DD/MM/YYYY)
   - Pipe-separated values ("|")
5. **Tworzy rekordy** w bazie:
   - Base Entity record (wspólne pola)
   - Extension record (pola specyficzne dla rejestru)
   - Relacje (services, passport_countries dla CASP)

### Architektura bazy danych

```
entities (base table)
├── register_type: casp|other|art|emt|ncasp
├── Common fields: lei, lei_name, commercial_name, home_member_state, etc.
└── Extension tables (1:1):
    ├── casp_entities (services a-j, passport_countries, website_platform)
    ├── other_entities (white_paper_url, offer_countries, dti_codes)
    ├── art_entities (credit_institution, white_paper_notification_date)
    ├── emt_entities (exemption_48_4, exemption_48_5, authorisation_other_emt)
    └── ncasp_entities (websites, infringement, reason, decision_date)
```

### Mapowanie kolumn CSV → Baza danych

#### Wspólne pola (wszystkie rejestry):
- `ae_competentAuthority` → `competent_authority`
- `ae_homeMemberState` → `home_member_state`
- `ae_lei_name` → `lei_name`
- `ae_lei` → `lei`
- `ae_lei_cou_code` → `lei_cou_code`
- `ae_commercial_name` → `commercial_name`
- `ae_address` → `address`
- `ae_website` → `website`
- `ac_authorisationNotificationDate` → `authorisation_notification_date`
- `ac_lastupdate` → `last_update`
- `ac_comments` → `comments`

#### CASP-specific:
- `ae_website_platform` → `website_platform`
- `ac_authorisationEndDate` → `authorisation_end_date`
- `ac_serviceCode` → `services` (pipe-separated, a-j)
- `ac_serviceCode_cou` → `passport_countries` (pipe-separated)

#### OTHER-specific:
- `wp_url` → `white_paper_url`
- `wp_comments` → `white_paper_comments`
- `wp_lastupdate` → `white_paper_last_update`
- `ae_offerCode_cou` → `offer_countries` (pipe-separated)
- `ae_DTI` → `dti_codes` (pipe-separated)
- `ae_DTI_FFG` → `dti_ffg` (boolean)
- `ae_lei_casp` → `lei_casp` (linked CASP LEI)
- `ae_lei_name_casp` → `lei_name_casp`

#### ART-specific:
- `ae_credit_institution` → `credit_institution` (boolean)
- `wp_url` → `white_paper_url`
- `wp_authorisationNotificationDate` → `white_paper_notification_date`
- `wp_url_cou` → `white_paper_offer_countries` (pipe-separated)
- `wp_comments` → `white_paper_comments`
- `wp_lastupdate` → `white_paper_last_update`

#### EMT-specific:
- `ae_exemption48_4` → `exemption_48_4` (boolean)
- `ae_exemption48_5` → `exemption_48_5` (boolean)
- `ae_authorisation_other_emt` → `authorisation_other_emt`
- `ae_DTI_FFG` → `dti_ffg` (boolean)
- `ae_DTI` → `dti_codes` (pipe-separated)
- `wp_url` → `white_paper_url`
- `wp_authorisationNotificationDate` → `white_paper_notification_date`
- `wp_comments` → `white_paper_comments`
- `wp_lastupdate` → `white_paper_last_update`

#### NCASP-specific:
- `ae_website` → `websites` (pipe-separated multiple websites)
- `ae_infrigment` → `infringement`
- `ae_reason` → `reason`
- `ae_decision_date` → `decision_date`

## 🐛 Rozwiązywanie problemów

### Problem: "CSV file not found" podczas importu

**Rozwiązanie:**
1. Sprawdź czy plik istnieje w katalogu `data/raw/{register}/`
2. Sprawdź nazwę pliku (musi zaczynać się od CASP/OTHER/ART/EMT/NCASP)
3. Sprawdź format daty w nazwie pliku (yyyymmdd)

```bash
# Sprawdź jakie pliki są w katalogu
ls -la data/raw/casp/
ls -la data/raw/other/
# itd.
```

### Problem: Błąd podczas importu - "Invalid encoding"

**Rozwiązanie:**
Skrypt automatycznie obsługuje różne encodingi (UTF-8, Latin-1, Windows-1252). Jeśli nadal jest problem:

1. Sprawdź encoding pliku:
   ```bash
   file -b --mime-encoding data/raw/casp/CASP20260129.csv
   ```

2. Konwertuj do UTF-8 jeśli potrzebne:
   ```bash
   iconv -f WINDOWS-1252 -t UTF-8 data/raw/casp/CASP20260129.csv > temp.csv
   mv temp.csv data/raw/casp/CASP20260129.csv
   ```

### Problem: Brakujące dane w bazie po imporcie

**Rozwiązanie:**
1. Sprawdź logi importu - skrypt pokazuje ile rekordów zaimportowano
2. Sprawdź czy plik CSV ma poprawny format
3. Uruchom import ponownie z flagą --verbose (jeśli dostępna)
4. Sprawdź backend logs dla szczegółów błędów

### Problem: Frontend nie pokazuje nowej daty

**Rozwiązanie:**
1. Sprawdź czy zmiana w `App.jsx` została zapisana
2. Przeładuj frontend (Ctrl+R / Cmd+R)
3. Wyczyść cache przeglądarki (Ctrl+Shift+R / Cmd+Shift+R)
4. Sprawdź czy vite server wykrył zmianę (powinien automatycznie hot reload)

### Problem: Dane z różnych rejestrów mieszają się

**Rozwiązanie:**
To nie powinno się zdarzyć dzięki architekturze z `register_type`. Jeśli się zdarza:

1. Sprawdź czy wszystkie importy używają poprawnej flagi `--register`
2. Sprawdź w bazie danych:
   ```sql
   SELECT register_type, COUNT(*) FROM entities GROUP BY register_type;
   ```
3. W razie potrzeby wyczyść bazę i zaimportuj ponownie

## 📝 Checklist przed aktualizacją

- [ ] Pobrano nowe pliki CSV z ESMA dla wybranych rejestrów
- [ ] Pliki zapisane w odpowiednich katalogach `data/raw/{register}/`
- [ ] Uruchomiono import: `python backend/app/import_csv.py --all` lub per rejestr
- [ ] Sprawdzono statystyki importu (liczba zaimportowanych entities)
- [ ] Zaktualizowano datę w `frontend/src/App.jsx`
- [ ] Sprawdzono czy aplikacja działa lokalnie (wszystkie zakładki)
- [ ] (Opcjonalnie) Zrobiono commit i push na GitHub
- [ ] (Opcjonalnie - produkcja) Zdeployowano do Railway/Vercel

## 🔄 Automatyzacja (przyszłość)

### Obecny stan

✅ **Zaimplementowane:**
- Automatyczne sprawdzanie strony ESMA pod kątem nowych aktualizacji
- Automatyczne pobieranie plików CSV dla wszystkich rejestrów
- Skrypt orchestracji: `scripts/update_esma_data.py --all`
- Multi-register import: `backend/app/import_csv.py --all`

⏳ **Do zaimplementowania (planowane):**
- Automatyczna walidacja i czyszczenie plików CSV
- Automatyczny import po pobraniu
- Automatyczny commit i push do GitHub
- Cron job do regularnego sprawdzania i aktualizacji
- Notyfikacje (email/Slack) po aktualizacji
- Per-register "Last updated" display w UI

## 🔗 Przydatne linki

- **ESMA MiCA Registers:** https://www.esma.europa.eu/press-news/esma-news/esma-publishes-first-list-crypto-asset-service-providers-casps-authorised-under-mica
- **Railway Dashboard:** https://railway.app (opcjonalnie, dla produkcji)
- **Vercel Dashboard:** https://vercel.com (opcjonalnie, dla produkcji)
- **GitHub Repository:** https://github.com/your-repo/mica-register

## 📞 Kontakt / Wsparcie

Jeśli masz problemy z aktualizacją:
1. Sprawdź logi w konsoli podczas importu
2. Sprawdź czy wszystkie kroki zostały wykonane
3. Sprawdź dokumentację w `README.md`
4. Sprawdź backend logs (`uvicorn app.main:app --reload`)

---

**Ostatnia aktualizacja instrukcji:** 29 stycznia 2026
