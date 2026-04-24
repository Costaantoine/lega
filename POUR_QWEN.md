# CONTEXTE PROJET — LEGA / BUREAU VIRTUEL IA
> Fichier de transfert de contexte. Copie-colle ce fichier dans Qwen Code pour reprendre le travail.
> Généré le : 2026-04-24

---

## REBUILD APRÈS MODIFICATION PYTHON
```bash
# Bureau IA
cd /opt/bvi && docker compose up -d --build api

# Vitrine
cd /opt/lega-site && docker compose up -d --build lega-backend

# Frontends Next.js = hot-reload, pas besoin de rebuild
```

---

## LES 13 AGENTS (depuis agent_registry en DB)

| Nom interne     | Nom affiché                   | Modèle           | Statut | Premium |
|-----------------|-------------------------------|------------------|--------|---------|
| agenda          | Agent Agenda                  | gemma2:2b        | active | non     |
| comptable       | Secrétaire Comptable          | gemma4:e2b       | active | oui     |
| demandes_prix   | Agent Demandes de Prix        | gemma4:e2b       | active | oui     |
| documentation   | Agent Documentation Technique | gemma4:e2b       | active | oui     |
| lea             | Léa (standardiste vitrine)    | gemma4:e2b       | active | non     |
| lea_extract     | Extraction Specs              | gemma4:e2b       | active | oui     |
| logistique      | Agent Logistique              | gemma4:e2b       | active | oui     |
| max_search      | Recherche Multi-Sources       | gemma4:e2b       | active | oui     |
| sam_comms       | Communication Email/SMS       | gemma4:e2b       | active | non     |
| site_manager    | Gestionnaire Site Web         | gemma4:e2b       | active | oui     |
| tony_interface  | Interface Conversationnelle   | gemma2:2b        | active | non     |
| traducteur      | Traducteur Multilingue        | gemma4:e2b       | active | oui     |
| visa_vision     | Analyse Photos                | moondream:latest | active | oui     |

---

## TABLES DB (PostgreSQL 16 — bvi_db)

```
activation_requests
agent_registry
conversation_history
doc_download_requests
events
products              ← 5 produits Bureau IA (publiés depuis max_search)
search_results        ← 1 pending actuellement
site_audit_log
site_clients
site_config
site_products
site_sections
site_translations
sources
tasks                 ← 0 tâches running actuellement
team_availability
user_subscriptions
users
```
Total : 18 tables

---

## ENDPOINTS API BUREAU IA (port 8002)

```
GET      /api/activations
POST     /api/activations
PUT      /api/activations/{activation_id}
POST     /api/agenda/brief-now
POST     /api/agent/manage-site
GET      /api/agent/manage-site/mode
GET      /api/agents/registry
GET      /api/agents/{name}/status
PUT      /api/agents/{name}/status
POST     /api/auth/login
GET      /api/auth/me
POST     /api/chat
POST     /api/crew/argus
POST     /api/crew/devis
POST     /api/crew/fiche
POST     /api/crew/veille
GET      /api/health
GET      /api/monitoring
GET      /api/products
POST     /api/products
GET      /api/products/{product_id}
PUT      /api/products/{product_id}
DELETE   /api/products/{product_id}
PATCH    /api/products/{product_id}/status
POST     /api/products/{product_id}/upload
GET      /api/search-results
POST     /api/search-results/{result_id}/publish
POST     /api/search-results/{result_id}/reject
GET      /api/sources
POST     /api/sources/add
DELETE   /api/sources/{source_id}
GET      /api/tasks
GET      /api/tasks/{task_id}
WS       /ws?token=...
```

---

## ENDPOINTS API VITRINE (port 8003)

```
GET      /api/site/audit
POST     /api/site/auth/login
POST     /api/site/auth/register
GET      /api/site/auth/verify
GET      /api/site/config
POST     /api/site/config/bulk
GET      /api/site/config/{key}
PUT      /api/site/config/{key}
POST     /api/site/contact
GET      /api/site/docs
GET      /api/site/docs/content
GET      /api/site/docs/download/{token}
POST     /api/site/docs/request
GET      /api/site/docs/requests
POST     /api/site/docs/requests/{rid}/approve
POST     /api/site/docs/requests/{rid}/reject
GET      /api/site/health
POST     /api/site/import/tob
GET      /api/site/products          ← 66 produits actuellement
POST     /api/site/products
GET      /api/site/products/{product_id}
PUT      /api/site/products/{product_id}
DELETE   /api/site/products/{product_id}
PATCH    /api/site/products/{product_id}/status
POST     /api/site/products/{product_id}/upload
POST     /api/site/scraper/run
GET      /api/site/sections
PATCH    /api/site/sections/{name}
PUT      /api/site/translations
PUT      /api/site/translations/bulk
GET      /api/site/translations/{lang}
POST     /api/site/upload
```

---

## FONCTIONNALITÉS — CE QUI MARCHE À 100%

- Tony routing deux temps : gemma2:2b (ack <2s) + gemma4:e2b (traitement async)
- Indicateur visuel 3 états dans interface port 3001 (waiting → thinking → done)
- Mémoire conversationnelle Tony par session WS (6 derniers échanges)
- Pipeline max_search → search_results → publication vitrine
- Panneau Annonces dans port 3001 avec bouton Publier/Rejeter
- Site vitrine 8 langues + RTL arabe (port 3002)
- Léa standardiste vitrine (web gemma2 / voice gemma4)
- Sam SMTP configuré (escritorio.ai.lega@gmail.com) — gate confirmation implémenté
- Documentation vitrine (login, viewer PDF, demande DL)
- 66 produits sur la vitrine
- Morning brief Telegram (cron quotidien, pelleteuse + marché)
- Sam gate : draft stocké dans sam_pending → bouton "✉️ Confirmer l'envoi" sur dashboard
- Léa redirect docs : keyword check sans LLM → pointe vers section Documentation vitrine
- Site Manager : product_add / product_update / product_status via API port 8003
- Catalogue vitrine pagination : filtre catégorie = tout charger / sans filtre = 12 + "Charger plus"

---

## CE QUI EST INCOMPLET OU CASSÉ

- Tony classify error silencieux dans les logs (à surveiller — peut bloquer dispatch)
- Léa RAG docs non branché (/app/docs/ présent mais non connecté à run_lea_streaming canal web)
- Catalogue vitrine : 66 annonces en DB mais bug limite d'affichage côté frontend (à vérifier)
- Traefik en reboot loop → SSL lega.pt bloqué (traefik-c9es-traefik-1 Restarting)
- Dashboard "Demandes docs" port 3000 non fait (endpoint GET /api/site/docs/requests existe déjà)
- gemma4:e2b timeout 30s sur classify → surveiller sous charge

---

## TÂCHE EN COURS — REPRENDRE ICI

> Dernière session : Session 15 (2026-04-20)
> Rien en cours — tout est stable. Prochaine tâche = voir P0/P1 ci-dessous.

---

## PROCHAINES TÂCHES PAR PRIORITÉ

P0 — Vérifier test max_search complet (pelleteuse) end-to-end jusqu'à publication vitrine
P1 — Léa RAG docs : brancher /app/docs/ dans run_lea_streaming() canal=web
P1 — Bug catalogue vitrine : vérifier et corriger limit d'affichage dans frontend port 3002
P2 — Dashboard Demandes docs port 3000 (endpoint backend déjà prêt : GET /api/site/docs/requests)
P2 — SSL lega.pt : désactiver traefik-c9es-traefik-1 dans Coolify UI d'abord
P2 — TTS Léa vocal : TTS_ENABLED=false → true (quand SSL résolu)

---

## RÈGLES ABSOLUES — NE JAMAIS VIOLER

1. site_manager : PREMIUM, activation MANUELLE Antoine UNIQUEMENT
   → Jamais de trial automatique, jamais d'action sans admin connecté
2. sam_comms : NE JAMAIS envoyer email sans confirmation Antoine
3. knowledge_base.json : READ ONLY, ne jamais modifier
4. Ollama : UN seul modèle à la fois — pas de gemma4 en parallèle
5. Tony deux temps : gemma2 pour l'ack immédiat, gemma4 pour le fond
6. Frontends hot-reload : ne pas rebuild shop/dashboard/frontend vitrine
7. Toujours tester après modification avant de commit

---

## NOTES TECHNIQUES IMPORTANTES

- Tony classify error → surveiller dans logs, peut bloquer dispatch
- /opt/lega-site unstaged possible → committer avant tout travail vitrine
- Traefik reboot loop → désactiver dans Coolify UI avant SSL
- Ollama swap gemma2↔gemma4 = 5-10s → ne pas paralléliser
- DB réseau Docker : bvi-db (depuis containers) / localhost:5432 (depuis host)
- Logs API : `docker logs bvi-api-1 --tail 50`
- knowledge_base.json = source de données marché, NE PAS TOUCHER
- gemma4:e2b nécessite "think": False dans tous les appels Ollama
- sam_pending = dict en mémoire, perdu au redémarrage API
- Credentials admin : ADMIN_USER=admin, ADMIN_PASS=Lega2026!
- Accès DB : `docker exec bvi-db-1 psql -U bvi_user -d bvi_db -t -c "..."`

---

## FONCTIONS CLÉS DANS /opt/bvi/bvi-api/main.py

```
L63    create_jwt_token()
L71    verify_jwt_token()
L197   notify_telegram()
L212   get_or_create_user()
L228   check_subscription()
L246   activate_trial()
L263   detect_language()
L303   tony_classify()          ← routing principal, gemma4:e2b
L488   tony_quick_ack()         ← ack immédiat, gemma2:2b
L569   _ollama_quick()
L583   _send_enriched_if_better()
L597   handle_general_chat()    ← réponse enrichie gemma4
L633   tony_dispatch()          ← orchestre routing + exécution agents
L815   load_kb()                ← charge knowledge_base.json (READ ONLY)
L826   _parse_and_store_results() ← stocke résultats max_search en DB
L913   run_max_search()         ← SearXNG + LLM + store
L980   _smtp_send()
L994   run_sam_comms()          ← génère draft, stocke sam_pending
L1060  build_rag_index()
L1085  rag_search()
L1104  run_documentation()
L1146  run_logistique()
L1180  run_comptable()
L1210  run_traducteur()
L1243  run_demandes_prix()
L1285  run_standardiste()
L1350  run_standardiste_streaming()
L1466  text_to_speech_edge()
L1489  run_vitrine_bot_streaming()
L1613  run_lea_streaming()      ← canal web (gemma2) ou voice (gemma4)
L1746  run_site_manager()
L1901  db_connect()
L1907  _build_history_str()     ← 6 derniers échanges pour contexte
L1917  _load_conv_history()
L1931  _save_conv_history()
L1947  create_task()
L1963  update_task()
L1988  task_worker()            ← boucle async, traite la queue
L2076  trial_expiry_cron()
L2096  build_morning_brief()
L2226  morning_brief_cron()     ← Telegram quotidien
L2245  startup()
L2311  websocket_endpoint()     ← WS principal port 8002/ws
L2446  chat_rest()
```

---

## ARCHITECTURE CONTENEURS

| Service              | Port | Container                 |
|----------------------|------|---------------------------|
| BVI API (FastAPI)    | 8002 | bvi-api-1                 |
| Dashboard admin      | 3000 | bvi-dashboard-1           |
| Shop PWA (Tony)      | 3001 | bvi-shop-1                |
| Vitrine backend      | 8003 | lega-site-lega-backend-1  |
| Vitrine frontend     | 3002 | lega-site-lega-frontend-1 |
| DB PostgreSQL 16     | 5432 | bvi-db-1                  |
| SearXNG              | 8888 | bvi-searxng-1             |
| Traefik (EN REBOOT)  | —    | traefik-c9es-traefik-1    |

---

## COMMENT FINIR UNE SESSION PROPREMENT

À la fin de chaque session, OBLIGATOIRE :
1. Mettre à jour /opt/bvi/ETAT_SESSION.md
2. Mettre à jour /opt/bvi/POUR_QWEN.md
3. Commit et push Bureau IA :
   `cd /opt/bvi && git add -A && git commit -m "session: [résumé]" && git push`
4. Commit et push Vitrine :
   `cd /opt/lega-site && git add -A && git commit -m "session: [résumé]" && git push`

---FIN FICHIER---
