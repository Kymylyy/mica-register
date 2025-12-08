# TODO

## Ulepszenie procesu aktualizacji danych CSV

### Cel
Zoptymalizować i zautomatyzować proces aktualizacji danych z pliku CSV, szczególnie w zakresie weryfikacji poprawności danych przed importem do bazy danych.

### Obecne problemy
- Duplikaty LEI (np. EUWAX) wymagają ręcznej interwencji
- Wieloliniowe pola (np. website) mogą powodować błędy parsowania
- Brak automatycznej walidacji przed commitem
- Proces aktualizacji wymaga wielu ręcznych kroków

### Proponowane rozwiązania

#### 1. Automatyczna walidacja i czyszczenie CSV
- **Skrypt walidacyjny** - automatyczne wykrywanie i raportowanie problemów:
  - Duplikaty LEI z sugestią połączenia
  - Nieprawidłowe formaty dat (np. `01/12/.2025`)
  - Wieloliniowe pola wymagające naprawy
  - Brakujące wymagane pola
  - Nieprawidłowe kody usług (poza zakresem a-j)
  - Nieprawidłowe kody krajów

#### 2. Automatyczne czyszczenie przed commitem
- **Skrypt `clean_csv.py`** - automatyczne naprawianie znanych problemów:
  - Łączenie duplikatów LEI (używając istniejącej logiki `merge_entities_by_lei`)
  - Naprawianie wieloliniowych pól website (łączenie w jedną linię)
  - Normalizacja formatów dat
  - Naprawianie problemów z encodingiem
  - Generowanie raportu zmian

#### 3. Integracja z workflow
- **Pre-commit hook** (opcjonalnie) - automatyczne uruchamianie walidacji przed commitem
- **Aktualizacja dokumentacji** - dodanie instrukcji użycia skryptów walidacyjnych do `UPDATE_DATA.md`
- **Testy jednostkowe** - weryfikacja poprawności działania skryptów czyszczących

#### 4. Ulepszona obsługa błędów
- **Szczegółowe raporty** - informowanie o wszystkich znalezionych problemach
- **Tryb dry-run** - możliwość sprawdzenia zmian bez modyfikacji pliku
- **Backup automatyczny** - tworzenie kopii zapasowej przed modyfikacją

### Priorytet
**Wysoki** - problemy z duplikatami LEI mogą powodować błędy podczas importu i wymagają ręcznej interwencji, co spowalnia proces aktualizacji.

### Szacowany czas
2-4 godziny (w zależności od zakresu implementacji)

### Powiązane pliki
- `backend/app/import_csv.py` - istniejąca logika importu i łączenia duplikatów
- `UPDATE_DATA.md` - dokumentacja procesu aktualizacji
- `casp-register.csv` - główny plik danych

---

**Uwagi:**
- Funkcja `merge_entities_by_lei()` już istnieje i działa podczas importu, ale lepiej byłoby czyścić CSV przed commitem
- Skrypt powinien być łatwy w użyciu i dawać jasne informacje zwrotne o znalezionych problemach
