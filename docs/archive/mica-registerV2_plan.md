## Zmiany wprowadzone w tej rewizji (dla Claude)
- Skorygowałem nieścisłości w liście plików (np. `frontend/src/main.jsx` już istnieje – teraz do modyfikacji, nie „NOWY”).
- Dodałem kluczową zmianę schematu: usunięcie globalnej unikalności `lei` i zastąpienie jej unikalnością per rejestr (`register_type`, `lei`).
- Doprecyzowałem model relacji CASP: `services` i `passport_countries` przeniesione do warstwy CASP (nowe tabele asocjacyjne z FK do `casp_entities`).
- Uzupełniłem brakujące miejsca w backendzie (np. `schemas.py`, `tests/`, `scripts/check_esma_update.py`) i doprecyzowałem migrację dla SQLite.
- Usunąłem/ograniczyłem niepewne optymalizacje (np. `query_cache_size`) i połączyłem zduplikowane sekcje performance.
- Dodałem etap „walidacji CSV/headers” przed właściwą implementacją, bo pozostałe rejestry mogą mieć inne nagłówki.

# Plan: Rozszerzenie aplikacji MICA o wszystkie 5 rejestrów ESMA

## Podsumowanie

Rozbudowa obecnej aplikacji obsługującej jeden rejestr (CASP - Crypto-Asset Service Providers) do systemu wspierającego wszystkie 5 rejestrów ESMA MiCA:

1. **CASP** - Crypto-Asset Service Providers (obecny)
2. **OTHER** - White papers dla innych krypto-aktywów
3. **ART** - Emitenci tokenów referencyjnych aktywów (Asset-Referenced Tokens)
4. **EMT** - Emitenci tokenów pieniądza elektronicznego (E-Money Tokens)
5. **NCASP** - Podmioty niezgodne z przepisami

## Architektura: podejście hybrydowe (base + rozszerzenia)

### 1. Schemat bazy danych

**Strategia**: tabela bazowa `entities` + tabele rozszerzeń (1:1) per rejestr.

```
entities (wspólne pola + register_type)
├── casp_entities (pola CASP + relacje services/passport)
├── other_entities (pola white papers)
├── art_entities (pola ART)
├── emt_entities (pola EMT)
└── ncasp_entities (pola NCASP)
```

**Uzasadnienie**:
- ✅ Bezpieczeństwo typów (SQLAlchemy + Pydantic)
- ✅ Wydajność zapytań (1 join do tabeli rozszerzeń)
- ✅ Łatwa rozbudowa (nowy rejestr = nowa tabela rozszerzeń)
- ✅ Wspólna logika w klasie bazowej

**Ważna korekta względem obecnego schematu**:
- `lei` **nie może być globalnie unikalne** – ta sama instytucja może pojawić się w wielu rejestrach.
- Docelowo: unikalność `(register_type, lei)` albo brak unikalności i indeks na `(register_type, lei)`.

### 2. Relacje CASP

`services` i `passport_countries` są **tylko dla CASP**. Przenosimy je na warstwę CASP:

```
casp_entities
├── casp_entity_service (FK -> casp_entities.id)
└── casp_entity_passport_country (FK -> casp_entities.id)
```

To usuwa „śmieciowe” relacje dla OTHER/ART/EMT/NCASP i upraszcza filtrowanie.

## API (wspólne endpointy)

**Endpoint**: `/api/entities?register_type=casp`

Parametry:
- `register_type` (wymagany, ale z domyślną wartością): `casp|other|art|emt|ncasp`
- Wspólne filtry: `search`, `home_member_states`, `auth_date_from/to`
- Specyficzne filtry:
  - CASP: `service_codes`
  - ART: `credit_institution`
  - EMT: `exemption_48_4`, `exemption_48_5`

**Backend compatibility**: domyślnie `register_type=casp` dla istniejących klientów.

**Do aktualizacji**:
- `/api/entities`
- `/api/entities/count`
- `/api/filters/options`
- `/api/filters/counts`

## Frontend UX

**Nawigacja**: Zakładki poziome (styl GitHub)
```
[ CASPs ] [ Other ] [ ART ] [ EMT ] [ NCASP ]
```

**Routing** (React Router – modyfikujemy istniejące `frontend/src/main.jsx`):
- `/casp` - Crypto-Asset Service Providers (domyślny)
- `/other` - White Papers
- `/art` - Asset-Referenced Tokens
- `/emt` - E-Money Tokens
- `/ncasp` - Non-Compliant Entities

**Komponenty**:
- `RegisterSelector` - zakładki nawigacyjne
- `Filters` - dynamiczne filtry zależne od rejestru
- `DataTable` - kolumny dostosowane do rejestru
- (Opcjonalnie) wydzielony modal z detalami entity

## Kluczowe pliki do modyfikacji

### Backend

1. **`backend/app/models.py`**
   - dodać `register_type`
   - przenieść pola CASP do `CaspEntity`
   - nowe tabele: `OtherEntity`, `ArtEntity`, `EmtEntity`, `NcaspEntity`
   - nowe tabele asocjacyjne CASP

2. **`backend/app/schemas.py`**
   - dodać `register_type`
   - osobne schemy per rejestr lub `Entity` z polami opcjonalnymi

3. **`backend/app/config/registers.py`** (NOWY)
   - definicje rejestrów, mapowania kolumn, walidacje per rejestr

4. **`backend/app/routers/entities.py`**
   - filtr `register_type`
   - filtry zależne od rejestru
   - `/filters/options` i `/filters/counts` per rejestr

5. **`backend/app/import_csv.py`**
   - parametr `register_type`
   - parser per rejestr
   - tworzenie wpisów w `entities` + tabeli rozszerzeń

6. **`backend/app/csv_validate.py` + `backend/app/csv_clean.py`**
   - walidacja per rejestr (z configu)
   - testy spójności: daty, LEI, kody, URL

### Frontend

1. **`frontend/src/main.jsx`**
   - wprowadzić routing (React Router)

2. **`frontend/src/components/RegisterSelector.jsx`** (NOWY)
   - zakładki nawigacyjne

3. **`frontend/src/App.jsx`**
   - dodać `registerType`
   - przekazać do API calls
   - renderowanie kolumn/filters specyficznych

4. **`frontend/src/components/Filters.jsx`**
   - `registerType` jako prop
   - dynamiczne filtry per rejestr

5. **`frontend/src/config/registerColumns.js`** (NOWY)
   - definicje kolumn tabeli per rejestr

### Scripts / tests

1. **`scripts/check_esma_update.py`**
   - wsparcie wielu rejestrów (nazwa plików, daty, cache)

2. **`scripts/update_esma_data.py`**
   - `--register=casp|other|art|emt|ncasp`
   - `--all` dla pełnej aktualizacji

3. **`scripts/clean_csv.py` / `scripts/validate_csv.py`**
   - argument `--register` + użycie konfiguracji rejestrów

4. **`tests/`**
   - aktualizacja `test_import.py`, `test_validate_csv.py`, `test_search_api.py` pod multi-register

## Struktura katalogów danych

```
data/
├── raw/
│   ├── casp/CASP20260123.csv
│   ├── other/OTHER20260123.csv
│   ├── art/ART20260123.csv
│   ├── emt/EMT20260123.csv
│   └── ncasp/NCASP20260123.csv
└── cleaned/
    ├── casp/CASP20260123_clean.csv
    ├── other/OTHER20260123_clean.csv
    ├── art/ART20260123_clean.csv
    ├── emt/EMT20260123_clean.csv
    └── ncasp/NCASP20260123_clean.csv
```

## Migracja bazy danych (PostgreSQL + SQLite)

### Krok 0: Backup
- Zrzut bazy i snapshot plików `data/cleaned`

### Krok 1: `register_type` + indeksy
```sql
ALTER TABLE entities ADD COLUMN register_type VARCHAR NOT NULL DEFAULT 'casp';
CREATE INDEX ix_entities_register_type ON entities(register_type);
```

### Krok 2: unikalność `lei`
```sql
-- Usunięcie globalnej unikalności
DROP INDEX IF EXISTS ix_entities_lei; -- zależnie od nazwy
-- Nowy indeks per rejestr
CREATE INDEX ix_entities_register_lei ON entities(register_type, lei);
```

> **SQLite**: wymagana przebudowa tabeli (CREATE TABLE new_entities + INSERT + DROP old).

### Krok 3: tabele rozszerzeń
```sql
CREATE TABLE casp_entities (
    id INTEGER PRIMARY KEY REFERENCES entities(id),
    website_platform VARCHAR,
    authorisation_end_date DATE
);

CREATE TABLE other_entities (
    id INTEGER PRIMARY KEY REFERENCES entities(id),
    white_paper_url VARCHAR,
    white_paper_comments TEXT,
    white_paper_last_update DATE,
    offer_countries TEXT,
    dti_codes TEXT,
    dti_ffg BOOLEAN,
    lei_casp VARCHAR
);

-- Analogicznie: art_entities, emt_entities, ncasp_entities
```

### Krok 4: CASP relacje
```sql
CREATE TABLE casp_entity_service (
    casp_entity_id INTEGER REFERENCES casp_entities(id),
    service_id INTEGER REFERENCES services(id),
    PRIMARY KEY (casp_entity_id, service_id)
);

CREATE TABLE casp_entity_passport_country (
    casp_entity_id INTEGER REFERENCES casp_entities(id),
    country_id INTEGER REFERENCES passport_countries(id),
    PRIMARY KEY (casp_entity_id, country_id)
);
```

### Krok 5: migracja danych CASP
```sql
INSERT INTO casp_entities (id, website_platform, authorisation_end_date)
SELECT id, website_platform, authorisation_end_date FROM entities WHERE register_type = 'casp';

INSERT INTO casp_entity_service (casp_entity_id, service_id)
SELECT entity_id, service_id FROM entity_service;

INSERT INTO casp_entity_passport_country (casp_entity_id, country_id)
SELECT entity_id, country_id FROM entity_passport_country;
```

### Krok 6: usunięcie starych pól CASP
```sql
ALTER TABLE entities DROP COLUMN website_platform;
ALTER TABLE entities DROP COLUMN authorisation_end_date;
DROP TABLE entity_service;
DROP TABLE entity_passport_country;
```

## Walidacja CSV i mapowanie kolumn

**Nowy etap przed implementacją**: pobrać przykładowe CSV dla OTHER/ART/EMT/NCASP i potwierdzić nagłówki.

Mapowanie wstępne (do weryfikacji):

### Wspólne kolumny (większość rejestrów)
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
- `ac_comments` / `wp_comments` → `comments`

### CASP-specific
- `ae_website_platform` → `website_platform`
- `ac_authorisationEndDate` → `authorisation_end_date`
- `ac_serviceCode` → `services` (pipe-separated, a-j)
- `ac_serviceCode_cou` → `passport_countries`

### OTHER-specific
- `wp_url` → `white_paper_url`
- `wp_comments` → `white_paper_comments`
- `wp_lastupdate` → `white_paper_last_update`
- `ae_offerCode_cou` → `offer_countries`
- `ae_DTI` → `dti_codes`
- `ae_DTI_FFG` → `dti_ffg`
- `ae_lei_casp` → `lei_casp`

### ART-specific
- `ae_credit_institution` → `credit_institution`
- `wp_url` → `white_paper_url`
- `wp_authorisationNotificationDate` → `white_paper_notification_date`
- `wp_url_cou` → `white_paper_offer_countries`
- `wp_comments` → `white_paper_comments`
- `wp_lastupdate` → `white_paper_last_update`

### EMT-specific
- `ae_exemption48_4` → `exemption_48_4`
- `ae_exemption48_5` → `exemption_48_5`
- `ae_authorisation_other_emt` → `authorisation_other_emt`
- `ae_DTI_FFG` → `dti_ffg`
- `ae_DTI` → `dti_codes`
- `wp_url` → `white_paper_url`
- `wp_authorisationNotificationDate` → `white_paper_notification_date`
- `wp_comments` → `white_paper_comments`
- `wp_lastupdate` → `white_paper_last_update`

### NCASP-specific
- `ae_infrigment` → `infringement`
- `ae_reason` → `reason`
- `ae_decision_date` → `decision_date`
- `ae_website` → `websites` (pipe-separated)

## Ulepszenia obecnego rejestru CASP

### Problemy w danych CASP20260123.csv:
1. Duplikaty kodów usług (linia 16 - Revolut)
2. Spacje końcowe w `competent_authority` (linie 4-7)
3. Spacje przed kodami usług (linia 7)
4. Encoding issues (linie 2-3)

### Dodatkowe ulepszenia do zaimplementowania:
1. Walidacja LEI: `^[A-Z0-9]{20}$`
2. Walidacja kodów usług: tylko a-j
3. Normalizacja URL-i
4. Deduplikacja passport countries

## Kolejność implementacji (etapy)

### ETAP 0: Weryfikacja CSV + data dictionary (tydzień 0)
1. Pobrać próbki CSV OTHER/ART/EMT/NCASP
2. Zweryfikować nagłówki i formaty
3. Zaktualizować `registers.py`

### ETAP 0.5: Performance fixes dla obecnego CASP (tydzień 0)
1. Indeksy na polach filtrów
2. Przepisanie `/api/filters/counts` na GROUP BY
3. Frontend debouncing i caching

### ETAP 1: Refactor backendu pod multi-register (tydzień 1-2)
1. Zmiany w modelach i migracja
2. Aktualizacja `schemas.py`
3. Zmiany w API (`register_type`)
4. Testy regresyjne CASP

### ETAP 2: Frontend routing + selector (tydzień 2-3)
1. React Router w `main.jsx`
2. `RegisterSelector`
3. Przekazanie `registerType` do `App.jsx`

### ETAP 3: OTHER (tydzień 3-4)
1. Model + import
2. UI/kolumny
3. Testy

### ETAP 4: ART + EMT (tydzień 4-5)
1. Modele + import
2. Filtry (credit institution, exemptions)
3. UI

### ETAP 5: NCASP (tydzień 5-6)
1. Model + import
2. UI + multiple websites

### ETAP 6: Automatyzacja + deployment (tydzień 6)
1. `update_esma_data.py --all`
2. Automatyczne „Last updated” per rejestr
3. Dokumentacja + deploy

## URL-e CSV (do pobierania dynamicznego)

**Nie polegać na hard-coded datach w URL-ach.**
Skrypt powinien:
1. Scrape’ować stronę ESMA
2. Wyciągać linki per rejestr
3. Fallback do ostatnich znanych URL-i

## Optymalizacje wydajności (skrót)

1. **Indeksy** (Postgres):
   - `(register_type, home_member_state)`
   - `(register_type, authorisation_notification_date)`
   - trigram dla `commercial_name` (wymaga `CREATE EXTENSION pg_trgm`)

2. **/filters/counts**:
   - zastąpić pętle `COUNT` jednym `GROUP BY`

3. **Frontend**:
   - debounce (300ms)
   - batching `Promise.all`
   - cache counts per filtr

## Ryzyka i mitigacje (aktualizacja)

1. **Duplikaty LEI między rejestrami** → indeks per `register_type`
2. **Zmiany w strukturze CSV** → walidacja schematu przed importem
3. **Migracja w SQLite** → przebudowa tabeli, test migracji lokalnie
4. **Wydajność** → indeksy + ograniczenie datasetu per `register_type`

## Metryki sukcesu

1. **Funkcjonalność**:
   - wszystkie 5 rejestrów działają
   - filtry specyficzne per rejestr

2. **Wydajność**:
   - filtrowanie < 300ms
   - counts < 200ms

3. **Jakość kodu**:
   - brak duplikacji
   - testy dla importu + API

## Opcjonalne dodatki po MVP

1. Cross-register search
2. Export CSV/Excel
3. Dashboard statystyk
4. Powiadomienia NCASP
