# ÉTAT SESSION — LEGA/BVI
> Mis à jour automatiquement après chaque étape. En cas de coupure, colle ce fichier et reprends.

---

## 🗓 Dernière mise à jour : 2026-04-16

---

## ✅ FAIT — Session 3 (2026-04-16)

### Vitrine (repo lega-vitrine — /opt/lega-site)
- **Backend CMS complet** (`/opt/lega-site/backend/main.py`) — commit `aab257f`
  - `GET/PUT /api/site/config`, `POST /api/site/config/bulk`
  - `GET/PATCH /api/site/sections/{name}`
  - `GET/PUT /api/site/translations`
  - `GET/POST/PUT/DELETE/PATCH /api/site/products` + upload image par produit
  - `POST /api/site/upload` — logo / hero image → stocké dans /uploads/
  - `POST /api/site/import/tob` — scraper tob.pt **fonctionnel**
    - URL réelle : `https://www.tob.pt/pt/machinery.aspx` (ASP.NET, pas de search par mot-clé)
    - Extraction : brand (h2.post-title), model (post-meta), year (meta-spacer), image (Handler.ashx)
    - 57 annonces disponibles, déduplication par source_url
    - Paramètre `max_items` (défaut 20)
    - **Testé : 10 annonces insérées** (Caterpillar, Case, Komatsu, Bobcat, Manitou...)
  - 16 produits total en DB (dont 10 tob.pt + 6 produits démo)

### Bureau IA (repo lega — /opt/bvi)
- **Section "Site Vitrine" dans dashboard admin** (port 3000) — commit `662980a`
  - `SiteVitrinePage.tsx` câblé dans sidebar (`page.tsx`)
  - 4 tabs : Config, Produits, Sections, Import tob.pt
  - Config : nom, slogans 8 langues, coordonnées, couleurs, stats hero, upload logo/hero
  - Produits : CRUD complet + filtre statut + upload image
  - Sections : toggle actif/désactivé par section
  - Import tob.pt : max_items, déduplication, résultat détaillé

### Déjà fait sessions précédentes (JWT, docs, routing)
- JWT dashboard : `POST /api/auth/login`, middleware, page `/login` — commit `7ac0190`
- Tony routing `documentation_search` — commit `7ac0190`
- Docs RAG : fiches CAT/Volvo/Komatsu, prix marché 2026, réglementation PT — commit `9da2d6f`

---

## 🔄 EN COURS

Rien — toutes les étapes de la session sont terminées.

---

## ⏭ PROCHAINE ÉTAPE

### P1 — Bloqué, nécessite action Antoine
- [ ] **Sam Comms SMTP** : mot de passe app Gmail `escritorio.ai.lega@gmail.com` → `aiosmtplib` dans `web_utils.py`
- [ ] **Second VPS** : confirmer existence et IP

### P2 — Développement immédiat
- [ ] **Vitrine frontend (port 3002)** : vérifier que les produits importés tob.pt apparaissent dans le catalogue
- [ ] **Traductions site** : remplir `site_translations` FR/PT/EN via dashboard CMS
- [ ] **Tony → site_manager** : routing intent `modifier_site` dans Tony pour déclencher `site_manager` agent
- [ ] **Agent site_manager** : intégration dans le WS routing (`/api/site/config` + sections via agent)

### P3 — Infra
- [ ] **Traefik** : `traefik-c9es-traefik-1` en restarting en boucle → désactiver via Coolify UI
  (conflit port 80 avec coolify-proxy, pas urgnt)

---

## 🏗 Architecture cible rappel

| Service | Port | Repo | Container |
|---------|------|------|-----------|
| BVI API (FastAPI) | 8002 | lega | bvi-api-1 |
| Dashboard admin (Next.js) | 3000 | lega | bvi-dashboard-1 |
| Shop PWA (Next.js) | 3001 | lega | bvi-shop-1 |
| Vitrine backend (FastAPI) | 8003 | lega-vitrine | lega-site-lega-backend-1 |
| Vitrine frontend (Next.js) | 3002 | lega-vitrine | lega-site-lega-frontend-1 |
| DB (PostgreSQL 16) | 5432 | — | bvi-db-1 |
| SearXNG | 8888 | — | bvi-searxng-1 |

## ⚠️ Rappels techniques

```bash
# Après rebuild bvi-api → reconnecter au réseau
docker network connect bvi_bvi-net bvi-api-1

# Accès DB
docker exec bvi-db-1 psql -U bvi_user -d bvi_db

# Logs vitrine backend
docker logs lega-site-lega-backend-1 --tail=30

# Rebuild vitrine backend
cd /opt/lega-site && docker compose up -d --build lega-backend

# Push repos
cd /opt/lega-site && git push origin main   # lega-vitrine
cd /opt/bvi && git push origin main          # lega (Bureau IA)
```
