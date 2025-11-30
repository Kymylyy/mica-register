# Konfiguracja Custom Domain

## Krok 1: Konfiguracja Frontendu w Vercel

### 1.1. Dodaj domenę w Vercel
1. Otwórz Vercel Dashboard → Twój projekt `mica-register`
2. Przejdź do **Settings** → **Domains**
3. Kliknij **Add Domain**
4. Wpisz swoją domenę (np. `micaregister.eu`)
5. Vercel pokaże Ci rekordy DNS do dodania

### 1.2. Vercel pokaże Ci coś takiego:
```
Type: A
Name: @
Value: 76.76.21.21

Type: CNAME
Name: www
Value: cname.vercel-dns.com
```

---

## Krok 2: Konfiguracja DNS w OVH

### 2.1. Zaloguj się do OVH
1. Otwórz [ovh.com](https://www.ovh.com)
2. Zaloguj się do panelu klienta
3. Przejdź do **Web Cloud** → **Domeny**
4. Kliknij na swoją domenę

### 2.2. Dodaj rekordy DNS
1. Przejdź do zakładki **DNS Zone** lub **Zarządzanie DNS**
2. Dodaj rekordy które pokazał Vercel:

**Rekord A (główna domena):**
- **Type:** A
- **Subdomain:** @ (lub puste, lub główna domena)
- **Target:** IP z Vercel (np. `76.76.21.21`)
- **TTL:** 3600 (lub domyślne)

**Rekord CNAME (www):**
- **Type:** CNAME
- **Subdomain:** www
- **Target:** `cname.vercel-dns.com`
- **TTL:** 3600 (lub domyślne)

### 2.3. Zapisz zmiany
- Kliknij **Zapisz** lub **Confirm**
- Propagacja DNS może zająć kilka minut do 24 godzin (zwykle 5-30 minut)

---

## Krok 3: Weryfikacja w Vercel

1. Wróć do Vercel Dashboard → **Settings** → **Domains**
2. Vercel automatycznie zweryfikuje domenę
3. Status powinien zmienić się na **Valid** (zielony checkmark)
4. Jeśli nie - poczekaj kilka minut i odśwież

---

## Krok 4: Aktualizacja CORS w Railway

Po skonfigurowaniu domeny frontendu:

1. Railway Dashboard → kafelek **mica-register**
2. **Settings** → **Variables**
3. Zaktualizuj `CORS_ORIGINS`:
   - **Stara wartość:** `https://mica-register.vercel.app`
   - **Nowa wartość:** `https://micaregister.eu,https://www.micaregister.eu`
   - (Dodaj obie wersje: z www i bez www)
4. Railway automatycznie zrestartuje service

---

## Krok 5 (Opcjonalne): Subdomain dla Backendu

Jeśli chcesz mieć własny subdomain dla API (np. `api.micaregister.eu`):

### 5.1. W Railway
1. Railway Dashboard → kafelek **mica-register**
2. **Settings** → **Networking**
3. W sekcji **Custom Domain** kliknij **Generate Domain** lub **Add Custom Domain**
4. Railway pokaże Ci rekord DNS do dodania

### 5.2. W OVH
1. Dodaj rekord CNAME:
   - **Type:** CNAME
   - **Subdomain:** api
   - **Target:** URL z Railway (np. `mica-register-production.up.railway.app`)
   - **TTL:** 3600

### 5.3. Aktualizacja Vercel
1. Vercel Dashboard → **Settings** → **Environment Variables**
2. Zaktualizuj `VITE_API_URL`:
   - **Nowa wartość:** `https://api.micaregister.eu`
3. Zrób **Redeploy** (Vercel nie redeployuje automatycznie po zmianie env vars)

---

## Krok 6: Sprawdź czy wszystko działa

1. Otwórz swoją domenę: `https://micaregister.eu`
2. Sprawdź czy frontend się ładuje
3. Sprawdź DevTools → Console (czy nie ma błędów CORS)
4. Sprawdź czy dane się ładują

---

## Troubleshooting

### DNS nie działa po 30 minutach:
- Sprawdź w OVH czy rekordy są poprawnie dodane
- Użyj narzędzia do sprawdzania DNS: [dnschecker.org](https://dnschecker.org)
- Sprawdź czy TTL nie jest za długie

### Vercel pokazuje "Invalid Configuration":
- Sprawdź czy rekordy DNS są poprawnie dodane w OVH
- Poczekaj na propagację DNS (może zająć do 24h, ale zwykle 5-30 min)

### CORS errors po zmianie domeny:
- Sprawdź czy `CORS_ORIGINS` w Railway zawiera nową domenę
- Sprawdź czy Railway service się zrestartował
- Sprawdź czy używasz `https://` (nie `http://`)

### Frontend działa, ale API nie:
- Sprawdź czy `VITE_API_URL` w Vercel jest ustawione
- Zrób redeploy w Vercel po zmianie env vars
- Sprawdź czy backend URL w Railway działa

---

## Przydatne komendy do sprawdzania DNS:

```bash
# Sprawdź rekordy A
dig micaregister.eu A

# Sprawdź rekordy CNAME
dig www.micaregister.eu CNAME

# Sprawdź wszystkie rekordy
dig micaregister.eu ANY
```

---

## Notatki:

- **Propagacja DNS:** Zwykle 5-30 minut, maksymalnie 24 godziny
- **HTTPS:** Vercel automatycznie wystawia certyfikat SSL (Let's Encrypt)
- **WWW redirect:** Vercel automatycznie przekierowuje www na główną domenę (lub odwrotnie - zależy od konfiguracji)
- **Backend:** Możesz zostawić Railway domain lub skonfigurować własny subdomain

