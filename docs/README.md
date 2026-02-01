# MiCA Register - Dokumentacja

## 📖 Główne Dokumenty (Root)

- [README.md](../README.md) - Główna dokumentacja projektu (setup, architektura, deployment)
- [UPDATE_DATA.md](../UPDATE_DATA.md) - Workflow aktualizacji danych ESMA
- [IMPLEMENTATION_SUMMARY.md](../IMPLEMENTATION_SUMMARY.md) - Podsumowanie implementacji multi-register

## 🔧 Techniczna Dokumentacja (docs/)

- [MiCA.pdf](MiCA.pdf) - Dokument regulacyjny MiCA (Markets in Crypto-Assets)
- [CSV_VALIDATION.md](CSV_VALIDATION.md) - System walidacji CSV
- [CSV_CLEANING.md](CSV_CLEANING.md) - Automatyczne czyszczenie danych
- [LLM_REMEDIATION_DESIGN.md](LLM_REMEDIATION_DESIGN.md) - LLM-based data remediation

## 🧪 Testowanie (docs/testing/)

- [TESTING_SUMMARY.md](testing/TESTING_SUMMARY.md) - Kompleksowy przewodnik testowania
- [TESTING_QUICK_START.md](testing/TESTING_QUICK_START.md) - Szybki start z testami
- [TEST_STATUS.md](testing/TEST_STATUS.md) - Aktualny status pokrycia testami

## 📦 Archiwum (docs/archive/)

Historyczne dokumenty z procesu rozwoju:
- [ETAP0_CSV_ANALYSIS_REPORT.md](archive/ETAP0_CSV_ANALYSIS_REPORT.md) - Początkowa analiza CSV (Etap 0)
- [mica-registerV2_plan.md](archive/mica-registerV2_plan.md) - Plan implementacji V2
- [IMPLEMENTATION_SUMMARY_columns_2026-01-29.md](archive/IMPLEMENTATION_SUMMARY_columns_2026-01-29.md) - Implementacja kolumn (29 Jan 2026)

---

## 🗺️ Mapa Reorganizacji

Poniżej nowe lokalizacje przeniesionych plików (dla odniesienia):

| Stara lokalizacja | Nowa lokalizacja |
|-------------------|------------------|
| `TESTING_SUMMARY.md` | `docs/testing/TESTING_SUMMARY.md` |
| `TESTING_QUICK_START.md` | `docs/testing/TESTING_QUICK_START.md` |
| `TEST_STATUS.md` | `docs/testing/TEST_STATUS.md` |
| `ETAP0_CSV_ANALYSIS_REPORT.md` | `docs/archive/ETAP0_CSV_ANALYSIS_REPORT.md` |
| `mica-registerV2_plan.md` | `docs/archive/mica-registerV2_plan.md` |
| `IMPLEMENTATION_SUMMARY.md` | `docs/archive/IMPLEMENTATION_SUMMARY_columns_2026-01-29.md` |
| `IMPLEMENTATION_SUMMARY_COMPLETE.md` | `IMPLEMENTATION_SUMMARY.md` (główny dokument) |

---

## 📂 Struktura Dokumentacji

```
/
├── README.md                        # Główna dokumentacja
├── UPDATE_DATA.md                   # Workflow aktualizacji
├── IMPLEMENTATION_SUMMARY.md        # Podsumowanie implementacji
└── docs/
    ├── README.md                    # Ten plik - nawigacja
    ├── MiCA.pdf                     # Dokument regulacyjny
    ├── CSV_VALIDATION.md            # Walidacja
    ├── CSV_CLEANING.md              # Czyszczenie
    ├── LLM_REMEDIATION_DESIGN.md    # LLM remediation
    ├── testing/                     # Dokumentacja testów
    │   ├── TESTING_SUMMARY.md
    │   ├── TESTING_QUICK_START.md
    │   └── TEST_STATUS.md
    └── archive/                     # Historyczne dokumenty
        ├── IMPLEMENTATION_SUMMARY_columns_2026-01-29.md
        ├── ETAP0_CSV_ANALYSIS_REPORT.md
        └── mica-registerV2_plan.md
```
