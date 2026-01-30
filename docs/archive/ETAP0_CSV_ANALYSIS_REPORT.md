# ETAP 0: Raport analizy CSV dla wszystkich rejestrów ESMA MiCA

**Data analizy:** 2026-01-29
**Źródło:** https://www.esma.europa.eu/

## Podsumowanie

| Rejestr | Liczba wierszy | Separator główny | Separator wielowartościowy | Status |
|---------|---------------|------------------|---------------------------|--------|
| CASP    | ~200+ (existing) | comma (,) | pipe (\|) w polach multi-value | ✅ Działający |
| OTHER   | 714           | comma (,) | pipe (\|) w polach multi-value | ✅ Dane dostępne |
| ART     | 1 (tylko header) | comma (,) | pipe (\|) w polach multi-value | ⚠️ Pusty rejestr |
| EMT     | 32            | comma (,) | pipe (\|) w polach multi-value | ✅ Dane dostępne |
| NCASP   | 102           | comma (,) | pipe (\|) w polach multi-value | ✅ Dane dostępne |

## Kluczowe odkrycia

### 1. Separator CSV
- **Wszystkie rejestry**: używają `,` (comma) jako główny separator pól CSV
- **Pola wielowartościowe**: używają `|` (pipe) do rozdzielania wartości w ramach jednego pola
  - CASP: `ac_serviceCode` (np. "a. custody | c. exchange | d. crypto-to-crypto")
  - CASP: `ac_serviceCode_cou` (np. "BE|BG|CY|CZ|DE...")
  - OTHER: `ae_offerCode_cou`, `ae_DTI`
  - EMT: `ae_DTI`
  - NCASP: `ae_website` (multiple websites)
- **Implikacja**: Parser CSV używa standardowego comma-separated, a pipe-separated tylko dla parsowania wartości wielowartościowych

### 2. ART - pusty rejestr
- Rejestr ART zawiera tylko wiersz nagłówków, bez danych
- **Implikacja**: Implementacja ART może zostać odłożona lub zrobiona jako szkielet

### 3. Różnice w strukturze kolumn vs plan

## Szczegółowa analiza per rejestr

---

## OTHER (White Papers) - 714 wierszy

### Kolumny (13 + 4 puste):
```
1.  ae_competentAuthority
2.  ae_homeMemberState
3.  ae_lei_name
4.  ae_lei
5.  ae_lei_cou_code
6.  ae_lei_name_casp
7.  ae_lei_casp
8.  ae_offerCode_cou
9.  ae_DTI_FFG
10. ae_DTI
11. wp_url
12. wp_comments
13. wp_lastupdate
14-17. (puste kolumny)
```

### Mapowanie kolumn:
| CSV Column | Database Field | Typ | Notatki |
|------------|---------------|-----|---------|
| ae_competentAuthority | competent_authority | String | ✅ Zgodne |
| ae_homeMemberState | home_member_state | String(2) | ✅ Zgodne |
| ae_lei_name | lei_name | String | ✅ Zgodne |
| ae_lei | lei | String | ✅ Zgodne |
| ae_lei_cou_code | lei_cou_code | String(2) | ✅ Zgodne |
| ae_lei_name_casp | lei_name_casp | String | ⚠️ Nowa kolumna (nie w planie) |
| ae_lei_casp | lei_casp | String | ✅ Zgodne z planem |
| ae_offerCode_cou | offer_countries | Text | ✅ Zgodne (pipe-separated) |
| ae_DTI_FFG | dti_ffg | Boolean | ✅ Zgodne |
| ae_DTI | dti_codes | Text | ✅ Zgodne (pipe-separated) |
| wp_url | white_paper_url | String | ✅ Zgodne |
| wp_comments | white_paper_comments | Text | ✅ Zgodne |
| wp_lastupdate | white_paper_last_update | Date | ✅ Zgodne |

### ⚠️ Różnice od planu:
1. **Brak `ae_commercial_name`** - OTHER używa tylko `ae_lei_name`
2. **Brak `ae_address`** - nie jest w CSV
3. **Brak `ae_website`** - nie jest w CSV
4. **Brak dat autoryzacji** (`ac_authorisationNotificationDate`, `ac_lastupdate`)
5. **Nowa kolumna**: `ae_lei_name_casp` - nazwa CASP powiązanego z white paper
6. **4 puste kolumny na końcu** - prawdopodobnie błąd w formacie CSV

### Przykładowe dane:
```
Austrian Financial Market Authority (FMA),AT,Skygate Network GmbH,984500BBFE52FE449926,AT,,,,,,
https://www.skygatetoken.at/wp-content/uploads/2025/01/WHITEPAPER-SKYGATE-MiCAR-Version-1-18.01.25-EN-DE.pdf,,
20/01/2025,,,,
```

### Format daty: `DD/MM/YYYY`

---

## ART (Asset-Referenced Tokens) - PUSTY

### Kolumny (16):
```
1.  ae_competentAuthority
2.  ae_homeMemberState
3.  ae_lei_name
4.  ae_lei
5.  ae_lei_cou_code
6.  ae_commercial_name
7.  ae_address
8.  ae_website
9.  ac_authorisationNotificationDate
10. ac_authorisationEndDate
11. ae_credit_institution
12. wp_url
13. wp_authorisationNotificationDate
14. wp_url_cou
15. wp_comments
16. wp_lastupdate
```

### Mapowanie kolumn:
| CSV Column | Database Field | Typ | Notatki |
|------------|---------------|-----|---------|
| ae_competentAuthority | competent_authority | String | ✅ Zgodne |
| ae_homeMemberState | home_member_state | String(2) | ✅ Zgodne |
| ae_lei_name | lei_name | String | ✅ Zgodne |
| ae_lei | lei | String | ✅ Zgodne |
| ae_lei_cou_code | lei_cou_code | String(2) | ✅ Zgodne |
| ae_commercial_name | commercial_name | String | ✅ Zgodne |
| ae_address | address | Text | ✅ Zgodne |
| ae_website | website | String | ✅ Zgodne |
| ac_authorisationNotificationDate | authorisation_notification_date | Date | ✅ Zgodne |
| ac_authorisationEndDate | authorisation_end_date | Date | ⚠️ Nowa kolumna |
| ae_credit_institution | credit_institution | Boolean | ✅ Zgodne z planem |
| wp_url | white_paper_url | String | ✅ Zgodne |
| wp_authorisationNotificationDate | white_paper_notification_date | Date | ✅ Zgodne z planem |
| wp_url_cou | white_paper_offer_countries | Text | ✅ Zgodne z planem |
| wp_comments | white_paper_comments | Text | ✅ Zgodne |
| wp_lastupdate | white_paper_last_update | Date | ✅ Zgodne |

### Status:
- ✅ Struktura zgodna z planem
- ⚠️ **Brak danych** - tylko nagłówki
- ⚠️ Dodatkowa kolumna: `ac_authorisationEndDate` (nie była w planie)

---

## EMT (E-Money Tokens) - 32 wiersze

### Kolumny (19):
```
1.  ae_competentAuthority
2.  ae_homeMemberState
3.  ae_lei_name
4.  ae_lei
5.  ae_lei_cou_code
6.  ae_commercial_name
7.  ae_address
8.  ae_website
9.  ac_authorisationNotificationDate
10. ac_authorisationEndDate
11. ae_exemption48_4
12. ae_exemption48_5
13. ae_authorisation_other_emt
14. ae_DTI_FFG
15. ae_DTI
16. wp_url
17. wp_authorisationNotificationDate
18. wp_comments
19. wp_lastupdate
```

### Mapowanie kolumn:
| CSV Column | Database Field | Typ | Notatki |
|------------|---------------|-----|---------|
| ae_competentAuthority | competent_authority | String | ✅ Zgodne |
| ae_homeMemberState | home_member_state | String(2) | ✅ Zgodne |
| ae_lei_name | lei_name | String | ✅ Zgodne |
| ae_lei | lei | String | ✅ Zgodne |
| ae_lei_cou_code | lei_cou_code | String(2) | ✅ Zgodne |
| ae_commercial_name | commercial_name | String | ✅ Zgodne |
| ae_address | address | Text | ✅ Zgodne |
| ae_website | website | String | ✅ Zgodne |
| ac_authorisationNotificationDate | authorisation_notification_date | Date | ✅ Zgodne |
| ac_authorisationEndDate | authorisation_end_date | Date | ⚠️ Nowa kolumna |
| ae_exemption48_4 | exemption_48_4 | Boolean | ✅ Zgodne z planem (YES/NO) |
| ae_exemption48_5 | exemption_48_5 | Boolean | ✅ Zgodne z planem (YES/NO) |
| ae_authorisation_other_emt | authorisation_other_emt | Text | ✅ Zgodne z planem |
| ae_DTI_FFG | dti_ffg | Boolean | ✅ Zgodne |
| ae_DTI | dti_codes | Text | ✅ Zgodne (pipe-separated) |
| wp_url | white_paper_url | String | ✅ Zgodne |
| wp_authorisationNotificationDate | white_paper_notification_date | Date | ✅ Zgodne z planem |
| wp_comments | white_paper_comments | Text | ✅ Zgodne |
| wp_lastupdate | white_paper_last_update | Date | ✅ Zgodne |

### Przykładowe dane:
```
Czech National Bank (CNB),CZ,Payment Corporation SE,315700IJDQF91J9C8B68,CZ,Stable Labs,
"Krizikova 710/30, Karlin, 18600 Prague 8, Czech Republic",https://stablelabs.co/,26/04/2017,,
YES,YES,Electronic money institution,,,https://stablelabs.co/whitepaper0.pdf,17/05/2025,
"EMT is issued under the limited network exception...",30/10/2025
```

### Status:
- ✅ Struktura w pełni zgodna z planem
- ✅ 32 wiersze danych (mało, ale wystarczające do testów)
- ⚠️ Dodatkowa kolumna: `ac_authorisationEndDate` (nie była w planie)
- ⚠️ Format daty: `DD/MM/YYYY`
- ⚠️ Wartości boolean: `YES`/`NO` (nie `true`/`false`)

---

## NCASP (Non-Compliant) - 102 wiersze

### Kolumny (12):
```
1.  ae_competentAuthority
2.  ae_homeMemberState
3.  ae_lei_name
4.  ae_lei
5.  ae_lei_cou_code
6.  ae_commercial_name
7.  ae_website
8.  ae_infrigment
9.  ae_reason
10. ae_decision_date
11. ae_comments
12. ae_lastupdate
```

### Mapowanie kolumn:
| CSV Column | Database Field | Typ | Notatki |
|------------|---------------|-----|---------|
| ae_competentAuthority | competent_authority | String | ✅ Zgodne |
| ae_homeMemberState | home_member_state | String(2) | ✅ Zgodne |
| ae_lei_name | lei_name | String | ✅ Zgodne |
| ae_lei | lei | String | ⚠️ Często puste! |
| ae_lei_cou_code | lei_cou_code | String(2) | ✅ Zgodne |
| ae_commercial_name | commercial_name | String | ✅ Zgodne |
| ae_website | websites | Text | ✅ Pipe-separated (multiple) |
| ae_infrigment | infringement | String/Boolean | ✅ Zgodne ("No" lub opis) |
| ae_reason | reason | Text | ✅ Zgodne |
| ae_decision_date | decision_date | Date | ✅ Zgodne |
| ae_comments | comments | Text | ⚠️ Inny prefix niż plan |
| ae_lastupdate | last_update | Date | ⚠️ Inny prefix niż plan |

### Przykładowe dane:
```
Commissione Nazionale per le Societa e la Borsa (CONSOB),IT,Dobibo,,,Dobibo,
https://dobibo.com|https://dobibo1.com|https://dobibo2.com,No,None,12/02/2025,,18/02/2025
```

### Kluczowe obserwacje:
1. **Multiple websites**: Rozdzielone `|` (pipe) w jednej kolumnie `ae_website`
2. **LEI często puste**: Wiele wpisów nie ma LEI (podmioty niezgodne mogą nie mieć)
3. **Infringement**: Wartość "No" lub opis naruszenia
4. **Reason**: "None" jeśli brak naruszenia
5. **Brak `ae_address`**: Nie ma adresu w NCASP

### Status:
- ✅ Struktura w większości zgodna z planem
- ⚠️ Prefix `ae_` zamiast `ac_` dla comments/lastupdate
- ⚠️ LEI opcjonalne (nullable)
- ✅ 102 wiersze - dobra ilość danych do implementacji

---

## Wspólne wzorce i różnice

### Wspólne kolumny we wszystkich rejestrach:
```
✅ ae_competentAuthority
✅ ae_homeMemberState
✅ ae_lei_name
✅ ae_lei (ale nullable w NCASP)
✅ ae_lei_cou_code
```

### Różnice w kolumnach "basic info":
| Pole | CASP | OTHER | ART | EMT | NCASP |
|------|------|-------|-----|-----|-------|
| commercial_name | ✅ | ❌ | ✅ | ✅ | ✅ |
| address | ✅ | ❌ | ✅ | ✅ | ❌ |
| website | ✅ | ❌ | ✅ | ✅ | ✅ (multiple) |

### Różnice w kolumnach "dates":
| Pole | CASP | OTHER | ART | EMT | NCASP |
|------|------|-------|-----|-----|-------|
| authorisation_notification_date | ✅ | ❌ | ✅ | ✅ | ❌ |
| authorisation_end_date | ✅ | ❌ | ✅ | ✅ | ❌ |
| last_update | ✅ | ✅ (wp_) | ✅ (wp_) | ✅ (wp_) | ✅ (ae_) |
| decision_date | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## Problemy do rozwiązania

### 1. Format daty
- **CASP**: używa ISO format `YYYY-MM-DD`
- **OTHER/ART/EMT/NCASP**: używają format `DD/MM/YYYY`
- **Rozwiązanie**: Parser musi obsługiwać oba formaty

### 2. Wartości boolean
- **CASP**: `true`/`false`
- **EMT**: `YES`/`NO`
- **NCASP**: `No` lub tekst
- **Rozwiązanie**: Normalizacja do boolean w parserze

### 3. Separator CSV ✅ POPRAWIONE
- **Wszystkie rejestry**: używają comma `,` jako głównego separatora CSV
- **Pipe `|`**: używany tylko w wielowartościowych polach (services, countries, websites)
- **Rozwiązanie**: Standardowy CSV parser z comma, + split("|") dla pól multi-value

### 4. Puste kolumny (OTHER)
- 4 trailing empty columns w OTHER.csv
- **Rozwiązanie**: Strip empty columns podczas parsowania

### 5. LEI nullable
- NCASP często nie ma LEI
- **Rozwiązanie**: Zmienić `lei` na nullable w modelu

### 6. Multiple websites (NCASP)
- Pipe-separated w jednej kolumnie
- **Rozwiązanie**: Parse i store jako Text (pipe-separated) lub separate table

---

## Rekomendacje implementacyjne

### Priorytet implementacji (zaktualizowany):
1. **ETAP 3: OTHER** (714 wierszy - duży, reprezentatywny dataset)
2. **ETAP 4: EMT** (32 wiersze - pełna funkcjonalność, mniejszy)
3. **ETAP 5: NCASP** (102 wiersze - specyficzna logika multiple websites)
4. **ETAP 4: ART** - ODŁOŻYĆ (pusty rejestr - tylko szkielet)

### Kluczowe zmiany w planie:

#### 1. Model Entity (base)
```python
class Entity(Base):
    # ...
    lei = Column(String, nullable=True, index=True)  # ⚠️ Zmiana: nullable dla NCASP
    commercial_name = Column(String, nullable=True)  # ⚠️ Nullable dla OTHER
    address = Column(Text, nullable=True)  # ⚠️ Nullable dla OTHER/NCASP
    website = Column(String, nullable=True)  # ⚠️ Nullable dla OTHER
    authorisation_notification_date = Column(Date, nullable=True)  # ⚠️ Nullable dla OTHER/NCASP
    authorisation_end_date = Column(Date, nullable=True)
    last_update = Column(Date, nullable=True)
    comments = Column(Text, nullable=True)
```

#### 2. OtherEntity
```python
class OtherEntity(Base):
    id = Column(Integer, ForeignKey('entities.id'), primary_key=True)
    lei_name_casp = Column(String, nullable=True)  # ⚠️ Nowe pole
    lei_casp = Column(String, nullable=True)
    offer_countries = Column(Text, nullable=True)  # pipe-separated
    dti_ffg = Column(Boolean, nullable=True)
    dti_codes = Column(Text, nullable=True)  # pipe-separated
    white_paper_url = Column(String, nullable=True)
    white_paper_comments = Column(Text, nullable=True)
    white_paper_last_update = Column(Date, nullable=True)
```

#### 3. ArtEntity & EmtEntity
```python
# Dodać:
authorisation_end_date = Column(Date, nullable=True)  # ⚠️ Nowe pole w obu
```

#### 4. NcaspEntity
```python
class NcaspEntity(Base):
    id = Column(Integer, ForeignKey('entities.id'), primary_key=True)
    websites = Column(Text, nullable=True)  # ⚠️ pipe-separated multiple websites
    infringement = Column(String, nullable=True)
    reason = Column(Text, nullable=True)
    decision_date = Column(Date, nullable=True)
    # comments i last_update są w Entity (base)
```

### 3. CSV Parser - wymagania:
```python
def parse_date(date_str):
    """Parse both DD/MM/YYYY and YYYY-MM-DD formats"""
    formats = ['%d/%m/%Y', '%Y-%m-%d']
    # try both...

def parse_boolean(value):
    """Parse YES/NO, true/false, No, or text"""
    if value.upper() in ['YES', 'TRUE', '1']:
        return True
    elif value.upper() in ['NO', 'FALSE', '0', '']:
        return False
    else:
        return None  # or store as text

def detect_separator(file_path):
    """Auto-detect CSV separator (pipe or comma)"""
    # Check first line...
```

---

## Gotowe do implementacji

### Pliki do utworzenia w ETAP 1:
1. ✅ `backend/app/config/registers.py` - z pełnym mapowaniem kolumn
2. ✅ Zaktualizowane modele w `backend/app/models.py`
3. ✅ Parser CSV z obsługą wielu formatów
4. ✅ Walidacja per rejestr

### Dane testowe:
- ✅ OTHER: 714 wierszy
- ⚠️ ART: Pusty (skip lub mock data)
- ✅ EMT: 32 wiersze
- ✅ NCASP: 102 wiersze

---

## Podsumowanie

✅ **ETAP 0 ZAKOŃCZONY**

**Status implementacji:**
- OTHER: Gotowy do implementacji (duży dataset)
- ART: Pusty - można odłożyć lub zrobić tylko szkielet
- EMT: Gotowy do implementacji
- NCASP: Gotowy do implementacji

**Kluczowe zmiany vs plan:**
1. LEI musi być nullable
2. OTHER nie ma commercial_name, address, website
3. ART/EMT mają dodatkowe pole authorisation_end_date
4. NCASP używa ae_ prefix zamiast ac_ dla comments/lastupdate
5. Multiple date formats do obsługi
6. Multiple boolean formats do normalizacji

**Następny krok:** ETAP 0.5 - Performance fixes dla obecnego CASP
