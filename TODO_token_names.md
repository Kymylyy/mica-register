# TODO: Ekstrakcja nazw tokenów z rejestru OTHER

> Data analizy: 2026-02-10
> Status: Do implementacji

## Problem

Rejestr OTHER (~732 wpisów) zawiera white papery, ale ESMA nie podaje nazwy tokena/kryptoaktywa.
Dostępne pola: `ae_lei_name` (firma), `wp_url` (whitepaper), `ae_DTI_FFG`/`ae_DTI` (kody DTI — tylko ~20% wpisów).

## Strategia: kaskadowa ekstrakcja (od najtańszej)

### Priorytet 1: Parsowanie URL white papera (~61% wpisów, 0 kosztu)

Największe klastry z czytelnym URL:

| Domena | Ilość | Wzorzec URL | Regex |
|---|---|---|---|
| crypto-risk-metrics.com | 77 | `/white-paper-{TOKEN}-ffg-{code}/` | `white-paper-(.+?)-ffg-` |
| lcx.com | 62 | `/{TICKER}-mica-white-paper/` | `/([a-z0-9]+)-mica-white-paper` |
| socios.com | 51 | `/whitepapers/{TICKER}-whitepaper/` | `/whitepapers/([a-z]+)-whitepaper` |
| okx.com | 21 | `/learn/{TOKEN}-white-paper` | `/learn/(.+?)-white-paper` |
| bitstamp.net | 20 | `White-paper-{TOKEN}-FFG-` | `White-paper-(.+?)-FFG-` |
| Inne czytelne | ~100+ | np. `steelcoin.com`, `uxlink.io/docs/micar-whitepaper.pdf` | heurystyka per-domain |

### Priorytet 2: Parsowanie `ae_lei_name` (~10% dodatkowych)

Niektóre nazwy firm zawierają ticker:
- `Planck Network ($PLANCK)` — regex: `\$([A-Z]{2,10})`
- `ZKsync Association` — matching z bazą CoinGecko
- `VeChain Foundation San Marino S.r.l.` — matching z bazą CoinGecko

### Priorytet 3: CoinGecko API — walidacja i wzbogacenie (darmowe)

- Endpoint: `GET https://api.coingecko.com/api/v3/coins/list` → ~16k tokenów (id, name, symbol)
- Endpoint: `GET https://api.coingecko.com/api/v3/search?query={name}` → wyszukiwanie
- Limit: 5-15 req/min (bez klucza), 30 req/min (darmowe konto)
- Strategia: po wyekstrahowaniu kandydatów z URL/nazwy firmy → walidacja przez CoinGecko

### Priorytet 4: Scraping treści white papera (~250 wpisów, fallback)

Dotyczy głównie:
- **Kraken** (99 PDF-ów) — hashed filenames `assets-cms.kraken.com/files/.../f92eda9a...pdf`
- **Google Drive** (14) — konwersja linku: `drive.google.com/file/d/{ID}/view` → `drive.google.com/uc?export=download&id={ID}`
- **Inne nieczytelne** (~150) — strony projektowe, CDN-y

#### Ścieżka A: PDF

```
1. requests.get(url) → pobranie PDF
2. PyMuPDF (fitz) → tekst z pierwszej strony + metadata (/Title, /Subject)
3. Regex cascade:
   - PDF metadata['title']
   - re.search(r'white\s*paper[:\s\-—]+(.+?)[\n\r(]', text, re.I)
   - re.search(r'\$([A-Z]{2,10})', text)
   - Fallback: największy font na stronie 1 (PyMuPDF daje info o fontach)
```

Zależności: `pip install PyMuPDF` (aka `fitz`)

#### Ścieżka B: HTML

```
1. requests.get(url) → HTML
2. BeautifulSoup → <title>, <h1>, <meta og:title>, <meta description>
3. Dla JS-rendered stron (GitBook, React) → Playwright headless
```

Zależności: `pip install beautifulsoup4 playwright`

### Priorytet 5: GLEIF API (uzupełnienie — firma, nie token)

- Endpoint: `GET https://api.gleif.org/api/v1/lei-records/{LEI}` → nazwa firmy, adres, jurysdykcja
- W pełni darmowe, bez klucza, bez limitu
- Nie daje nazwy tokena, ale potwierdza/wzbogaca dane o emitencie

## Rozkład typów URL w rejestrze

| Kategoria | Ilość | % | Uwagi |
|---|---|---|---|
| HTML pages | ~404 | 55% | Docs, GitBook, strony projektowe |
| Bezpośrednie PDF | ~223 | 31% | W tym 99 z Krakena (hashed) |
| Broken/empty/placeholder | ~84 | 11% | Brak URL lub nonsens |
| Google Drive/DocSend | ~19 | 3% | Wymaga konwersji linków |
| Inne (XHTML, GitHub, etc.) | ~20 | 3% | Edge cases |

## Wyzwania techniczne

1. **Kraken (99 PDF)** — hashed filenames, ale prawdopodobnie ustandaryzowany template. Trzeba pobrać kilka i zobaczyć strukturę.
2. **Rate limiting** — `time.sleep(1-2s)` między requestami + retry z backoff
3. **Anti-bot** — ustawić `User-Agent` header jak przeglądarka
4. **JS rendering** — ~12 stron GitBook + inne SPA wymagają Playwright
5. **Google Drive** — konwersja sharing link → direct download
6. **Multilingualność** — część WP po niemiecku/fińsku, ale nazwa tokena prawie zawsze po angielsku

## DTI FFG — odpada jako darmowe źródło

- DTIF registry download wymaga konta (Auth0 login wall)
- DTIF API: od 7,186 EUR/rok (Standard)
- Registry search UI (registry.dtif.org) — JS-rendered, nie do scrapowania
- Jedyna darmowa opcja: Ospree public mapping (~640 tokenów) na docs.ospree.io

## Szacowane pokrycie

| Metoda | Pokrycie | Niezawodność |
|---|---|---|
| URL parsing | ~450/732 (61%) | Wysoka |
| Nazwa firmy + CoinGecko | ~70/732 (10%) | Średnia |
| PDF metadata + tytuł | ~100/732 (14%) | Średnia |
| HTML title/h1 | ~40/732 (5%) | Średnia |
| Content regex | ~20/732 (3%) | Niska |
| **Łącznie** | **~680/732 (93%)** | — |
| Manualna weryfikacja | ~52/732 (7%) | — |

## Następne kroki

- [ ] Proof of concept: URL parser dla top 5 domen (crypto-risk-metrics, lcx, socios, okx, bitstamp)
- [ ] Pobrać 5-10 PDF z Krakena i przeanalizować strukturę (czy jest template?)
- [ ] Pobrać listę tokenów z CoinGecko (`/coins/list`) jako lokalny lookup
- [ ] Zbudować pipeline: URL parse → firm name parse → CoinGecko match → PDF scrape
- [ ] Zdecydować gdzie przechowywać wynik (nowa kolumna w DB? osobna tabela?)
