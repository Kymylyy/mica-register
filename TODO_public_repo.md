# TODO: Przygotowanie repo do upublicznienia na GitHub

> Data analizy: 2026-02-10
> Status: Do zrobienia
> Szacowany czas: 2-3 godziny

## KRYTYCZNE — przed upublicznieniem

- [ ] **Sprawdzić czy `.env` był kiedykolwiek commitowany** — zawiera `DEEPSEEK_API_KEY`. Komenda: `git log --all --full-history -- .env`. Jeśli tak → zrotować klucz NATYCHMIAST (po upublicznieniu boty wyciągną go z historii w sekundy).
- [ ] Usunąć `venv/` z dysku (duplikat `.venv/`)

## Pliki do usunięcia z git tracking

```bash
# Wewnętrzne notatki / plany
git rm migration-plan.md
git rm UPDATE_DATA.md              # duplikuje sekcję w README
git rm TODO_token_names.md         # prywatne TODO
git rm TODO_public_repo.md         # ten plik :)

# Archiwalne docs
git rm -r docs/archive/            # stare plany implementacji
git rm -r docs/testing/            # wewnętrzne notatki testowe
git rm docs/LLM_REMEDIATION_DESIGN.md  # design doc nieistniejącej funkcji

# Duże pliki binarne
git rm docs/MiCA.pdf               # 1.6MB PDF regulacji — nie powinien być w repo

# Generowane artefakty
git rm reports/cleaning/cleaning_report.json

# macOS śmieci (tracked!)
git rm docs/.DS_Store
git rm reports/.DS_Store
```

## Dodać do .gitignore

```
TODO_*.md
*.DS_Store
```

## README — przeredagować

Obecny: ~580 linii, za dużo wewnętrznych detali.

Docelowa struktura dla publicznego repo:
1. **Nagłówek** — 1-2 zdania co to jest + badge (np. "Live Demo")
2. **Screenshot** — jeden screenshot UI
3. **Features** — krótka bulleted lista (max 10 punktów)
4. **Quick Start** — 5 kroków do odpalenia lokalnie
5. **Tech Stack** — lista technologii (FastAPI, React, etc.)
6. **Data Source** — link do ESMA + wyjaśnienie skąd dane
7. **License** — MIT
8. **Contributing** — opcjonalne

Detale (architektura DB, API endpoints, deployment) → przenieść do `docs/` jako osobne pliki.

## Dodać

- [ ] Plik `LICENSE` (MIT)
- [ ] Screenshot aplikacji (zapisać jako `docs/screenshot.png` i osadzić w README)
- [ ] Link do live demo (jeśli jest deployed)

## Git history

138 commitów — historia jest OK, konwencjonalne commity (`feat:`, `fix:`).
Nie trzeba squashować. Jedyny risk: sprawdzić czy sekrety nie wyciekły w historii.

## Opcjonalnie

- [ ] Dodać `.github/README.md` zamiast root README (lepiej wygląda na GitHub)
- [ ] Dodać topics do repo na GitHub (mica, esma, crypto, regulation, fastapi, react)
- [ ] Krótki opis repo na GitHub ("ESMA MiCA Register Browser — all 5 EU crypto registers")
