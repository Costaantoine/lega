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

# Réseau (si API perd sa connectivité après restart)
docker network connect bvi_bvi-net bvi-api-1

# Logs API
docker logs bvi-api-1 --tail=30

# Accès DB
docker exec bvi-db-1 psql -U bvi_user -d bvi_db
```

## Variables d'environnement clés (.env)

| Variable | Valeur | Description |
|----------|--------|-------------|
| `SITE_MANAGEMENT_MODE` | `manual`\|`agent` | Mode gestion produits |
| `AGENT_API_KEY` | (optionnel) | Clé pour sécuriser /api/agent/manage-site |
| `TELEGRAM_BOT_TOKEN` | configuré | @Legaadmin_bot |
| `TELEGRAM_CHAT_ID` | configuré | Antoine |

## ÉTAT ACTUEL — 2026-04-14

### ✅ Terminé

**Infrastructure**
- Docker Compose : api + db + dashboard + shop
- PostgreSQL 16 : 7 tables (products, sources, agent_registry, users, tasks, user_subscriptions, activation_requests)
- Next.js dashboard (port 3000) et shop PWA (port 3001) en inline styles (pas de Tailwind)

**API (bvi-api/main.py)**
- `GET /api/health` — statut + version + WS actifs
- `GET /api/agents/registry` — 5 agents : tony_interface, max_search, sam_comms, lea_extract, visa_vision
- `GET/PUT /api/agents/{name}/status` — toggle active/maintenance
- `GET /api/tasks`, `GET /api/tasks/{id}` — file de tâches async
- `GET /api/products`, `POST /api/products`, `PUT /api/products/{id}`, `PATCH /api/products/{id}/status`, `DELETE /api/products/{id}` — CRUD produits
- `POST /api/products/{id}/upload` — upload image → `/uploads/`
- `GET /api/sources`, `POST /api/sources/add`, `DELETE /api/sources/{id}` — gestion sources
- `GET /api/monitoring` — RAM, Ollama models/loaded, task stats
- `GET /api/activations`, `POST /api/activations`, `PUT /api/activations/{id}` — trials admin
- `POST /api/agent/manage-site`, `GET /api/agent/manage-site/mode` — mode agent (étape 7)

**Tony + Agents**
- WebSocket `/ws/stream` : classification intent FR/PT/EN → routing agents
- Tony (gemma2:2b) : general_chat réponse directe, agents → ack + tâche async
- Worker async : poll DB toutes les 10s, push résultat via WS
- Max Search (gemma4:e2b) : recherche machines TP + scraping tob.pt
- Sam Comms (gemma4:e2b) : génération emails professionnels

**Étape 5 — Abonnements et upsell**
- `get_or_create_user()` : upsert users à chaque connexion WS
- `check_subscription()` + `activate_trial()` : trial 24h auto pour agents premium
- Message upsell Tony en FR et PT (49€/mois)
- `trial_expiry_cron()` : expiry automatique toutes les heures

**Étape 6 — Notifications Telegram**
- `notify_telegram()` : @Legaadmin_bot → Antoine (chat_id 8070870984)
- Notification à chaque activation trial

**Étape 7 — Mode gestion site par agent**
- `SITE_MANAGEMENT_MODE=agent|manual`
- Actions : create, update, delete, publish, unpublish
- 403 en mode manual, notification Telegram en mode agent

**Étape 8 — Tests finaux**
- ✅ WebSocket FR : general_chat détecté, réponse Tony correcte
- ✅ Multi-langue PT-PT : langue détectée et réponse en portugais
- ✅ Upsell + trial : message upsell → trial DB → délégation agent
- ✅ Workflow produit : draft → published → visible /api/products
- ✅ Upload image : PNG stocké dans /uploads/, référencé en DB
- ✅ RAM stable : +29 Mo sous charge, 84% utilisé (Ollama en mémoire)
- ✅ Fix httpx[http2] : warnings web_utils résolus

### 🔲 À faire (Phase 2)

- [ ] user_subscriptions : gestion trial 24h + upsell contextuel par Tony
- [ ] Notification admin Telegram quand trial demandé (fait) → suivi paiement
- [ ] Prompt upsell dans Tony : vérifier abonnement avant délégation (fait) → upgrade vers abonnement payant
- [ ] Authentification JWT dashboard admin
- [ ] Interface client : afficher statut trial + bouton upgrade
