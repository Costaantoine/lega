# ÉTAT SESSION — LEGA/BVI
> Mis à jour automatiquement après chaque étape. En cas de coupure, colle ce fichier et reprends.

---

## 🗓 Dernière mise à jour : 2026-04-16 (~02h UTC)

---

## ✅ FAIT — Session 3 (2026-04-16)

### Vitrine (repo lega-vitrine — /opt/lega-site) — commits aab257f, 4fad640
- **Backend CMS complet** (`backend/main.py`) — tous endpoints /api/site/*
- **Scraper tob.pt fonctionnel** — URL réelle machinery.aspx, 57 annonces, déduplication
- **Traductions DB** — 326 clés × 8 langues en site_translations
- **loadLocale()** lit d'abord la DB (éditable depuis dashboard CMS), fallback fichiers JSON

### Bureau IA (repo lega — /opt/bvi) — commits 662980a, 75d32c1, f30bc2a
- **Section "🌐 Site Vitrine"** dans dashboard sidebar (SiteVitrinePage.tsx câblé)
  - 4 tabs : Config, Produits, Sections, Import tob.pt (max_items)
- **ETAT_SESSION.md** créé (ce fichier)
- **Tony → site_manager routing** (commit f30bc2a)
  - Intent `modifier_site` dans TONY_SYSTEM + exemples
  - Override keywords : slogan, couleur, téléphone, adresse, section, logo…
  - `run_site_manager()` : LLM gemma4:e2b → JSON action → appel /api/site/config/bulk ou /api/site/sections/{name}
  - Notif Telegram après chaque modification
  - WS `?token=JWT` → is_admin=True → site_manager débloqué
  - Non-admin → 🔒 message bloqué
- **AdminChatPage.tsx** dans dashboard — "💬 Chat Admin"
  - Connexion WS avec JWT token, exemples rapides, indicateur admin

### Sessions précédentes (déjà fait)
- JWT dashboard : POST /api/auth/login + page /login — commit 7ac0190
- Tony routing documentation_search — commit 7ac0190
- Docs RAG : CAT/Volvo/Komatsu, prix marché, réglementation PT — commit 9da2d6f
- 16 produits en site_products (10 tob.pt + 6 démo)

---

## 🔄 EN COURS

Rien — tout est commité et poussé.

---

## ⏭ PROCHAINE ÉTAPE

### P1 — Bloqué, nécessite action Antoine
- [ ] **Sam Comms SMTP** : mot de passe app Gmail `escritorio.ai.lega@gmail.com` → aiosmtplib dans web_utils.py
- [ ] **Second VPS** : confirmer existence et IP

### P2 — Développement immédiat (sans Antoine)
- [ ] **Test AdminChatPage** : vérifier que "Change le slogan FR…" modifie bien le site vitrine en live
  - Le WS admin est sur port 8002, token JWT requis en query param
  - run_site_manager appelle lega-site-lega-backend-1:8000 (même réseau bvi_bvi-net ✅)
- [ ] **Onglet Traductions** dans SiteVitrinePage : interface pour éditer site_translations par langue/clé
- [ ] **Import tob.pt full** : lancer import max_items=50 pour remplir le catalogue

### P3 — Infra
- [ ] **Traefik** : traefik-c9es-traefik-1 en restarting → désactiver via Coolify UI

---

## 🏗 Architecture actuelle

| Service | Port | Container | Réseau |
|---------|------|-----------|--------|
| BVI API (FastAPI) | 8002 | bvi-api-1 | bvi_bvi-net |
| Dashboard admin | 3000 | bvi-dashboard-1 | bvi_bvi-net |
| Shop PWA | 3001 | bvi-shop-1 | bvi_bvi-net |
| Vitrine backend | 8003 | lega-site-lega-backend-1 | bvi_bvi-net + lega_net |
| Vitrine frontend | 3002 | lega-site-lega-frontend-1 | lega_net |
| DB PostgreSQL 16 | 5432 | bvi-db-1 | bvi_bvi-net |
| SearXNG | 8888 | bvi-searxng-1 | bvi_bvi-net |

## ⚠️ Rappels techniques

```bash
# Après rebuild bvi-api → reconnecter réseau
docker network connect bvi_bvi-net bvi-api-1

# Rebuild vitrine backend
cd /opt/lega-site && docker compose up -d --build lega-backend

# Push repos
cd /opt/lega-site && git push origin main   # lega-vitrine
cd /opt/bvi && git push origin main          # lega (Bureau IA)

# Accès DB
docker exec bvi-db-1 psql -U bvi_user -d bvi_db

# Logs API
docker logs bvi-api-1 --tail=30
docker logs lega-site-lega-backend-1 --tail=30
```
