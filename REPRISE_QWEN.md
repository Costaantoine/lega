# REPRISE PROJET LEGA — Pour Qwen Code
> Généré le : 2026-04-20 ~11h45 UTC

---

## INFRASTRUCTURE

- **VPS principal** : 76.13.141.221 (Ubuntu 24.04, 16 Go RAM — 11 Go utilisés, swap 1.7/2Go)
- **Second VPS** : root@72.62.25.52 (rôle non défini, à clarifier avec Antoine)
- **GitHub repo Bureau IA** : https://github.com/Costaantoine/lega
- **GitHub repo Vitrine** : https://github.com/Costaantoine/lega-vitrine
- **Token GitHub** : dans `~/.git-credentials` sur le VPS
- **Modèles Ollama** : gemma4:e2b (7.2 GB, modèle principal), gemma2:2b (1.6 GB, parser), gemma4:e4b (9.6 GB, inutilisé), moondream (1.7 GB, vision)

---

## ACCÈS COMPLETS

| Service | URL | Credentials |
|---------|-----|-------------|
| Dashboard admin | http://76.13.141.221:3000 | admin / Lega2026! |
| Interface client (Shop) | http://76.13.141.221:3001 | Public |
| API Bureau IA | http://76.13.141.221:8002/docs | JWT (admin) |
| Site Vitrine | http://76.13.141.221:3002 | Public |
| API Vitrine | http://76.13.141.221:8003/docs | Public |
| SearXNG | http://76.13.141.221:8888 | Interne |
| Coolify | http://76.13.141.221:8000 | Admin |
| n8n | http://76.13.141.221:32768 | Workflows |
| Telegram bot | @Legaadmin_bot | Chat ID: 8070870984 |
| DB PostgreSQL | bvi-db-1:5432 | bvi_user / BviSecure2026! |

---

## ÉTAT DES CONTAINERS (2026-04-20 ~11h30 UTC)

| Container | Status | Ports |
|-----------|--------|-------|
| bvi-api-1 | Up 22 min (rebuild session 15) | 8002→8000 |
| bvi-shop-1 | Up 3 days (hot-reload) | 3001→3000 |
| bvi-dashboard-1 | Up 23h (hot-reload) | 3000→3000 |
| bvi-db-1 | Up 3 days (healthy) | 5432 |
| bvi-searxng-1 | Up 22 min (restart session 15) | 8888→8080 |
| lega-site-lega-backend-1 | Up 24h | 8003→8000 |
| lega-site-lega-frontend-1 | Up 40h (hot-reload) | 3002→3000 |
| coolify-proxy | Up 3 days | 80, 443, 8080 |
| traefik-c9es-traefik-1 | **RESTARTING** (conflit avec coolify-proxy) | — |
| n8n-gieb-n8n-1 | Up 3 days | 32768→5678 |

> ⚠️ traefik-c9es-traefik-1 est en reboot loop — conflit port 80/443 avec coolify-proxy. À désactiver via Coolify UI. N'affecte pas le fonctionnement actuel (coolify-proxy gère SSL).

---

## ÉTAT GIT

### Bureau IA (`/opt/bvi`) — CLEAN ✅
```
9e3f0ce  docs: ETAT_SESSION.md session 15 — fix pipeline max_search
6096f4c  fix: pipeline max_search → search_results → publication vitrine
7a7a566  feat: bouton annonces Max entre chat et catalogue + badge count
4c897fa  feat: panneau annonces trouvées + fix Tony hallucination
810f884  feat: Tony mémoire conversationnelle + multi-action
be5c724  fix: general_chat réponse intelligente avec contexte 13 agents
```

### Vitrine (`/opt/lega-site`) — ⚠️ UNSTAGED (91 lignes page.tsx + 8 fichiers locales)
```
07b7ad9  feat(vitrine): section Documentation — login client + navigateur + viewer
9d10bf6  feat(vitrine+backend): section docs + auth clients + agent lea
ebcfa0b  fix(vitrine): Léa WS reconnect + hero grader image
d792F79  fix: Tony supprimé vitrine, drapeaux, WELCOME court
```
> Les fichiers unstaged : `frontend/app/page.tsx` + tous les locales (fr/pt/en/es/de/it/ru/ar) dans `frontend/locales/` et `frontend/public/locales/`. À committer ou à vérifier avant tout travail sur la vitrine.

---

## ARCHITECTURE FICHIERS

```
/opt/bvi/
├── bvi-api/
│   ├── main.py          ← FastAPI + WebSocket + tous les agents + worker
│   └── web_utils.py     ← SearXNG search_web / search_smart
├── bvi-shop/app/
│   └── page.tsx         ← Interface client port 3001 (Next.js hot-reload)
├── bvi-dashboard/       ← Dashboard admin port 3000 (hot-reload)
├── searxng/settings.yml ← Config SearXNG (bing activé depuis session 15)
└── docker-compose.yml

/opt/lega-site/
├── backend/main.py      ← FastAPI vitrine port 8003
├── frontend/app/
│   └── page.tsx         ← Next.js port 3002 (hot-reload) ⚠️ unstaged
├── frontend/locales/    ← Traductions i18n ⚠️ unstaged
└── docker-compose.yml
```

---

## CE QUI EST TERMINÉ ET FONCTIONNE

### Bureau IA (port 3001 + 8002)
- ✅ Tony routing : classify gemma4:e2b, dispatch vers 13 agents
- ✅ Mémoire conversationnelle : 6 derniers échanges par session, persistée en DB
- ✅ Multi-action "fais les deux" : dispatche les 2 derniers agents en séquence
- ✅ Thinking indicator (●●●) + badge agent pendant traitement
- ✅ Message d'accueil Tony depuis WS backend (3 langues)
- ✅ **Pipeline max_search → search_results → vitrine** (fixé session 15)
- ✅ Sam Comms + gate confirmation avant envoi SMTP
- ✅ Agents premium trial 7 jours (activation_requests)
- ✅ Brief matinal Telegram 7h00 (agenda cron)
- ✅ Onglet "📋 Annonces" avec badge count (rafraîchi toutes 30s + WS push)

### Vitrine (port 3002 + 8003)
- ✅ Catalogue 66 produits (scraped depuis tob.pt + manuels)
- ✅ Pagination : 12 items + "Charger plus" (tout chargé si filtre catégorie actif)
- ✅ 8 langues (fr/pt/en/es/de/it/ru/ar)
- ✅ CMS dynamique (site_config, site_sections, site_translations)
- ✅ Section Documentation : login client + navigateur + viewer PDF + demande DL
- ✅ Léa vitrine (streaming, sans emojis)
- ✅ Scraper tob.pt cron toutes les 24h
- ✅ Gestion produits via site_manager (add/update/status)

---

## LES 13 AGENTS — ÉTAT RÉEL

| Agent | Executor | Statut DB | Notes |
|-------|----------|-----------|-------|
| tony_interface | WS direct (gemma4:e2b) | active | Classify + dispatch + general_chat |
| max_search | run_max_search | active | SearXNG bing + gemma4:e2b + stockage search_results |
| sam_comms | run_sam_comms | active | Emails SMTP + gate confirmation |
| documentation | run_documentation | active | Redirection vers vitrine docs |
| site_manager | run_site_manager | active | CMS produits/config via API 8003 |
| logistique | run_logistique | active | Calcul coûts transport |
| comptable | run_comptable | active | Analyse financière |
| traducteur | run_traducteur | active | Traduction multi-langue |
| demandes_prix | run_demandes_prix | active | Estimation prix machines |
| standardiste (Léa) | run_standardiste_streaming | active | WS streaming, widget vitrine |
| lea_extract | via WS direct | active | Extraction données |
| visa_vision | via WS direct | active | Analyse images (moondream) |
| agenda | cron + Telegram | active | Brief matinal 7h00 |

> ⚠️ `AGENT_EXECUTORS` wired : max_search, sam_comms, documentation, site_manager, standardiste, logistique, comptable, traducteur, demandes_prix. Les agents streaming (lea, visa_vision, vitrine_bot) sont gérés directement dans le WS handler, pas via le worker.

---

## BASE DE DONNÉES — TABLES

| Table | Lignes | Usage |
|-------|--------|-------|
| products | 5 | Produits Bureau IA (4 published + 1 sold) |
| site_products | 66 | Catalogue vitrine |
| search_results | 3 | Annonces max_search (1 pending, 1 published, 1 rejected) |
| users | ~5 | Sessions WS |
| tasks | ~12 | Tâches agents (3 stuck resetées à failed session 15) |
| agent_registry | 13 | Tous active |
| conversation_history | — | Mémoire Tony par user_id |
| activation_requests | — | Demandes accès agents premium |
| user_subscriptions | — | Trials 7 jours |
| site_config | — | CMS clés/valeurs (logo, hero, couleurs) |
| site_sections | — | Sections vitrine (hero, about, etc.) |
| site_translations | — | Traductions dynamiques |
| doc_download_requests | — | Demandes DL documentation |

---

## PIPELINE ANNONCES MAX_SEARCH — ÉTAT COMPLET ✅

**Flux validé session 15 :**
1. User → "trouve pelleteuse" → Tony classify → `max_search` dispatché
2. `create_task()` → task_id UUID en DB avec `user_id` dans payload
3. Worker appelle `run_max_search(payload, lang)`
4. `search_web()` → SearXNG bing → 5-10 résultats
5. LLM gemma4:e2b → réponse structurée avec annonces
6. `_parse_and_store_results()` → gemma2:2b parse JSON → INSERT search_results
7. Fallback : si LLM parse = 0, insère les résultats SearXNG bruts
8. Retourne `result_text + "___SEARCH_COUNT:N___"`
9. Worker strip `___SEARCH_COUNT` → envoi `agent_response` au WS
10. Si count > 0 → Tony notifie "✅ Max a trouvé N annonce(s). Disponibles dans 📋 Annonces."
11. WS `search_results_ready` → frontend refresh panel
12. Bouton "✅ Publier" → `POST /api/search-results/{id}/publish` → INSERT products
13. Bouton "❌ Rejeter" → `POST /api/search-results/{id}/reject` → status=rejected

---

## CE QUI RESTE À FAIRE (par priorité)

### P0 — Bugs actifs
- [ ] **Tony classify error** : `WARNING:main:Tony classify error:` dans les logs (erreur silencieuse, cause inconnue) — surveiller, peut empêcher le dispatch d'agents
- [ ] **Vitrine unstaged** : committer `page.tsx` + 8 locales avant tout travail vitrine
- [ ] **Traefik restarting** : désactiver `traefik-c9es-traefik-1` via Coolify UI (conflit port 443 avec coolify-proxy → SSL lega.pt bloqué)

### P1 — Fonctionnalités manquantes
- [ ] **Dashboard "Demandes docs"** (port 3000) : page pending/approve/reject pour `doc_download_requests`
- [ ] **Léa RAG docs** : brancher `/app/docs` dans `run_lea_streaming()` canal=web (la table RAG a 33 chunks chargés mais Léa ne les utilise pas encore en web)
- [ ] **TTS Léa** : `TTS_ENABLED=false` en env — à activer quand modèle TTS disponible
- [ ] **Tony vitrine (port 3002)** : indicateur visuel thinking comme port 3001

### P2 — Améliorations
- [ ] **Mémoire conversationnelle vitrine** : Léa vitrine n'a pas de mémoire de session (contrairement à Tony)
- [ ] **Second VPS** : confirmer rôle et IP 72.62.25.52 avec Antoine
- [ ] **Brief matinal agenda** : brancher Google Calendar / données réelles (actuellement statique)

---

## COMMANDES OPÉRATIONNELLES

```bash
# Rebuild Bureau IA
cd /opt/bvi && docker compose up -d --build api

# Rebuild Vitrine backend
cd /opt/lega-site && docker compose up -d --build lega-backend

# Logs API en direct
docker logs bvi-api-1 -f --tail 30

# Accès DB
docker exec -it bvi-db-1 psql -U bvi_user -d bvi_db

# Test pipeline search
docker exec bvi-api-1 python3 -c "
import asyncio, sys, uuid
sys.path.insert(0, '/app')
async def t():
    from main import _parse_and_store_results
    import web_utils
    lw = await web_utils.search_web('pelleteuse occasion', max_results=5, lang='fr')
    c = await _parse_and_store_results(str(uuid.uuid4()), 'd2b05893-244b-4546-94c7-95fbfae89772', 'Volvo EC220 18000 euros France', lw, 'fr')
    print(f'Stored: {c}')
asyncio.run(t())"

# Push repos
cd /opt/bvi && git push origin main
cd /opt/lega-site && git push origin main

# SearXNG test
curl -s "http://localhost:8888/search?q=pelleteuse&format=json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('results',[])), 'results')"

# IMPORTANT : après tout rebuild bvi-api
docker network connect bvi_bvi-net bvi-api-1 2>/dev/null || true
```

---

## RAPPELS TECHNIQUES CRITIQUES

- `gemma4:e2b` requiert `"think": False` dans TOUS les appels Ollama (sinon timeout)
- `bvi-shop` et `bvi-dashboard` sont en **hot-reload** : les fichiers `.tsx` sont montés en volume. Pas besoin de rebuild pour les changements frontend, seulement pour les dépendances npm.
- Le worker poll les tasks toutes les **10 secondes** — délai normal entre dispatch et exécution
- `user_id` est toujours présent dans le payload task (créé par `get_or_create_user()` au connect WS)
- `sam_pending` est un dict en **mémoire** (pas DB) — perdu au restart de bvi-api
- Credentials admin JWT : `ADMIN_USER=admin`, `ADMIN_PASS=Lega2026!`
- Réseau Docker interne : `bvi_bvi-net` — tous les containers bvi doivent y être connectés
