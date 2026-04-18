# ÉTAT SESSION — LEGA/BVI
> Mis à jour automatiquement après chaque étape. En cas de coupure, colle ce fichier et reprends.

---

## 🗓 Dernière mise à jour : 2026-04-18 (~19h30 UTC)

---

## ✅ FAIT — Session 8 (2026-04-18)

### 1. Bug Léa corrigé — commit ebcfa0b (lega-vitrine)
- **WebSocket**: `onclose`/`onerror` → `setWs(null)` — reconnect auto si socket mort
- **openChat**: vérifie `ws.readyState === WebSocket.OPEN` avant réutilisation
- **sendChat**: vérifie readyState, sinon tente reconnexion
- Test validé : Léa répond < 5s ✅

### 2. Hero image — commit ebcfa0b (lega-vitrine)
- Remplacé photo générique par grader Unsplash `photo-1747004175907-e64576ba2e22`
- Grader jaune gros plan, chantier routier, contraste fort ✅

### 3. Tables DB créées dans bvi-db-1
- `doc_download_requests` : id, doc_path, client_name/email/company, motif, status, download_token, token_expires_at
- `site_clients` : UUID, email (unique), name, company, password_hash, lang

### 4. Agent Léa unifié — commit b456e62 (lega/bvi)
- `run_lea_streaming()` : canal `web` → gemma2:2b, canal `voice/phone/whatsapp` → gemma4:e2b + TTS
- WS routing : `preferred_agent=lea` + `canal` param
- Aliases backward-compat : `vitrine_bot`→lea/web, `standardiste`→lea/voice
- DB : `standardiste` renommé → `lea`, `vitrine_bot` supprimé
- Test validé : agent=lea, canal=web, model=gemma2:2b ✅

### 5. Backend docs + auth — commit 9d10bf6 (lega-vitrine)
- `GET /api/site/docs` : arborescence /app/docs
- `GET /api/site/docs/content?path=` : contenu MD/PDF
- `POST /api/site/docs/request` : demande DL + Telegram + email client
- `GET /api/site/docs/requests` + approve/reject + download/{token}
- `POST /api/site/auth/register|login|verify` : JWT clients vitrine
- docker-compose : volume /opt/bvi/docs + vars SMTP/Telegram/JWT

### 6. Section Documentation vitrine — commit 07b7ad9 (lega-vitrine)
- Navbar : onglet Documentation + indicateur session + déconnexion
- Login modal : login + register inline
- Section docs : DocTree arborescence + visionneuse MD/PDF
- Modal demande téléchargement : formulaire pré-rempli + workflow
- Bannière docs pour visiteurs non connectés

---

## 🔄 EN COURS

Rien — tout est commité.

---

## ⏭ PROCHAINES ÉTAPES

### P1 — Développement immédiat
- [ ] **Dashboard admin port 3000** : page "Demandes docs" — liste pending, boutons Approuver/Refuser (appelle `/api/site/docs/requests/{id}/approve|reject`)
- [ ] **Léa accède au RAG docs** : dans `run_lea_streaming()`, quand canal=web, ajouter recherche RAG `/app/docs` si question technique
- [ ] **Drapeaux 10 langues** : déjà en place (🇵🇹🇫🇷🇬🇧🇪🇸🇩🇪🇮🇹🇳🇱🇨🇳🇷🇺🇸🇦) ✅

### P2 — Enrichir docs
- [ ] Fiches PDF constructeurs (CAT, Volvo, Komatsu) dans /opt/bvi/docs/machines/
- [ ] Prix marché 2026 enrichi
- [ ] Réglementation transport Portugal

### P3 — Infra
- [ ] **Second VPS** : confirmer existence et IP (Antoine)
- [ ] **Traefik** : désactiver traefik-c9es-traefik-1 via Coolify UI

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

# Logs
docker logs bvi-api-1 --tail=30
docker logs lega-site-lega-backend-1 --tail=30

# IMPORTANT : gemma4:e2b nécessite "think": False dans tous les appels Ollama

# Agent Léa — canal web (gemma2:2b) vs voice (gemma4:e2b)
# preferred_agent: "lea", canal: "web"|"voice"|"phone"|"whatsapp"

# Docs API
curl http://76.13.141.221:8003/api/site/docs
curl "http://76.13.141.221:8003/api/site/docs/content?path=machines/pelleteuse.md"
```
