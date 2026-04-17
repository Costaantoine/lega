# ÉTAT SESSION — LEGA/BVI
> Mis à jour automatiquement après chaque étape. En cas de coupure, colle ce fichier et reprends.

---

## 🗓 Dernière mise à jour : 2026-04-17 (~10h30 UTC)

---

## ✅ FAIT — Session 7 (2026-04-17)

### 1. Cron scraper tob.pt — commit 440b9d6 (lega-vitrine)
- **`_scrape_tob_once()`** : fonction partagée cron + endpoint manuel
- **`tob_scraper_cron()`** : boucle asyncio, lance au démarrage, intervalle configurable `TOB_SCRAPE_INTERVAL_H` (défaut 24h)
- **`POST /api/site/scraper/run`** : déclenchement immédiat sans attendre le cron
- **`POST /api/site/import/tob`** : délègue désormais à `_scrape_tob_once` (code dédupliqué)
- Test au démarrage : 7 nouveaux produits détectés ✅

### 2. TTS streaming Léa — commit 087e7dc (lega/bvi)
- **`run_standardiste_streaming()`** : streaming gemma4:e2b → phrases → edge-tts, même architecture que vitrine_bot
- **WS routing** : `preferred_agent=standardiste` → streaming (était plain `agent_response`)
- **bvi-shop/page.tsx** : gère `text_chunk` sur panel standardiste + `Msg.streaming` dans le type
- Testé : FR 4 text_chunks + 4 audio_chunks ✅, PT 4 text_chunks + 4 audio_chunks ✅
- Vitrine port 3002 : envoie `preferred_agent=vitrine_bot` → déjà streaming + TTS ✅

### 3. CMS vitrine — commits 553e28e (lega-vitrine) + 40874b7 (lega/bvi)
- **Couleurs dynamiques** : `C1`/`C2` lus depuis `cfg[color_primary/color_secondary]` au runtime
  - Modification couleur dans dashboard → appliquée immédiatement au rechargement vitrine
- **Dashboard tab Import** : bloc cron actif (badge vert) + bouton "Lancer un scrape maintenant"

### 4. NL et ZH sur vitrine — commit 5abd7e2 (lega-vitrine)
- **LANGS étendu à 10** : +nl (Néerlandais) +zh (Chinois simplifié)
- 42 clés chacune en DB (vérifiées: `nav_home=Home/首页`)
- Sélecteur navbar vitrine affiche NL et ZH

---

## ✅ FAIT — Session 6 (2026-04-17) — commits fbd3275 + 84eb724

### Vitrine port 3002 — commit fbd3275 (lega-vitrine)
- **Bug Standardiste** : corrigé pour appeler `LEGA_SITE_API/products?status=available` (56 produits)
- **Logo navbar** : `<img src={cfg["logo_url"]}>` configurable depuis site_config
- **LEGA Trading → LEGA.PT** : navbar, hero h1 fallback, footer, layout metadata
- **Message d'accueil** : multilingue sans emojis (8 langues)
- **Strip emojis** : sur toutes les réponses agent

### Shop port 3001 — commit 84eb724 (lega/bvi)
- **Tony → Léa** : welcome FR/PT, uploadDesc, analyzeBtn, hint upload, bouton catalogue
- **Strip emojis** : sur les réponses agent dans le WS handler

---

## ✅ FAIT — Session 5 (2026-04-16)

### Sam Comms SMTP — commit 9b5c7b7
- SMTP configuré : `escritorio.ai.lega@gmail.com` via Gmail app password
- Test validé depuis le container → email reçu ✅

### Bureau IA — commit c3726f3
- NL/ZH traductions : 42 clés × 2 langues insérées en DB
- SiteVitrinePage : LANGS étendu à 9 langues
- Notif Telegram : testée et confirmée ✅

---

## 🔄 EN COURS

Rien — tout est commité et poussé.

---

## ⏭ PROCHAINES ÉTAPES

### P1 — Bloqué, nécessite action Antoine
- [ ] **Second VPS** : confirmer existence et IP pour déploiement client

### P2 — Développement immédiat
- [ ] **site_manager langues** : étendre les actions site_manager pour supporter nl/zh
- [ ] **Enrichir docs/** : fiches constructeurs (CAT, Volvo, Komatsu), prix marché 2026, réglementation Portugal
- [ ] **Scraper auto pages multiples** : tob.pt a plusieurs pages — scraper page 2, 3...

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

# IMPORTANT : gemma4:e2b nécessite "think": False dans tous les appels Ollama
# Sans ça : content="" → tous les agents retournent erreur/vide

# Déclencher scrape tob.pt immédiat
curl -X POST http://76.13.141.221:8003/api/site/scraper/run

# Tester TTS standardiste
# (voir script test WS dans session 7)
```
