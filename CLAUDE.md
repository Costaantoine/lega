# LEGA/BVI — Claude Code Context

## Architecture

- **API** : `bvi-api/main.py` (FastAPI + asyncpg) — port 8002
- **Dashboard admin** : `bvi-dashboard/` (Next.js) — port 3000
- **Shop client PWA** : `bvi-shop/` (Next.js) — port 3001
- **DB** : `bvi-db-1` (PostgreSQL 16) — service Docker `db`
- **LLM local** : Ollama sur host (`host.docker.internal:11434`)
  - Tony : `gemma2:2b` (~2s)
  - Agents spécialisés : `gemma4:e2b`
  - Visa Vision : `moondream:latest`

## Commandes utiles

```bash
# Rebuild API
docker compose up -d --build api

# ⚠️ OBLIGATOIRE après chaque restart API — bug Docker bvi_bvi-net
docker network connect bvi_bvi-net bvi-api-1

# Logs API
docker logs bvi-api-1 --tail=30

# Accès DB
docker exec bvi-db-1 psql -U bvi_user -d bvi_db

# Push GitHub (token configuré dans l'URL remote)
git push origin main
```

## ⚠️ Problème réseau Docker connu

Après chaque `docker compose restart api` ou rebuild, le container `bvi-api-1`
perd sa connexion au réseau `bvi_bvi-net`. L'API démarre mais ne répond pas sur
`localhost:8002`. Solution systématique :

```bash
docker network connect bvi_bvi-net bvi-api-1
```

## Variables d'environnement clés (.env)

| Variable | Valeur | Description |
|----------|--------|-------------|
| `SITE_MANAGEMENT_MODE` | `manual`\|`agent` | Mode gestion produits |
| `AGENT_API_KEY` | (optionnel) | Clé pour sécuriser /api/agent/manage-site |
| `TELEGRAM_BOT_TOKEN` | configuré | @Legaadmin_bot |
| `TELEGRAM_CHAT_ID` | 8070870984 | Antoine |

## ÉTAT FINAL — 2026-04-14

### ✅ Étape 1 — Infrastructure Docker

- Docker Compose : api + db + dashboard + shop
- PostgreSQL 16 (`bvi-db-1`) : 7 tables (products, sources, agent_registry, users, tasks, user_subscriptions, activation_requests)
- Next.js dashboard (port 3000) et shop PWA (port 3001) en inline styles (pas de Tailwind)

### ✅ Étape 2 — API FastAPI complète

- `GET /api/health` — statut + version + WS actifs
- `GET /api/agents/registry` — 5 agents : tony_interface, max_search, sam_comms, lea_extract, visa_vision
- `GET/PUT /api/agents/{name}/status` — toggle active/maintenance
- `GET /api/tasks`, `GET /api/tasks/{id}` — file de tâches async
- `GET /api/products`, `POST`, `PUT`, `PATCH /status`, `DELETE` — CRUD produits
- `POST /api/products/{id}/upload` — upload image → `/uploads/`
- `GET /api/sources`, `POST /api/sources/add`, `DELETE /api/sources/{id}` — gestion sources
- `GET /api/monitoring` — RAM, Ollama models/loaded, task stats
- `GET /api/activations`, `POST`, `PUT` — trials admin

### ✅ Étape 3 — Tony + Agents IA

- WebSocket `/ws/stream` : classification intent FR/PT/EN → routing agents
- `detect_language()` Python : pré-détection par mots-clés (robuste vs gemma2:2b)
- Tony (gemma2:2b) : general_chat réponse directe, agents → ack immédiat + tâche async
- Worker async : poll DB toutes les 10s, push résultat via WS
- Max Search (gemma4:e2b) : recherche machines TP + scraping tob.pt
- Sam Comms (gemma4:e2b) : génération emails professionnels
- Override intent machine_search si mots-clés machines présents (fallback gemma2:2b)

### ✅ Étape 4 — Dashboard admin + Shop PWA

- Dashboard : sidebar nav, monitoring live, agents, tâches, produits, activations, sources
- Shop PWA : chat Tony WS, catalogue produits, upload photo (capture=environment)
- Tous les composants en inline styles (SourceManager, AddSource corrigés)

### ✅ Étape 5 — Abonnements et upsell

- `get_or_create_user()` : upsert users à chaque connexion WS
- `check_subscription()` + `activate_trial()` : trial 24h auto pour agents premium
- Message upsell Tony en FR, PT et EN (49€/mois)
- `trial_expiry_cron()` : expiry automatique toutes les heures (status → expired)

### ✅ Étape 6 — Notifications Telegram

- `notify_telegram()` : @Legaadmin_bot → Antoine (chat_id 8070870984)
- Notification à chaque activation trial (agent, session, message, renouvellement)

### ✅ Étape 7 — Mode gestion site par agent

- `SITE_MANAGEMENT_MODE=agent|manual` (défaut: manual)
- `POST /api/agent/manage-site` : create/update/delete/publish/unpublish produits
- 403 en mode manual avec message explicite
- Notification Telegram à chaque action agent

### ✅ Étape 8 — Tests finaux + corrections

- ✅ WebSocket FR : pelleteuse → machine_search → trial → délégation max_search
- ✅ WebSocket PT : escavadora → machine_search → upsell PT-PT → délégation
- ✅ WebSocket EN : excavator → machine_search → upsell EN → délégation
- ✅ Workflow produit : draft → published → visible catalogue port 3001
- ✅ Upload image : PNG stocké /uploads/, référencé en DB
- ✅ RAM stable : +29 Mo sous charge, 84% utilisé (Ollama)
- ✅ Fix httpx[http2] : warnings web_utils résolus
- ✅ Multi-langue : detect_language() + override post-Tony + fallback machine_kw

## 🔲 Prochaines étapes (Phase 2)

- [ ] **Amélioration UI dashboard** : graphes monitoring, filtres avancés produits, pagination
- [ ] **Tests utilisateur réels** : session avec PME TP, recueil feedback Tony
- [ ] Authentification JWT dashboard admin (actuellement ouvert)
- [ ] Interface client : afficher statut trial + bouton upgrade abonnement
- [ ] Suivi paiement : lien Stripe/PayPal depuis message upsell
- [ ] Sam Comms : intégration SMTP réelle pour envoi emails
