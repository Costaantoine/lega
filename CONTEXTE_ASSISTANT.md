# CONTEXTE PROJET LEGA — Assistant IA de développement
> Généré automatiquement depuis le VPS — 2026-04-24
> À coller dans Qwen 3.6 Plus pour reprendre le développement

## RÔLE DE L'ASSISTANT
Tu es l'assistant développeur du projet Bureau IA LEGA.
Antoine te donne des instructions en français.
Tu fournis du code prêt à l'emploi à coller dans Claude Code 
ou Qwen Code sur le VPS. Toujours en français.

## RÉSUMÉ PROJET
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

---
## HISTORIQUE COMPLET DES SESSIONS

# ÉTAT SESSION — LEGA/BVI
> Mis à jour automatiquement après chaque étape. En cas de coupure, colle ce fichier et reprends.

---

## 🗓 Dernière mise à jour : 2026-04-20 (~11h30 UTC)

---

## ✅ FAIT — Session 15 (2026-04-20)

### Fix pipeline max_search → search_results (commit `6096f4c`)

**Problèmes identifiés et corrigés :**
- **SearXNG** : engines par défaut (startpage/mojeek) retournaient 0 résultats → bing activé (`settings.yml`)
- **web_utils.py** : `search_web()` force maintenant `engines=bing,startpage,mojeek`
- **Worker main.py** : ne gérait pas `___SEARCH_COUNT:N___` → strip du marker + notification Tony + `search_results_ready`
- **Tasks stuck** : 3 tasks "running" depuis restart resetées à "failed"

**Tests validés :**
- `search_web('pelleteuse')` → 5 résultats bing ✅
- `_parse_and_store_results()` → 3 annonces stockées en DB ✅
- `GET /api/search-results` → liste les pending ✅
- `POST /api/search-results/{id}/publish` → produit_id=5 créé dans products ✅
- `POST /api/search-results/{id}/reject` → disparaît du panel ✅

**Flux complet après fix :**
1. User demande "trouve pelleteuse" → max_search dispatché
2. max_search appelle search_web (bing) + LLM gemma4:e2b
3. `_parse_and_store_results` stocke les annonces en DB
4. Worker strip `___SEARCH_COUNT:N___` du texte
5. Tony envoie "✅ Max a trouvé N annonce(s). Disponibles dans l'onglet 📋 Annonces."
6. WS `search_results_ready` → frontend refresh panel Annonces
7. Bouton ✅ Publier → POST publish → produit dans vitrine
8. Bouton ❌ Rejeter → POST reject → disparaît

---

## ✅ FAIT — Session 14 (2026-04-20)

### Correction 1 — Fix hallucination Tony

- **Ordre swap** : `create_task()` appelé EN PREMIER, ack envoyé APRÈS avec le task_id réel
- **Ack honnête** : "✅ Demande transmise à max_search [ref: xxxxxxxx]\nRésultat dans environ 2-4 min."
- **user_id dans payload** : inclus pour traçabilité et stockage search_results
- Plus possible pour Tony de "simuler" une action — la tâche existe en DB avant tout message

### Correction 2 — Panneau "Annonces trouvées" (port 3001)

- **Table `search_results`** créée au startup avec colonnes : id, task_id, user_id, title, brand, model, year, price, description, photo_url, source_url, status, created_at
- **`run_max_search`** : appelle `search_web()` (SearXNG) et stocke les résultats en DB via `_store_search_results()`
- **3 nouveaux endpoints API** :
  - `GET /api/search-results` → liste pending/selected
  - `POST /api/search-results/{id}/publish` → crée produit dans `products` + status='published'
  - `POST /api/search-results/{id}/reject` → status='rejected', disparaît du panneau
- **Frontend shop (port 3001)** : onglet "📋 Annonces" ajouté entre Chat et Catalogue
  - Cartes avec photo (ou 🚜 placeholder), titre, marque/modèle/année, prix, description, lien source
  - Bouton "✅ Publier sur la vitrine" (orange) + bouton "❌ Rejeter" (gris)
  - Publication → crée produit local visible sur port 3001 catalogue
  - Jamais de publication automatique — validation manuelle obligatoire

### Commit : `4c897fa` — feat: panneau annonces trouvées + fix Tony hallucination

---

## ✅ FAIT — Session 13 (2026-04-20)

### Mémoire conversationnelle Tony — 6 étapes complètes

- **Étape 1** : `conversation_history` par session WS, chargée depuis DB à la connexion, user message ajouté à chaque échange (ligne 2247)
- **Étape 2** : `_build_history_str(max_turns=6)` → 6 derniers échanges injectés dans `tony_classify` et `handle_general_chat`
- **Étape 3** : `session_context` avec `pending_actions`, `last_agent`, `last_intent`, `user_lang` — mis à jour à chaque dispatch
- **Étape 4** : Multi-action "fais les deux" / "suite" → dispatche les 2 derniers `recent_agents` en séquence si `pending_actions` vide
- **Étape 5** : `no_greet` conditionné sur `if history` → pas de "Bonjour" après le 1er message (dans classify + general_chat)
- **Étape 6** : `_save_conv_history` appelé aussi pour agents spécialisés (après `create_task`) + `conv_hist.append(ack)`

### Commit : `810f884` — feat: Tony mémoire conversationnelle + multi-action

---

## ✅ FAIT — Session 12 (2026-04-19)

### 1. general_chat — réponse intelligente (remplace fallback hardcodé)
- Ancien : message figé "Je peux rechercher des machines TP..." pour toutes les questions
- Nouveau : `handle_general_chat` → appel gemma4:e2b avec `_TONY_ENRICHED_CHAT`
- Prompt : liste des 13 agents, instructions contextuelles, 2-4 phrases naturelles
- Paramètres : 200 tokens, timeout 40s (same model as classify → déjà chaud, +10-15s)
- Système deux-temps gemma2/gemma4 abandonné : swap Ollama gemma4→gemma2 coûte 35-45s
  (plus lent que réponse gemma4 déjà chaud). Architecturalement non viable.
- Frontend : handle `agent_response_enriched` → ajoute au chat principal

### 2. Résultats tests finaux
- "combien d'agents ?" → "treize agents IA, rôles spécialisés comme Lea..." ✅ 24s
- "bonjour comment tu vas" → "Je vais très bien, merci..." ✅ 55s
- "quel temps fait-il ?" → "Je n'ai pas accès aux infos météo, consultez..." ✅ 57s
- "trouve moi une pelleteuse" → max_search dispatché ✅ 30s

### 3. Note performance
- Classify (gemma4:e2b) : 20-35s selon charge Ollama
- general_chat enriched (gemma4:e2b) : +10-25s après classify (même modèle chaud)
- Total general_chat : 30-60s selon charge
- Agents spécialisés (max_search etc.) : classify seul, puis exécution en background

---

## ✅ FAIT — Session 11 (2026-04-19)

### 1. Tony routing confirmé (port 3001)
- `send()` n'envoie jamais `preferred_agent` → Tony reçoit toutes les requêtes du Bureau IA
- Standardiste widget : `preferred_agent: "standardiste"` → Léa uniquement
- Routing vérifié : bonjour → Tony ✅, pelleteuse → max_search ✅, traduction → traducteur ✅

### 2. Message d'accueil Tony depuis WS backend
- `websocket_endpoint` envoie `type="welcome"` dès la connexion (3 langues FR/PT/EN)
- Texte : "Je suis Tony, votre responsable de bureau LEGA. Je coordonne votre équipe d'agents IA."
- Frontend handle `type="welcome"` — met à jour le message d'accueil sans réinitialiser l'historique
- Changement de langue met à jour le welcome si c'est le seul message

### 3. Fix site_manager non-admin
- Ancien : "🔒 La gestion du site est réservée à l'administrateur." (silencieux)
- Nouveau : "🔒 Cette action nécessite les droits administrateur.\nContactez Antoine pour activer la gestion du site."
- Testé : 4.3s, agent=site_manager, message correct ✅

### 4. Indicateur visuel thinking (port 3001)
- `thinkingStatus` : waiting → thinking → done (fade-out 300ms) → idle
- `waiting` déclenché immédiatement sur `send()` : "Tony reçoit votre message..."
- `thinking` : texte du backend + badge agent + animation ●●● (CSS keyframes tonyPulse)
- Style : #f0f2f5 bg, border-radius 12px, font 13px — visible sur fond sombre
- Animation : `.tony-dot` nth-child delays 0 / 0.2s / 0.4s

### 5. Résultats tests
- Test A (bonjour) : welcome Tony ✅, thinking ✅, réponse Tony 28.5s ✅
- Test B (pelleteuse) : thinking "Je consulte le marché...", agent=max_search ✅, trial activé
- Test C (slogan site, non-admin) : thinking ✅, message block explicatif ✅, 4.3s
- Test D (traduction) : thinking ✅, agent=traducteur ✅, trial activé

---

## ✅ FAIT — Session 10 (2026-04-19)

### 1. Agents premium — logistique, comptable, traducteur, demandes_prix
- Ajoutés à `PREMIUM_AGENTS` et `AGENT_EXECUTORS`
- Overrides prioritaires dans `tony_classify` (bloc principal + fallback) — routing correct même avec mots-clés machines dans le message
- Override site_manager ajouté (même mécanisme)

### 2. Catalogue vitrine — pagination intelligente
- Filtre catégorie actif → charge tout (limit=999), pas de "Charger plus"
- Sans filtre (page d'accueil) → 12 items + "Charger plus"
- Bouton traduit dans 8 langues (clé `load_more` ajoutée tous fichiers locales)

### 3. Léa — catalogue count corrigé
- `limit=8` → `limit=100` dans les 4 fonctions Léa
- Total inclus dans le contexte : "CATALOGUE (63 annonces):"

### 4. Sam — gate de confirmation avant envoi SMTP
- Sam génère brouillon → stocke dans `sam_pending` (mémoire) → retourne draft
- Dashboard : bouton "✉️ Confirmer l'envoi" (vert) sur les messages Sam avec destinataire
- Clic → WS fast-path → envoi SMTP réel

### 5. Léa — redirection documentation
- Keyword check instantané (zéro LLM) dans les 3 fonctions Léa
- `_DOC_KW` + `_DOC_REDIRECT` : 5 langues (FR/PT/EN/ES/DE)
- Redirige vers section Documentation du site vitrine

### 6. Site Manager — gestion produits
- Nouvelles actions : `product_add`, `product_update`, `product_status`
- Prompt LLM enrichi avec exemples et schéma produit
- Appels API vers lega-site backend (port 8003)
- Testé : routing ✅, product_add ✅

---

## 🔄 EN COURS

Rien — tout est actif.

---

## ⏭ PROCHAINES ÉTAPES

### P0 — Corrections bugs restants
- [ ] Test B résultats complets (search pelleteuse) : attendu 60-180s, non vérifié jusqu'au bout
- [ ] gemma4:e2b timeout 30s sur classify → surveiller

### P1 — Développement
- [ ] Dashboard admin : page "Demandes docs" (pending/approve/reject)
- [ ] Léa RAG docs : brancher `/app/docs` dans `run_lea_streaming()` canal=web
- [ ] Second VPS : confirmer existence et IP (Antoine)

### P2 — Infra
- [ ] Traefik : désactiver traefik-c9es-traefik-1 via Coolify UI

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

# Rebuild bvi-api
cd /opt/bvi && docker compose up -d --build api

# Push repos
cd /opt/lega-site && git push origin main
cd /opt/bvi && git push origin main

# Accès DB
docker exec bvi-db-1 psql -U bvi_user -d bvi_db

# IMPORTANT : gemma4:e2b nécessite "think": False dans tous les appels Ollama
# Agent Léa — canal web (gemma2:2b) vs voice (gemma4:e2b)
# Credentials admin : ADMIN_USER=admin, ADMIN_PASS=Lega2026!
# sam_pending : dict en mémoire, TTL implicite (redémarre avec l'API)
```

---
## CODE SOURCE — FONCTIONS CLÉS main.py


### tony_classify() — ligne 303
```python
async def tony_classify(message: str, client_lang: str = None, history: list = None) -> dict:
    """Appelle Tony (gemma4:e2b) pour classifier l'intention."""
    forced_lang = detect_language(message, client_lang)
    lang_hint = {
        "pt": "LANGUAGE=Portuguese (PT-PT). All text fields must be in Portuguese.",
        "en": "LANGUAGE=English. All text fields must be in English.",
        "fr": "LANGUAGE=French. All text fields must be in French.",
    }.get(forced_lang, "LANGUAGE=French. All text fields must be in French.")
    history_str = _build_history_str(history or [])
    no_greet = "\nIMPORTANT: L'utilisateur a déjà été accueilli. Ne jamais recommencer par Bonjour dans direct_response." if history else ""
    prompt = f"{TONY_SYSTEM}\n\n{lang_hint}\nForce lang=\"{forced_lang}\" in your JSON.{no_greet}\n\n{history_str}MESSAGE: {message}\n\nJSON:"
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(50.0, connect=5.0)) as client:
            res = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": AGENT_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False, "think": False,
                    "options": {"temperature": 0.1, "num_predict": 256},
                },
            )
            raw = res.json().get("message", {}).get("content", "")
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(raw[start:end])
                # Toujours forcer la langue pré-détectée (Tony peut se tromper)
                result["lang"] = forced_lang
                m_low = message.lower()
                # Overrides prioritaires — agents spécialisés (avant machine_kw)
                _logistique_kw = {"coût transport","combien transport","transport de","transport d",
                                  "livraison de","devis transport","fret","camion plateau","ro-ro",
                                  "bateau ro","acheminer","expédier","convoi","logistique","shipping cost",
                                  "custo transporte","transporte de","enviar máquina"}
                _comptable_kw  = {"génère un devis","générer un devis","faire un devis","créer un devis",
                                  "facture","bon de commande","tva","avoir","relance paiement",
                                  "facturation","invoice","orçamento","fatura","nota fiscal"}
                _demandes_kw   = {"demande de prix","prix fournisseur","tarif fournisseur",
                                  "prix transporteur","pedido de preço","price request",
                                  "precio proveedor","rédige une demande"}
                _traducteur_kw = {"traduis","traduire","traduza","tradução","translation",
                                  "translate","traducir","en portugais","en français","en anglais",
                                  "in portuguese","in french","in english","em português","em francês"}
                if any(w in m_low for w in _logistique_kw):
                    result.update({"intent":"logistique","agent":"logistique","direct_response":None,
                        "estimated_delay":"15s",
                        "ack_message": result.get("ack_message") or {"fr":"Je calcule le transport...","pt":"A calcular o transporte...","en":"Calculating transport..."}.get(forced_lang,"Je calcule...")})
                elif any(w in m_low for w in _comptable_kw):
                    result.update({"intent":"comptable","agent":"comptable","direct_response":None,
                        "estimated_delay":"20s",
                        "ack_message": result.get("ack_message") or {"fr":"Je génère le document...","pt":"A gerar o documento...","en":"Generating document..."}.get(forced_lang,"Je génère...")})
                elif any(w in m_low for w in _demandes_kw):
                    result.update({"intent":"demandes_prix","agent":"demandes_prix","direct_response":None,
                        "estimated_delay":"15s",
                        "ack_message": result.get("ack_message") or {"fr":"Je rédige la demande de prix...","pt":"A redigir o pedido de preço...","en":"Writing price request..."}.get(forced_lang,"Je rédige...")})
                elif any(w in m_low for w in _traducteur_kw):
                    result.update({"intent":"traducteur","agent":"traducteur","direct_response":None,
                        "estimated_delay":"20s",
                        "ack_message": result.get("ack_message") or {"fr":"Je traduis le texte...","pt":"A traduzir o texto...","en":"Translating..."}.get(forced_lang,"Je traduis...")})
                # Override site_manager (avant machine_kw)
                _site_kw = {"ajoute produit","ajouter produit","ajoute une annonce","ajouter annonce",
                            "crée une fiche","créer fiche","nouveau produit","ajouter au catalogue",
                            "modifie le statut","modifier le statut","passe le produit","mettre en vente",
                            "modifie le site","modifier le site","change le slogan","changer slogan",
                            "configure le site","configurer le site","gestion du site","gérer le site",
                            "adicionar produto","atualizar site","mudar slogan","novo produto"}
                if any(w in m_low for w in _site_kw):
                    result.update({"intent":"modifier_site","agent":"site_manager","direct_response":None,
                        "estimated_delay":"10s",
                        "ack_message": result.get("ack_message") or {"fr":"Je modifie le site vitrine...","pt":"A modificar o site...","en":"Updating the site..."}.get(forced_lang,"Je modifie...")})
                # Forcer machine_search si mots-clés machines présents et Tony a raté
                machine_kw = {"escavadora","excavadora","pelleteuse","excavatrice","excavator","grue","crane",
                              "tracteur","tractor","chargeuse","loader","pelle","engin","engins",
                              "machine tp","machines tp","bulldozer","compacteur","tombereau","nacelle",
                              "chariot élévateur","chargeur","niveleuse","compacteur"}
                if result.get("intent") == "general_chat" and any(w in message.lower() for w in machine_kw):
                    ack_by_lang = {
                        "pt": f"A pesquisar...", "en": "Searching...", "fr": "Je recherche..."
                    }
                    result["intent"] = "machine_search"
                    result["agent"] = "max_search"
                    result["ack_message"] = result.get("ack_message") or ack_by_lang[forced_lang]
                    result["estimated_delay"] = "2-4 min"
                    result["direct_response"] = None
                # Override documentation_search si mots-clés doc présents
                doc_kw = {"fiche technique", "ficha técnica", "technical spec", "datasheet",
                          "certificat ce", "certificação", "ce marking", "douane", "alfândega",
                          "customs", "convoi exceptionnel", "transport routier", "poids total",
                          "dimensions machine", "documentation", "guide technique"}
                if result.get("intent") in ("general_chat",) and any(w in message.lower() for w in doc_kw):
                    ack_by_lang = {
                        "pt": "A consultar a documentação técnica...",
                        "en": "Checking technical documentation...",
                        "fr": "Je consulte la documentation technique..."
                    }
                    result["intent"] = "documentation_search"
                    result["agent"] = "documentation"
                    result["ack_message"] = result.get("ack_message") or ack_by_lang[forced_lang]
                    result["estimated_delay"] = "30s"
                    result["direct_response"] = None
                # Override modifier_site si mots-clés gestion site présents
                site_kw = {"slogan", "couleur", "color", "cor", "téléphone", "telefone", "phone",
                           "adresse", "morada", "address", "modifier le site", "atualizar site",
                           "update site", "change le site", "section", "logo", "site vitrine",
                           "stat_", "changer le ", "mets le ", "modifie le "}
                if result.get("intent") in ("general_chat",) and any(w in message.lower() for w in site_kw):
                    ack_by_lang = {
                        "pt": "A modificar o site vitrine...",
                        "en": "Updating the site...",
                        "fr": "Je modifie le site vitrine..."
                    }
                    result["intent"] = "modifier_site"
                    result["agent"] = "site_manager"
                    result["ack_message"] = result.get("ack_message") or ack_by_lang[forced_lang]
                    result["estimated_delay"] = "5s"
                    result["direct_response"] = None
                return result
    except Exception as e:
        logger.warning(f"Tony classify error: {e}")
    # Fallback — agents spécialisés prioritaires, puis machine_search
```

### tony_quick_ack() — ligne 488
```python
def tony_quick_ack(message: str, client_lang: str = None) -> str:
    """Retourne un ack instantané basé sur keywords — zéro LLM."""
    lang = detect_language(message, client_lang)
    m = message.lower()

    machine_kw  = {"prix","price","preço","excavatrice","excavator","escavadora","pelleteuse",
                   "chariot","forklift","empilhador","grue","crane","grua","tracteur","tractor",
                   "bulldozer","compacteur","compactor","chargeuse","loader","tombereau","dumper",
                   "cat ","volvo","doosan","komatsu","liebherr","occasion","used","usado"}
    transport_kw = {"transport","transporter","livrer","livraison","devis","porto","lyon","madrid",
                    "fret","logistic","logistique","convoi","acheminer","deliver","expédier"}
    site_kw      = {"ajoute","ajout","créer produit","modifie","modifier","prix du","statut",
                    "slogan","couleur","logo","adresse","téléphone","site vitrine","site web",
                    "update site","atualizar","adicionar","produto"}
    email_kw     = {"email","mail","courriel","envoie","envoyer","send","enviar","cliente",
                    "client","ferreira","silva","santos","prêt","ready","pronto"}
    docs_kw      = {"manuel","manual","fiche","spec","documentation","certif","douane",
                    "homolog","datasheet","técnica"}

    if any(w in m for w in machine_kw):
        return {"fr":"Je consulte le marché pour vous...",
                "pt":"A consultar o mercado para si...",
                "en":"Searching the market for you..."}.get(lang,"Je consulte le marché...")
    if any(w in m for w in transport_kw):
        return {"fr":"Je prépare votre devis logistique...",
                "pt":"A preparar o seu orçamento logístico...",
                "en":"Preparing your logistics quote..."}.get(lang,"Je prépare votre devis logistique...")
    if any(w in m for w in site_kw):
        return {"fr":"Je prépare la modification du site...",
                "pt":"A preparar a modificação do site...",
                "en":"Preparing the site update..."}.get(lang,"Je prépare la modification du site...")
    if any(w in m for w in email_kw):
        return {"fr":"Je prépare votre communication...",
                "pt":"A preparar a sua comunicação...",
                "en":"Preparing your communication..."}.get(lang,"Je prépare votre communication...")
    if any(w in m for w in docs_kw):
        return {"fr":"Je consulte la documentation technique...",
                "pt":"A consultar a documentação técnica...",
                "en":"Checking technical documentation..."}.get(lang,"Je consulte la documentation...")
    return {"fr":"Je traite votre demande...",
            "pt":"A tratar do seu pedido...",
            "en":"Processing your request..."}.get(lang,"Je traite votre demande...")


# ── General chat — système deux temps ────────────────────────────────────────

_TONY_QUICK_CHAT = """\
Tu es Tony, responsable de bureau LEGA. Tu coordonnes 13 agents IA spécialisés :
max_search, sam_comms, traducteur, visa_vision, comptable, logistique, documentation,
demandes_prix, lea, agenda, lea_extract, site_manager, standardiste.

Réponds en UNE phrase courte et naturelle à cette question : {message}
Langue : {lang}
Ton : professionnel et chaleureux.
Si c'est une question sur tes capacités ou tes agents → réponds précisément avec le bon chiffre ou nom.
Si c'est une salutation → réponds chaleureusement.
Si hors domaine machines TP → redirige poliment vers ton domaine.
Ne jamais répéter un message générique figé."""

_TONY_ENRICHED_CHAT = """\
Tu es Tony, responsable de bureau LEGA. Tu coordonnes 13 agents IA :
- lea : standardiste vitrine clients
- sam_comms : emails et communications B2B
- agenda : planning et brief matinal Telegram 7h00
- max_search : recherche machines TP et prix marché (Premium)
- lea_extract : extraction specs, parsing HTML (Premium)
- visa_vision : analyse photos et OCR (Premium)
- comptable : devis et factures TVA FR/PT (Premium)
- documentation : manuels techniques RAG (Premium)
- traducteur : traduction FR/PT/EN/ES/DE/IT (Premium)
- logistique : coûts transport France-Portugal (Premium)
- demandes_prix : demandes prix fournisseurs (Premium)
- site_manager : gestion site vitrine (Admin uniquement)

Question : {message}
Langue : {lang}
Réponds de façon naturelle, précise et utile en 2-4 phrases.
Si question sur les agents → donne les infos concrètes.
Si hors domaine → redirige poliment."""


async def _ollama_quick(model: str, prompt: str, num_predict: int, timeout: float) -> str:
    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout, connect=5.0)) as client:
        res = await client.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False, "think": False,
                "options": {"temperature": 0.5, "num_predict": num_predict},
            },
        )
        return res.json().get("message", {}).get("content", "").strip()


async def _send_enriched_if_better(ws, message: str, lang: str, quick_text: str, session_id: str):
    try:
        prompt = _TONY_ENRICHED_CHAT.format(message=message, lang=lang)
        enriched = await _ollama_quick(AGENT_MODEL, prompt, 300, 20.0)
        if len(enriched) > len(quick_text) * 1.4 and len(enriched) > 80:
            await ws.send_json({
                "type": "agent_response_enriched",
                "payload": enriched,
                "metadata": {"intent": "general_chat", "lang": lang, "agent": "tony_enriched"},
            })
    except Exception as e:
        logger.debug(f"general_chat enriched skipped [{session_id[:8]}]: {e}")


async def handle_general_chat(
    ws, message: str, lang: str, classification: dict, session_id: str,
    history: list = None, session_context: dict = None,
) -> str:
    _fallback = {
        "fr": "Je coordonne 13 agents IA pour les machines TP. Que puis-je faire pour vous ?",
        "pt": "Coordeno 13 agentes IA para máquinas TP. Em que posso ajudar?",
        "en": "I coordinate 13 AI agents for construction machinery. How can I help?",
        "es": "Coordino 13 agentes IA para maquinaria TP. ¿En qué puedo ayudarle?",
    }
    history_str = _build_history_str(history or [])
    no_greet = "Tu as déjà accueilli l'utilisateur. Ne jamais recommencer par Bonjour ou une formule d'accueil. Va directement au sujet.\n" if history else ""
```

### handle_general_chat() — ligne 597
```python
async def handle_general_chat(
    ws, message: str, lang: str, classification: dict, session_id: str,
    history: list = None, session_context: dict = None,
) -> str:
    _fallback = {
        "fr": "Je coordonne 13 agents IA pour les machines TP. Que puis-je faire pour vous ?",
        "pt": "Coordeno 13 agentes IA para máquinas TP. Em que posso ajudar?",
        "en": "I coordinate 13 AI agents for construction machinery. How can I help?",
        "es": "Coordino 13 agentes IA para maquinaria TP. ¿En qué puedo ayudarle?",
    }
    history_str = _build_history_str(history or [])
    no_greet = "Tu as déjà accueilli l'utilisateur. Ne jamais recommencer par Bonjour ou une formule d'accueil. Va directement au sujet.\n" if history else ""
    prompt = (
        f"{no_greet}{history_str}"
        f"{_TONY_ENRICHED_CHAT.format(message=message, lang=lang)}"
    )
    try:
        response = await _ollama_quick(AGENT_MODEL, prompt, 200, 40.0)
        if not response:
            response = _fallback.get(lang, _fallback["fr"])
    except Exception as e:
        logger.warning(f"general_chat failed [{session_id[:8]}]: {type(e).__name__} {e}")
        response = classification.get("direct_response") or _fallback.get(lang, _fallback["fr"])

    await ws.send_json({
        "type": "agent_response",
        "payload": response,
        "metadata": {"intent": "general_chat", "lang": lang, "agent": "tony_interface"},
    })
    return response


_MULTI_ACTION_KW = {"les deux", "fais les deux", "à la suite", "os dois", "ambos",
                    "et aussi", "et également", "ensuite", "puis ensuite"}


async def tony_dispatch(
    user_msg: str, client_lang: str,
    ws: "WebSocket", session_id: str, user_id: str, is_admin: bool,
    conversation_history: list = None, session_context: dict = None,
) -> None:
    """Classifie + dispatche vers l'agent — exécuté en arrière-plan via create_task."""
    conv_hist = conversation_history if conversation_history is not None else []
    ctx = session_context if session_context is not None else {}

    try:
        # Détecter multi-action trigger
        msg_low = user_msg.lower()
        is_multi_trigger = any(kw in msg_low for kw in _MULTI_ACTION_KW)
        # Si "fais les deux" sans pending_actions, utiliser les 2 derniers agents récents
        if is_multi_trigger and not ctx.get("pending_actions") and len(ctx.get("recent_agents", [])) >= 2:
            ctx["pending_actions"] = list(ctx["recent_agents"])
            ctx["recent_agents"] = []
        if is_multi_trigger and ctx.get("pending_actions"):
            pending = ctx.pop("pending_actions")
            lang = ctx.get("user_lang", "fr")
            info = {"fr": f"Je lance les actions en attente : {', '.join(pending)}.",
                    "pt": f"A executar as ações pendentes: {', '.join(pending)}.",
                    "en": f"Launching pending actions: {', '.join(pending)}."}
            await ws.send_json({"type": "agent_response",
                "payload": info.get(lang, info["fr"]),
                "metadata": {"intent": "multi_action", "lang": lang, "agent": "tony_interface"}})
            for pa in pending:
                ctx["pending_actions"] = []
                await tony_dispatch(user_msg, client_lang, ws, session_id, user_id,
                                    is_admin, conv_hist, {**ctx, "forced_agent": pa})
            return

        classification = await tony_classify(user_msg, client_lang, history=conv_hist)
        intent = classification.get("intent", "general_chat")
        lang   = classification.get("lang", "fr")
        agent  = classification.get("agent")
        ctx["last_intent"] = intent
        ctx["last_agent"] = agent
        ctx["user_lang"] = lang

        if intent == "general_chat" or not agent:
            response_text = await handle_general_chat(
                ws, user_msg, lang, classification, session_id,
                history=conv_hist, session_context=ctx,
            )
            if conv_hist is not None:
                conv_hist.append({"role": "assistant", "content": response_text or ""})
                asyncio.create_task(_save_conv_history(user_id, user_msg, response_text or "", lang))
            return

        latency_map = {"max_search": 180, "sam_comms": 90, "visa_vision": 10, "documentation": 30, "site_manager": 15}
        estimated   = latency_map.get(agent, 120)

        if agent == "site_manager" and not is_admin:
            block_msg = {
                "fr": "🔒 Cette action nécessite les droits administrateur.\nContactez Antoine pour activer la gestion du site.",
                "pt": "🔒 Esta ação requer direitos de administrador.\nContacte Antoine para ativar a gestão do site.",
                "en": "🔒 This action requires administrator rights.\nContact Antoine to activate site management.",
            }
            await ws.send_json({
                "type": "agent_response",
                "payload": block_msg.get(lang, block_msg["fr"]),
                "metadata": {"intent": intent, "lang": lang, "agent": agent, "status": "blocked"},
            })
            return

        if agent in PREMIUM_AGENTS:
            sub_status = await check_subscription(user_id, agent)
            if sub_status not in ("active", "trial"):
                is_renewal = sub_status == "expired"
                await activate_trial(user_id, agent)
                logger.info(f"Trial activé: user {user_id[:8]} → {agent}")
                if lang == "pt":
                    upsell = (
                        f"🎯 O agente <b>{agent}</b> é premium.\n\n"
                        f"✅ Ativei um <b>trial gratuito de 24h</b> para si!\n"
                        f"A processar o seu pedido agora...\n\n"
                        f"💡 Para acesso permanente: <b>49€/mês</b>. Contacte-nos."
                    ) if not is_renewal else (
                        f"🔄 O seu trial anterior expirou.\n"
                        f"✅ Novo trial de 24h ativado! A processar...\n\n"
                        f"💡 Acesso permanente: <b>49€/mês</b>."
                    )
                elif lang == "en":
                    upsell = (
```

### tony_dispatch() — ligne 633
```python
async def tony_dispatch(
    user_msg: str, client_lang: str,
    ws: "WebSocket", session_id: str, user_id: str, is_admin: bool,
    conversation_history: list = None, session_context: dict = None,
) -> None:
    """Classifie + dispatche vers l'agent — exécuté en arrière-plan via create_task."""
    conv_hist = conversation_history if conversation_history is not None else []
    ctx = session_context if session_context is not None else {}

    try:
        # Détecter multi-action trigger
        msg_low = user_msg.lower()
        is_multi_trigger = any(kw in msg_low for kw in _MULTI_ACTION_KW)
        # Si "fais les deux" sans pending_actions, utiliser les 2 derniers agents récents
        if is_multi_trigger and not ctx.get("pending_actions") and len(ctx.get("recent_agents", [])) >= 2:
            ctx["pending_actions"] = list(ctx["recent_agents"])
            ctx["recent_agents"] = []
        if is_multi_trigger and ctx.get("pending_actions"):
            pending = ctx.pop("pending_actions")
            lang = ctx.get("user_lang", "fr")
            info = {"fr": f"Je lance les actions en attente : {', '.join(pending)}.",
                    "pt": f"A executar as ações pendentes: {', '.join(pending)}.",
                    "en": f"Launching pending actions: {', '.join(pending)}."}
            await ws.send_json({"type": "agent_response",
                "payload": info.get(lang, info["fr"]),
                "metadata": {"intent": "multi_action", "lang": lang, "agent": "tony_interface"}})
            for pa in pending:
                ctx["pending_actions"] = []
                await tony_dispatch(user_msg, client_lang, ws, session_id, user_id,
                                    is_admin, conv_hist, {**ctx, "forced_agent": pa})
            return

        classification = await tony_classify(user_msg, client_lang, history=conv_hist)
        intent = classification.get("intent", "general_chat")
        lang   = classification.get("lang", "fr")
        agent  = classification.get("agent")
        ctx["last_intent"] = intent
        ctx["last_agent"] = agent
        ctx["user_lang"] = lang

        if intent == "general_chat" or not agent:
            response_text = await handle_general_chat(
                ws, user_msg, lang, classification, session_id,
                history=conv_hist, session_context=ctx,
            )
            if conv_hist is not None:
                conv_hist.append({"role": "assistant", "content": response_text or ""})
                asyncio.create_task(_save_conv_history(user_id, user_msg, response_text or "", lang))
            return

        latency_map = {"max_search": 180, "sam_comms": 90, "visa_vision": 10, "documentation": 30, "site_manager": 15}
        estimated   = latency_map.get(agent, 120)

        if agent == "site_manager" and not is_admin:
            block_msg = {
                "fr": "🔒 Cette action nécessite les droits administrateur.\nContactez Antoine pour activer la gestion du site.",
                "pt": "🔒 Esta ação requer direitos de administrador.\nContacte Antoine para ativar a gestão do site.",
                "en": "🔒 This action requires administrator rights.\nContact Antoine to activate site management.",
            }
            await ws.send_json({
                "type": "agent_response",
                "payload": block_msg.get(lang, block_msg["fr"]),
                "metadata": {"intent": intent, "lang": lang, "agent": agent, "status": "blocked"},
            })
            return

        if agent in PREMIUM_AGENTS:
            sub_status = await check_subscription(user_id, agent)
            if sub_status not in ("active", "trial"):
                is_renewal = sub_status == "expired"
                await activate_trial(user_id, agent)
                logger.info(f"Trial activé: user {user_id[:8]} → {agent}")
                if lang == "pt":
                    upsell = (
                        f"🎯 O agente <b>{agent}</b> é premium.\n\n"
                        f"✅ Ativei um <b>trial gratuito de 24h</b> para si!\n"
                        f"A processar o seu pedido agora...\n\n"
                        f"💡 Para acesso permanente: <b>49€/mês</b>. Contacte-nos."
                    ) if not is_renewal else (
                        f"🔄 O seu trial anterior expirou.\n"
                        f"✅ Novo trial de 24h ativado! A processar...\n\n"
                        f"💡 Acesso permanente: <b>49€/mês</b>."
                    )
                elif lang == "en":
                    upsell = (
                        f"🎯 The <b>{agent}</b> agent is premium.\n\n"
                        f"✅ I've activated a <b>free 24h trial</b> for you!\n"
                        f"Processing your request now...\n\n"
                        f"💡 Full access: <b>€49/month</b>. Contact us."
                    ) if not is_renewal else (
                        f"🔄 Your previous trial has expired.\n"
                        f"✅ New 24h trial activated! Processing...\n\n"
                        f"💡 Full access: <b>€49/month</b>."
                    )
                else:
                    upsell = (
                        f"🎯 L'agent <b>{agent}</b> est premium.\n\n"
                        f"✅ J'active un <b>trial gratuit 24h</b> pour vous !\n"
                        f"Je traite votre demande maintenant...\n\n"
                        f"💡 Accès permanent : <b>49€/mois</b>. Contactez-nous."
                    ) if not is_renewal else (
                        f"🔄 Votre trial précédent a expiré.\n"
                        f"✅ Nouveau trial 24h activé ! Je traite votre demande...\n\n"
                        f"💡 Accès permanent : <b>49€/mois</b>."
                    )
                await ws.send_json({
                    "type": "agent_response",
                    "payload": upsell,
                    "metadata": {"intent": intent, "lang": lang, "agent": agent, "status": "trial_activated"},
                })
                tg_msg = (
                    f"🆕 <b>Trial activé</b>\n"
                    f"Agent : <code>{agent}</code>\n"
                    f"Session : <code>{session_id[:12]}</code>\n"
                    f"Message : {user_msg[:200]}\n"
                    f"Langue : {lang}\n"
                    f"Renouvellement : {'oui' if is_renewal else 'non'}"
                )
                asyncio.create_task(notify_telegram(tg_msg))
                try:
                    conn_act = await db_connect()
```

### _parse_and_store_results() — ligne 826
```python
async def _parse_and_store_results(task_id: str, user_id: str, llm_response: str, listings_web: list, lang: str) -> int:
    """Parse réponse LLM via gemma2:2b → annonces structurées → search_results. Retourne le count."""
    stored = 0
    parse_prompt = f"""Analyse cette réponse de recherche de machines et extrait TOUTES les annonces mentionnées.
Réponds UNIQUEMENT avec un tableau JSON valide, rien d'autre.
Format exact:
[{{"title":"nom complet","brand":"marque","model":"modèle","year":2016,"price":"15000€","description":"description courte 1-2 phrases","photo_url":null,"source_url":null}}]
Si aucune annonce trouvée: []

Réponse à parser:
{llm_response[:2500]}

JSON:"""
    parsed = []
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=5.0)) as c:
            res = await c.post(f"{OLLAMA_URL}/api/chat", json={
                "model": TONY_MODEL,
                "messages": [{"role": "user", "content": parse_prompt}],
                "stream": False, "think": False,
                "options": {"temperature": 0.1, "num_predict": 700},
            })
            raw = res.json().get("message", {}).get("content", "")
            s, e = raw.find("["), raw.rfind("]") + 1
            if s >= 0 and e > s:
                parsed = json.loads(raw[s:e])
                if not isinstance(parsed, list):
                    parsed = []
    except Exception as ex:
        logger.warning(f"LLM parse search_results failed: {ex}")

    if parsed:
        try:
            conn = await db_connect()
            for a in parsed:
                if not a.get("title"):
                    continue
                year_val = None
                try:
                    year_val = int(a["year"]) if a.get("year") else None
                except Exception:
                    pass
                await conn.execute(
                    """INSERT INTO search_results
                       (task_id, user_id, title, brand, model, year, price, description, photo_url, source_url)
                       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)""",
                    task_id, user_id or "antoine",
                    str(a.get("title") or "")[:255],
                    str(a.get("brand") or "")[:100] or None,
                    str(a.get("model") or "")[:100] or None,
                    year_val,
                    str(a.get("price") or "")[:100] or None,
                    str(a.get("description") or "")[:500] or None,
                    str(a.get("photo_url") or "")[:500] or None,
                    str(a.get("source_url") or "")[:500] or None,
                )
                stored += 1
            await conn.close()
        except Exception as ex:
            logger.warning(f"store parsed annonces failed: {ex}")

    # Fallback: résultats SearXNG bruts si LLM n'a rien parsé
    if stored == 0 and listings_web:
        try:
            conn = await db_connect()
            for item in listings_web[:5]:
                title = (item.get("title") or "")[:255]
                if not title:
                    continue
                await conn.execute(
                    """INSERT INTO search_results
                       (task_id, user_id, title, price, source_url, description)
                       VALUES ($1,$2,$3,$4,$5,$6)""",
                    task_id, user_id or "antoine",
                    title,
                    (item.get("content") or "")[:100] or None,
                    (item.get("url") or "")[:500] or None,
                    (item.get("content") or "")[:500] or None,
                )
                stored += 1
            await conn.close()
        except Exception as ex:
            logger.warning(f"store raw listings fallback failed: {ex}")

    return stored


async def run_max_search(payload: dict, lang: str) -> str:
    """Max Search: recherche machines TP (gemma4:e2b)."""
    query = payload.get("message", "")
    user_id = payload.get("user_id", "")
    task_id = payload.get("task_id", str(uuid.uuid4()))
    context = load_kb()
    lang_instr = "Français." if lang == "fr" else ("Português europeu (PT-PT)." if lang == "pt" else "English.")

    listings = []
    try:
        listings = await web_utils.search_smart(query, max_results=5)
    except Exception:
        pass

    listings_web = []
    try:
        listings_web = await web_utils.search_web(query, max_results=8, lang=lang)
    except Exception:
        pass

    listings_text = "\n".join([f"- {l['title']} | {l.get('price','N/A')}" for l in listings]) if listings else "Aucune annonce directe trouvée."

    prompt = f"""Tu es Max Search, expert en recherche de machines TP pour le marché France→Portugal.
Langue de réponse: {lang_instr}

📚 BASE DE CONNAISSANCES:
{context}

🔍 ANNONCES RÉCENTES (tob.pt):
{listings_text}

🎯 DEMANDE CLIENT: {query}

Génère une réponse structurée:
```

### run_max_search() — ligne 913
```python
async def run_max_search(payload: dict, lang: str) -> str:
    """Max Search: recherche machines TP (gemma4:e2b)."""
    query = payload.get("message", "")
    user_id = payload.get("user_id", "")
    task_id = payload.get("task_id", str(uuid.uuid4()))
    context = load_kb()
    lang_instr = "Français." if lang == "fr" else ("Português europeu (PT-PT)." if lang == "pt" else "English.")

    listings = []
    try:
        listings = await web_utils.search_smart(query, max_results=5)
    except Exception:
        pass

    listings_web = []
    try:
        listings_web = await web_utils.search_web(query, max_results=8, lang=lang)
    except Exception:
        pass

    listings_text = "\n".join([f"- {l['title']} | {l.get('price','N/A')}" for l in listings]) if listings else "Aucune annonce directe trouvée."

    prompt = f"""Tu es Max Search, expert en recherche de machines TP pour le marché France→Portugal.
Langue de réponse: {lang_instr}

📚 BASE DE CONNAISSANCES:
{context}

🔍 ANNONCES RÉCENTES (tob.pt):
{listings_text}

🎯 DEMANDE CLIENT: {query}

Génère une réponse structurée:
🔍 RÉSULTATS TROUVÉS
• Liste des machines correspondantes avec prix estimé
📊 ANALYSE MARCHÉ
• Fourchette de prix constatée, tendances
💡 RECOMMANDATIONS
• Conseils d'achat, transport Portugal, vigilance
🔗 SOURCES À CONSULTER
• 2-3 sources pertinentes du contexte"""

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(180.0, connect=10.0)) as client:
            res = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": AGENT_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False, "think": False,
                    "options": {"temperature": 0.3, "num_predict": 800},
                },
            )
            result_text = res.json().get("message", {}).get("content", "Résultat indisponible.")

        # Parser et stocker les annonces APRÈS la réponse LLM
        if user_id:
            stored_count = await _parse_and_store_results(task_id, user_id, result_text, listings_web, lang)
            if stored_count > 0:
                return f"{result_text}\n___SEARCH_COUNT:{stored_count}___"
        return result_text
    except Exception as e:
        logger.error(f"Max Search error: {e}")
        return f"⚠️ Erreur Max Search: {str(e)[:100]}"


def _smtp_send(to_addr: str, subject: str, body: str) -> None:
    """Envoi synchrone via SMTP (appelé dans un thread executor)."""
    msg = MIMEMultipart("alternative")
    msg["From"] = SMTP_FROM
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
        server.ehlo()
        server.starttls()
        server.login(SMTP_FROM, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM, [to_addr], msg.as_string())


async def run_sam_comms(payload: dict, lang: str) -> str:
    """Sam Comms: génération + envoi d'emails professionnels (gemma4:e2b)."""
    context_msg = payload.get("message", "")
    lang_instr = "Français professionnel." if lang == "fr" else ("Português europeu profissional (PT-PT)." if lang == "pt" else "Professional English.")

    # Extraire adresse destinataire depuis le message
    to_match = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", context_msg)
    to_addr = to_match.group(0) if to_match else None

    prompt = f"""Tu es Sam Comms, expert communication B2B pour PME TP.
Langue: {lang_instr}

DEMANDE: {context_msg}

Génère EXACTEMENT dans ce format:
OBJET: <sujet de l'email en une ligne>
---
<corps du message complet, ton professionnel mais chaleureux, 3-5 paragraphes>
---
ACTIONS: <suivi suggéré, relance, délai>"""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            res = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": AGENT_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False, "think": False,
                    "options": {"temperature": 0.4, "num_predict": 700},
                },
            )
        content = res.json().get("message", {}).get("content", "")
        if not content:
            return "⚠️ Sam Comms: réponse vide du modèle."

        # Parser sujet et corps
        subject = "Email LEGA"
        body = content
        subj_match = re.search(r"OBJET\s*:\s*(.+)", content)
        if subj_match:
```

### run_sam_comms() — ligne 994
```python
async def run_sam_comms(payload: dict, lang: str) -> str:
    """Sam Comms: génération + envoi d'emails professionnels (gemma4:e2b)."""
    context_msg = payload.get("message", "")
    lang_instr = "Français professionnel." if lang == "fr" else ("Português europeu profissional (PT-PT)." if lang == "pt" else "Professional English.")

    # Extraire adresse destinataire depuis le message
    to_match = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", context_msg)
    to_addr = to_match.group(0) if to_match else None

    prompt = f"""Tu es Sam Comms, expert communication B2B pour PME TP.
Langue: {lang_instr}

DEMANDE: {context_msg}

Génère EXACTEMENT dans ce format:
OBJET: <sujet de l'email en une ligne>
---
<corps du message complet, ton professionnel mais chaleureux, 3-5 paragraphes>
---
ACTIONS: <suivi suggéré, relance, délai>"""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            res = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": AGENT_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False, "think": False,
                    "options": {"temperature": 0.4, "num_predict": 700},
                },
            )
        content = res.json().get("message", {}).get("content", "")
        if not content:
            return "⚠️ Sam Comms: réponse vide du modèle."

        # Parser sujet et corps
        subject = "Email LEGA"
        body = content
        subj_match = re.search(r"OBJET\s*:\s*(.+)", content)
        if subj_match:
            subject = subj_match.group(1).strip()
        parts = content.split("---")
        if len(parts) >= 2:
            body = parts[1].strip()

        # Gate de confirmation — toujours retourner un brouillon, ne jamais envoyer automatiquement
        if to_addr:
            draft_id = str(uuid.uuid4())
            sam_pending[draft_id] = {
                "to_addr": to_addr, "subject": subject, "body": body,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            confirm_note = f"\n\n📧 **Destinataire détecté : {to_addr}**\nCliquez sur **Confirmer l'envoi** pour envoyer cet email."
            return content + confirm_note + f"\n___DRAFT_ID:{draft_id}___"
        else:
            return content + "\n\n📋 Aucune adresse détectée — brouillon généré (ajoutez un destinataire pour envoyer)"

    except Exception as e:
        return f"⚠️ Erreur Sam Comms: {str(e)[:100]}"


# ── RAG — indexation docs ────────────────────────────────────────────────────

DOCS_DIR = Path("/app/docs")
_rag_index: list[dict] = []   # [{filename, content, chunk}]

def build_rag_index() -> int:
    """Indexe tous les fichiers .md et .txt du dossier /app/docs (récursif)."""
    global _rag_index
    _rag_index = []
    if not DOCS_DIR.exists():
        return 0
    for f in DOCS_DIR.rglob("*"):
        if f.suffix in (".md", ".txt") and f.is_file():
            try:
                content = f.read_text(encoding="utf-8")
                # Découper en chunks de ~800 caractères avec chevauchement 200
                chunk_size, overlap = 800, 200
                for i in range(0, len(content), chunk_size - overlap):
                    chunk = content[i:i + chunk_size]
                    if len(chunk) > 50:
                        _rag_index.append({
                            "filename": str(f.relative_to(DOCS_DIR)),
                            "chunk": chunk,
                        })
            except Exception as e:
                logger.warning(f"RAG index error {f}: {e}")
    logger.info(f"RAG index: {len(_rag_index)} chunks depuis {DOCS_DIR}")
    return len(_rag_index)


def rag_search(query: str, top_k: int = 4) -> str:
    """Recherche simple par mots-clés dans l'index RAG. Retourne le contexte pertinent."""
    if not _rag_index:
        return ""
    q_words = set(query.lower().split())
    scored = []
    for doc in _rag_index:
        text_lower = doc["chunk"].lower()
        score = sum(1 for w in q_words if w in text_lower)
        if score > 0:
            scored.append((score, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    if not scored:
        return ""
    top = scored[:top_k]
    parts = [f"[{d['filename']}]\n{d['chunk']}" for _, d in top]
    return "\n\n---\n\n".join(parts)


async def run_documentation(payload: dict, lang: str) -> str:
    """Agent Documentation: recherche dans la base RAG /docs/ (gemma4:e2b)."""
    query = payload.get("message", "")
    lang_instr = {"fr": "Français.", "pt": "Português europeu (PT-PT).", "en": "English."}.get(lang, "Français.")
    rag_context = rag_search(query, top_k=4)

    if not rag_context:
        no_doc = {
            "fr": f"Je n'ai pas trouvé de documentation sur '{query}'. Ajoutez des fichiers .md dans /docs/ pour enrichir la base.",
            "pt": f"Não encontrei documentação sobre '{query}'. Adicione ficheiros .md em /docs/ para enriquecer a base.",
            "en": f"No documentation found for '{query}'. Add .md files in /docs/ to enrich the knowledge base.",
```

### run_documentation() — ligne 1104
```python
async def run_documentation(payload: dict, lang: str) -> str:
    """Agent Documentation: recherche dans la base RAG /docs/ (gemma4:e2b)."""
    query = payload.get("message", "")
    lang_instr = {"fr": "Français.", "pt": "Português europeu (PT-PT).", "en": "English."}.get(lang, "Français.")
    rag_context = rag_search(query, top_k=4)

    if not rag_context:
        no_doc = {
            "fr": f"Je n'ai pas trouvé de documentation sur '{query}'. Ajoutez des fichiers .md dans /docs/ pour enrichir la base.",
            "pt": f"Não encontrei documentação sobre '{query}'. Adicione ficheiros .md em /docs/ para enriquecer a base.",
            "en": f"No documentation found for '{query}'. Add .md files in /docs/ to enrich the knowledge base.",
        }
        return no_doc[lang]

    prompt = f"""Tu es l'Agent Documentation de LEGA, expert en machines TP et négoce France-Portugal.
Langue de réponse: {lang_instr}

📚 DOCUMENTATION DISPONIBLE:
{rag_context}

🎯 QUESTION: {query}

Réponds de manière précise et structurée en te basant UNIQUEMENT sur la documentation fournie.
Si l'information n'est pas dans la documentation, dis-le clairement."""

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            res = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": AGENT_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False, "think": False,
                    "options": {"temperature": 0.2, "num_predict": 600},
                },
            )
            return res.json().get("message", {}).get("content", "Résultat indisponible.").strip()
    except Exception as e:
        logger.error(f"Documentation agent error: {e}")
        return f"⚠️ Erreur agent Documentation: {str(e)[:100]}"


async def run_logistique(payload: dict, lang: str) -> str:
    """Agent Logistique: calcul transport engins TP France↔Portugal."""
    query = payload.get("message", "")
    lang_instr = {"fr": "Français.", "pt": "Português europeu (PT-PT).", "en": "English."}.get(lang, "Français.")
    prompt = f"""Tu es l'Agent Logistique de LEGA.
Tu calcules les coûts de transport d'engins TP entre France et Portugal.
Données disponibles : transport routier (camion plateau), bateau (Ro-Ro Setúbal↔Le Havre), grue de chargement.
Tarifs approximatifs :
- Transport routier France↔Portugal : 800-1500€ selon distance/tonnage
- Bateau Ro-Ro : 400-700€ + port fees ~150€
- Grue chargement/déchargement : 200-500€
Pour chaque demande, donne : mode recommandé, coût estimé, délai, remarques douane si nécessaire.
Si tu manques d'info (poids, dimensions), demande-les clairement.
Langue: {lang_instr}

DEMANDE: {query}
RÉPONSE:"""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            res = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": AGENT_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False, "think": False,
                    "options": {"temperature": 0.2, "num_predict": 500},
                },
            )
            return res.json().get("message", {}).get("content", "Résultat indisponible.").strip()
    except Exception as e:
        logger.error(f"Logistique agent error: {e}")
        return f"⚠️ Erreur agent Logistique: {str(e)[:100]}"


async def run_comptable(payload: dict, lang: str) -> str:
    """Agent Comptable: devis et factures professionnels."""
    query = payload.get("message", "")
    lang_instr = {"fr": "Français.", "pt": "Português europeu (PT-PT).", "en": "English."}.get(lang, "Français.")
    prompt = f"""Tu es le Secrétaire Comptable de LEGA.
Tu génères des devis et factures professionnels pour la vente d'engins TP d'occasion entre France et Portugal.
Format devis : référence DEVIS-AAAA-NNN, date, coordonnées LEGA, coordonnées client, description machine (marque/modèle/année/heures), prix HT, TVA applicable (20% France / 23% Portugal), prix TTC, conditions de paiement, validité 30 jours.
Génère toujours un document structuré et professionnel.
Ne jamais inventer de prix — utilise uniquement les données fournies.
Langue: {lang_instr}

DEMANDE: {query}
DOCUMENT:"""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            res = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": AGENT_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False, "think": False,
                    "options": {"temperature": 0.1, "num_predict": 700},
                },
            )
            return res.json().get("message", {}).get("content", "Résultat indisponible.").strip()
    except Exception as e:
        logger.error(f"Comptable agent error: {e}")
        return f"⚠️ Erreur agent Comptable: {str(e)[:100]}"


async def run_traducteur(payload: dict, lang: str) -> str:
    """Agent Traducteur: documents techniques et commerciaux TP."""
    query = payload.get("message", "")
    lang_instr = {"fr": "Français.", "pt": "Português europeu (PT-PT).", "en": "English."}.get(lang, "Français.")
    prompt = f"""Tu es le Traducteur Multilingue de LEGA.
Tu traduis des documents techniques et commerciaux liés aux engins de travaux publics (pelleteuses, grues, chargeuses, etc.).
Langues : FR, PT (européen), EN, ES, DE, IT.
Règles :
- Conserver la mise en page originale (titres, listes, tableaux)
- Utiliser la terminologie technique correcte du secteur TP
- Pour PT : utiliser le portugais européen (pas brésilien)
- Indiquer la langue source et cible en en-tête
Langue de réponse: {lang_instr}

TEXTE À TRADUIRE / DEMANDE: {query}
```

### run_logistique() — ligne 1146
```python
async def run_logistique(payload: dict, lang: str) -> str:
    """Agent Logistique: calcul transport engins TP France↔Portugal."""
    query = payload.get("message", "")
    lang_instr = {"fr": "Français.", "pt": "Português europeu (PT-PT).", "en": "English."}.get(lang, "Français.")
    prompt = f"""Tu es l'Agent Logistique de LEGA.
Tu calcules les coûts de transport d'engins TP entre France et Portugal.
Données disponibles : transport routier (camion plateau), bateau (Ro-Ro Setúbal↔Le Havre), grue de chargement.
Tarifs approximatifs :
- Transport routier France↔Portugal : 800-1500€ selon distance/tonnage
- Bateau Ro-Ro : 400-700€ + port fees ~150€
- Grue chargement/déchargement : 200-500€
Pour chaque demande, donne : mode recommandé, coût estimé, délai, remarques douane si nécessaire.
Si tu manques d'info (poids, dimensions), demande-les clairement.
Langue: {lang_instr}

DEMANDE: {query}
RÉPONSE:"""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            res = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": AGENT_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False, "think": False,
                    "options": {"temperature": 0.2, "num_predict": 500},
                },
            )
            return res.json().get("message", {}).get("content", "Résultat indisponible.").strip()
    except Exception as e:
        logger.error(f"Logistique agent error: {e}")
        return f"⚠️ Erreur agent Logistique: {str(e)[:100]}"


async def run_comptable(payload: dict, lang: str) -> str:
    """Agent Comptable: devis et factures professionnels."""
    query = payload.get("message", "")
    lang_instr = {"fr": "Français.", "pt": "Português europeu (PT-PT).", "en": "English."}.get(lang, "Français.")
    prompt = f"""Tu es le Secrétaire Comptable de LEGA.
Tu génères des devis et factures professionnels pour la vente d'engins TP d'occasion entre France et Portugal.
Format devis : référence DEVIS-AAAA-NNN, date, coordonnées LEGA, coordonnées client, description machine (marque/modèle/année/heures), prix HT, TVA applicable (20% France / 23% Portugal), prix TTC, conditions de paiement, validité 30 jours.
Génère toujours un document structuré et professionnel.
Ne jamais inventer de prix — utilise uniquement les données fournies.
Langue: {lang_instr}

DEMANDE: {query}
DOCUMENT:"""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            res = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": AGENT_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False, "think": False,
                    "options": {"temperature": 0.1, "num_predict": 700},
                },
            )
            return res.json().get("message", {}).get("content", "Résultat indisponible.").strip()
    except Exception as e:
        logger.error(f"Comptable agent error: {e}")
        return f"⚠️ Erreur agent Comptable: {str(e)[:100]}"


async def run_traducteur(payload: dict, lang: str) -> str:
    """Agent Traducteur: documents techniques et commerciaux TP."""
    query = payload.get("message", "")
    lang_instr = {"fr": "Français.", "pt": "Português europeu (PT-PT).", "en": "English."}.get(lang, "Français.")
    prompt = f"""Tu es le Traducteur Multilingue de LEGA.
Tu traduis des documents techniques et commerciaux liés aux engins de travaux publics (pelleteuses, grues, chargeuses, etc.).
Langues : FR, PT (européen), EN, ES, DE, IT.
Règles :
- Conserver la mise en page originale (titres, listes, tableaux)
- Utiliser la terminologie technique correcte du secteur TP
- Pour PT : utiliser le portugais européen (pas brésilien)
- Indiquer la langue source et cible en en-tête
Langue de réponse: {lang_instr}

TEXTE À TRADUIRE / DEMANDE: {query}
TRADUCTION:"""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            res = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": AGENT_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False, "think": False,
                    "options": {"temperature": 0.2, "num_predict": 800},
                },
            )
            return res.json().get("message", {}).get("content", "Résultat indisponible.").strip()
    except Exception as e:
        logger.error(f"Traducteur agent error: {e}")
        return f"⚠️ Erreur agent Traducteur: {str(e)[:100]}"


async def run_demandes_prix(payload: dict, lang: str) -> str:
    """Agent Demandes de Prix: rédige des demandes aux fournisseurs/transporteurs."""
    query = payload.get("message", "")
    lang_instr = {"fr": "Français.", "pt": "Português europeu (PT-PT).", "en": "English."}.get(lang, "Français.")
    prompt = f"""Tu es l'Agent Demandes de Prix de LEGA.
Tu rédiges des demandes de prix professionnelles aux fournisseurs et transporteurs pour des engins TP d'occasion.
Format : objet clair, description précise de la machine recherchée (marque, modèle, année souhaitée, heures max, état), budget indicatif si fourni, délai souhaité, coordonnées LEGA.
Ton : professionnel, direct, bilingue FR/PT si fournisseur portugais.
Langue principale: {lang_instr}

DEMANDE: {query}
EMAIL:"""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            res = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": AGENT_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False, "think": False,
                    "options": {"temperature": 0.3, "num_predict": 500},
                },
            )
            return res.json().get("message", {}).get("content", "Résultat indisponible.").strip()
```

### run_comptable() — ligne 1180
```python
async def run_comptable(payload: dict, lang: str) -> str:
    """Agent Comptable: devis et factures professionnels."""
    query = payload.get("message", "")
    lang_instr = {"fr": "Français.", "pt": "Português europeu (PT-PT).", "en": "English."}.get(lang, "Français.")
    prompt = f"""Tu es le Secrétaire Comptable de LEGA.
Tu génères des devis et factures professionnels pour la vente d'engins TP d'occasion entre France et Portugal.
Format devis : référence DEVIS-AAAA-NNN, date, coordonnées LEGA, coordonnées client, description machine (marque/modèle/année/heures), prix HT, TVA applicable (20% France / 23% Portugal), prix TTC, conditions de paiement, validité 30 jours.
Génère toujours un document structuré et professionnel.
Ne jamais inventer de prix — utilise uniquement les données fournies.
Langue: {lang_instr}

DEMANDE: {query}
DOCUMENT:"""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            res = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": AGENT_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False, "think": False,
                    "options": {"temperature": 0.1, "num_predict": 700},
                },
            )
            return res.json().get("message", {}).get("content", "Résultat indisponible.").strip()
    except Exception as e:
        logger.error(f"Comptable agent error: {e}")
        return f"⚠️ Erreur agent Comptable: {str(e)[:100]}"


async def run_traducteur(payload: dict, lang: str) -> str:
    """Agent Traducteur: documents techniques et commerciaux TP."""
    query = payload.get("message", "")
    lang_instr = {"fr": "Français.", "pt": "Português europeu (PT-PT).", "en": "English."}.get(lang, "Français.")
    prompt = f"""Tu es le Traducteur Multilingue de LEGA.
Tu traduis des documents techniques et commerciaux liés aux engins de travaux publics (pelleteuses, grues, chargeuses, etc.).
Langues : FR, PT (européen), EN, ES, DE, IT.
Règles :
- Conserver la mise en page originale (titres, listes, tableaux)
- Utiliser la terminologie technique correcte du secteur TP
- Pour PT : utiliser le portugais européen (pas brésilien)
- Indiquer la langue source et cible en en-tête
Langue de réponse: {lang_instr}

TEXTE À TRADUIRE / DEMANDE: {query}
TRADUCTION:"""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            res = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": AGENT_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False, "think": False,
                    "options": {"temperature": 0.2, "num_predict": 800},
                },
            )
            return res.json().get("message", {}).get("content", "Résultat indisponible.").strip()
    except Exception as e:
        logger.error(f"Traducteur agent error: {e}")
        return f"⚠️ Erreur agent Traducteur: {str(e)[:100]}"


async def run_demandes_prix(payload: dict, lang: str) -> str:
    """Agent Demandes de Prix: rédige des demandes aux fournisseurs/transporteurs."""
    query = payload.get("message", "")
    lang_instr = {"fr": "Français.", "pt": "Português europeu (PT-PT).", "en": "English."}.get(lang, "Français.")
    prompt = f"""Tu es l'Agent Demandes de Prix de LEGA.
Tu rédiges des demandes de prix professionnelles aux fournisseurs et transporteurs pour des engins TP d'occasion.
Format : objet clair, description précise de la machine recherchée (marque, modèle, année souhaitée, heures max, état), budget indicatif si fourni, délai souhaité, coordonnées LEGA.
Ton : professionnel, direct, bilingue FR/PT si fournisseur portugais.
Langue principale: {lang_instr}

DEMANDE: {query}
EMAIL:"""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            res = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": AGENT_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False, "think": False,
                    "options": {"temperature": 0.3, "num_predict": 500},
                },
            )
            return res.json().get("message", {}).get("content", "Résultat indisponible.").strip()
    except Exception as e:
        logger.error(f"DemandePrix agent error: {e}")
        return f"⚠️ Erreur agent Demandes de Prix: {str(e)[:100]}"


_DOC_KW = {"manuel","manuels","manual","manuais","fiche technique","ficha técnica","datasheet",
           "data sheet","documentation","doc technique","pdf technique","certificat ce",
           "certificação","homolog","ce marking","guide d'utilisation","mode d'emploi",
           "technical spec","guide technique","notice","livret","schéma","schémas"}

_DOC_REDIRECT = {
    "fr": "Pour consulter nos manuels et fiches techniques, rendez-vous dans la section Documentation de notre site vitrine. Connectez-vous avec votre compte client pour y accéder.",
    "pt": "Para consultar os nossos manuais e fichas técnicas, aceda à secção Documentação do nosso site vitrine. Precisa de iniciar sessão com a sua conta de cliente.",
    "en": "To access our manuals and technical documentation, please visit the Documentation section of our website. You need to log in with your client account.",
    "es": "Para consultar nuestros manuales y fichas técnicas, visite la sección Documentación de nuestro sitio web. Debe iniciar sesión con su cuenta de cliente.",
    "de": "Für unsere Handbücher und technischen Datenblätter besuchen Sie bitte den Bereich Dokumentation unserer Website. Bitte melden Sie sich mit Ihrem Kundenkonto an.",
}

async def run_standardiste(message: str, lang: str) -> str:
    """Standardiste Multilingue: réception client, catalogue, transfert agents (gemma4:e2b)."""
    if any(w in message.lower() for w in _DOC_KW):
        return _DOC_REDIRECT.get(lang, _DOC_REDIRECT["fr"])
    lang_instr = {
        "fr": "Français. Tu t'appelles Léa, tu es la standardiste de LEGA.",
        "pt": "Português europeu (PT-PT). Chamas-te Léa, és a recepcionista da LEGA.",
        "en": "English. Your name is Lea, you are LEGA's receptionist.",
    }.get(lang, "Français.")

    # Catalogue depuis la vitrine (site_products, status=available)
    catalogue_context = ""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{LEGA_SITE_API}/products?status=available&limit=100")
            if r.status_code == 200:
```

### run_traducteur() — ligne 1210
```python
async def run_traducteur(payload: dict, lang: str) -> str:
    """Agent Traducteur: documents techniques et commerciaux TP."""
    query = payload.get("message", "")
    lang_instr = {"fr": "Français.", "pt": "Português europeu (PT-PT).", "en": "English."}.get(lang, "Français.")
    prompt = f"""Tu es le Traducteur Multilingue de LEGA.
Tu traduis des documents techniques et commerciaux liés aux engins de travaux publics (pelleteuses, grues, chargeuses, etc.).
Langues : FR, PT (européen), EN, ES, DE, IT.
Règles :
- Conserver la mise en page originale (titres, listes, tableaux)
- Utiliser la terminologie technique correcte du secteur TP
- Pour PT : utiliser le portugais européen (pas brésilien)
- Indiquer la langue source et cible en en-tête
Langue de réponse: {lang_instr}

TEXTE À TRADUIRE / DEMANDE: {query}
TRADUCTION:"""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            res = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": AGENT_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False, "think": False,
                    "options": {"temperature": 0.2, "num_predict": 800},
                },
            )
            return res.json().get("message", {}).get("content", "Résultat indisponible.").strip()
    except Exception as e:
        logger.error(f"Traducteur agent error: {e}")
        return f"⚠️ Erreur agent Traducteur: {str(e)[:100]}"


async def run_demandes_prix(payload: dict, lang: str) -> str:
    """Agent Demandes de Prix: rédige des demandes aux fournisseurs/transporteurs."""
    query = payload.get("message", "")
    lang_instr = {"fr": "Français.", "pt": "Português europeu (PT-PT).", "en": "English."}.get(lang, "Français.")
    prompt = f"""Tu es l'Agent Demandes de Prix de LEGA.
Tu rédiges des demandes de prix professionnelles aux fournisseurs et transporteurs pour des engins TP d'occasion.
Format : objet clair, description précise de la machine recherchée (marque, modèle, année souhaitée, heures max, état), budget indicatif si fourni, délai souhaité, coordonnées LEGA.
Ton : professionnel, direct, bilingue FR/PT si fournisseur portugais.
Langue principale: {lang_instr}

DEMANDE: {query}
EMAIL:"""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            res = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": AGENT_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False, "think": False,
                    "options": {"temperature": 0.3, "num_predict": 500},
                },
            )
            return res.json().get("message", {}).get("content", "Résultat indisponible.").strip()
    except Exception as e:
        logger.error(f"DemandePrix agent error: {e}")
        return f"⚠️ Erreur agent Demandes de Prix: {str(e)[:100]}"


_DOC_KW = {"manuel","manuels","manual","manuais","fiche technique","ficha técnica","datasheet",
           "data sheet","documentation","doc technique","pdf technique","certificat ce",
           "certificação","homolog","ce marking","guide d'utilisation","mode d'emploi",
           "technical spec","guide technique","notice","livret","schéma","schémas"}

_DOC_REDIRECT = {
    "fr": "Pour consulter nos manuels et fiches techniques, rendez-vous dans la section Documentation de notre site vitrine. Connectez-vous avec votre compte client pour y accéder.",
    "pt": "Para consultar os nossos manuais e fichas técnicas, aceda à secção Documentação do nosso site vitrine. Precisa de iniciar sessão com a sua conta de cliente.",
    "en": "To access our manuals and technical documentation, please visit the Documentation section of our website. You need to log in with your client account.",
    "es": "Para consultar nuestros manuales y fichas técnicas, visite la sección Documentación de nuestro sitio web. Debe iniciar sesión con su cuenta de cliente.",
    "de": "Für unsere Handbücher und technischen Datenblätter besuchen Sie bitte den Bereich Dokumentation unserer Website. Bitte melden Sie sich mit Ihrem Kundenkonto an.",
}

async def run_standardiste(message: str, lang: str) -> str:
    """Standardiste Multilingue: réception client, catalogue, transfert agents (gemma4:e2b)."""
    if any(w in message.lower() for w in _DOC_KW):
        return _DOC_REDIRECT.get(lang, _DOC_REDIRECT["fr"])
    lang_instr = {
        "fr": "Français. Tu t'appelles Léa, tu es la standardiste de LEGA.",
        "pt": "Português europeu (PT-PT). Chamas-te Léa, és a recepcionista da LEGA.",
        "en": "English. Your name is Lea, you are LEGA's receptionist.",
    }.get(lang, "Français.")

    # Catalogue depuis la vitrine (site_products, status=available)
    catalogue_context = ""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{LEGA_SITE_API}/products?status=available&limit=100")
            if r.status_code == 200:
                data = r.json()
                items_list = data.get("items", data) if isinstance(data, dict) else data
                total_count = data.get("total", len(items_list)) if isinstance(data, dict) else len(items_list)
                items = [
                    f"• {p['title']} — {p['price']} {p.get('currency','€')} ({p.get('category','')})"
                    if p.get('price') else
                    f"• {p['title']} — Prix sur demande ({p.get('category','')})"
                    for p in (items_list or [])
                ]
                if items:
                    catalogue_context = f"\nCATALOGUE DISPONIBLE ({total_count} annonces au total):\n" + "\n".join(items)
    except Exception:
        pass

    prompt = f"""Tu es Léa, la standardiste multilingue de LEGA, négociant international en engins de travaux publics (pelleteuses, chargeuses, grues, bulldozers, tracteurs TP d'occasion). LEGA opère entre la France et le Portugal.
Langue de réponse: {lang_instr}
{catalogue_context}

Règles:
- Réponse professionnelle, chaleureuse, concise (2-4 phrases MAX)
- Si question sur une machine spécifique → consulte catalogue ci-dessus, mentionne les machines disponibles
- Si demande complexe (recherche marché, email, analyse photo) → dis que tu passes l'appel à Tony, le spécialiste
- Ne jamais inventer de prix ou machines qui ne sont pas dans le catalogue

DEMANDE: {message}
RÉPONSE LÉA:"""

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0)) as client:
            res = await client.post(
```

### run_demandes_prix() — ligne 1243
```python
async def run_demandes_prix(payload: dict, lang: str) -> str:
    """Agent Demandes de Prix: rédige des demandes aux fournisseurs/transporteurs."""
    query = payload.get("message", "")
    lang_instr = {"fr": "Français.", "pt": "Português europeu (PT-PT).", "en": "English."}.get(lang, "Français.")
    prompt = f"""Tu es l'Agent Demandes de Prix de LEGA.
Tu rédiges des demandes de prix professionnelles aux fournisseurs et transporteurs pour des engins TP d'occasion.
Format : objet clair, description précise de la machine recherchée (marque, modèle, année souhaitée, heures max, état), budget indicatif si fourni, délai souhaité, coordonnées LEGA.
Ton : professionnel, direct, bilingue FR/PT si fournisseur portugais.
Langue principale: {lang_instr}

DEMANDE: {query}
EMAIL:"""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            res = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": AGENT_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False, "think": False,
                    "options": {"temperature": 0.3, "num_predict": 500},
                },
            )
            return res.json().get("message", {}).get("content", "Résultat indisponible.").strip()
    except Exception as e:
        logger.error(f"DemandePrix agent error: {e}")
        return f"⚠️ Erreur agent Demandes de Prix: {str(e)[:100]}"


_DOC_KW = {"manuel","manuels","manual","manuais","fiche technique","ficha técnica","datasheet",
           "data sheet","documentation","doc technique","pdf technique","certificat ce",
           "certificação","homolog","ce marking","guide d'utilisation","mode d'emploi",
           "technical spec","guide technique","notice","livret","schéma","schémas"}

_DOC_REDIRECT = {
    "fr": "Pour consulter nos manuels et fiches techniques, rendez-vous dans la section Documentation de notre site vitrine. Connectez-vous avec votre compte client pour y accéder.",
    "pt": "Para consultar os nossos manuais e fichas técnicas, aceda à secção Documentação do nosso site vitrine. Precisa de iniciar sessão com a sua conta de cliente.",
    "en": "To access our manuals and technical documentation, please visit the Documentation section of our website. You need to log in with your client account.",
    "es": "Para consultar nuestros manuales y fichas técnicas, visite la sección Documentación de nuestro sitio web. Debe iniciar sesión con su cuenta de cliente.",
    "de": "Für unsere Handbücher und technischen Datenblätter besuchen Sie bitte den Bereich Dokumentation unserer Website. Bitte melden Sie sich mit Ihrem Kundenkonto an.",
}

async def run_standardiste(message: str, lang: str) -> str:
    """Standardiste Multilingue: réception client, catalogue, transfert agents (gemma4:e2b)."""
    if any(w in message.lower() for w in _DOC_KW):
        return _DOC_REDIRECT.get(lang, _DOC_REDIRECT["fr"])
    lang_instr = {
        "fr": "Français. Tu t'appelles Léa, tu es la standardiste de LEGA.",
        "pt": "Português europeu (PT-PT). Chamas-te Léa, és a recepcionista da LEGA.",
        "en": "English. Your name is Lea, you are LEGA's receptionist.",
    }.get(lang, "Français.")

    # Catalogue depuis la vitrine (site_products, status=available)
    catalogue_context = ""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{LEGA_SITE_API}/products?status=available&limit=100")
            if r.status_code == 200:
                data = r.json()
                items_list = data.get("items", data) if isinstance(data, dict) else data
                total_count = data.get("total", len(items_list)) if isinstance(data, dict) else len(items_list)
                items = [
                    f"• {p['title']} — {p['price']} {p.get('currency','€')} ({p.get('category','')})"
                    if p.get('price') else
                    f"• {p['title']} — Prix sur demande ({p.get('category','')})"
                    for p in (items_list or [])
                ]
                if items:
                    catalogue_context = f"\nCATALOGUE DISPONIBLE ({total_count} annonces au total):\n" + "\n".join(items)
    except Exception:
        pass

    prompt = f"""Tu es Léa, la standardiste multilingue de LEGA, négociant international en engins de travaux publics (pelleteuses, chargeuses, grues, bulldozers, tracteurs TP d'occasion). LEGA opère entre la France et le Portugal.
Langue de réponse: {lang_instr}
{catalogue_context}

Règles:
- Réponse professionnelle, chaleureuse, concise (2-4 phrases MAX)
- Si question sur une machine spécifique → consulte catalogue ci-dessus, mentionne les machines disponibles
- Si demande complexe (recherche marché, email, analyse photo) → dis que tu passes l'appel à Tony, le spécialiste
- Ne jamais inventer de prix ou machines qui ne sont pas dans le catalogue

DEMANDE: {message}
RÉPONSE LÉA:"""

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0)) as client:
            res = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": AGENT_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False, "think": False,
                    "options": {"temperature": 0.3, "num_predict": 300},
                },
            )
            return res.json().get("message", {}).get("content", "").strip()
    except Exception as e:
        logger.error(f"Standardiste error: {e}")
        fallback = {
            "fr": "Je vous transfère à notre assistant Tony, qui pourra mieux vous aider.",
            "pt": "Vou transferi-lo para o Tony, o nosso assistente especializado.",
            "en": "I'll transfer you to Tony, our specialist assistant.",
        }
        return fallback.get(lang, fallback["fr"])


async def run_standardiste_streaming(message: str, lang: str, websocket: "WebSocket") -> None:
    """Standardiste Léa : streaming Ollama gemma4:e2b → phrases → TTS → WS audio_chunk."""
    import base64

    if any(w in message.lower() for w in _DOC_KW):
        redir = _DOC_REDIRECT.get(lang, _DOC_REDIRECT["fr"])
        await websocket.send_json({"type": "stream_chunk", "payload": redir, "metadata": {"done": True}})
        return

    lang_instr = {
        "fr": "Français. Tu t'appelles Léa, tu es la standardiste de LEGA.",
        "pt": "Português europeu (PT-PT). Chamas-te Léa, és a recepcionista da LEGA.",
        "en": "English. Your name is Lea, you are LEGA's receptionist.",
        "es": "Español. Tu nombre es Léa, eres la recepcionista de LEGA.",
```

### run_lea_streaming() — ligne 1613
```python
async def run_lea_streaming(message: str, lang: str, canal: str, websocket: "WebSocket") -> None:
    """Agent Léa unifié. Canal web → gemma2:2b. Canal voice/phone/whatsapp → gemma4:e2b + TTS."""
    import base64

    if any(w in message.lower() for w in _DOC_KW):
        redir = _DOC_REDIRECT.get(lang, _DOC_REDIRECT["fr"])
        await websocket.send_json({"type": "stream_chunk", "payload": redir, "metadata": {"done": True}})
        return

    is_voice = canal in ("phone", "whatsapp", "telegram", "voice")
    model = AGENT_MODEL if is_voice else VITRINE_MODEL

    lang_instr = {
        "fr": "Réponds en français.",
        "pt": "Responde em português europeu (PT-PT).",
        "en": "Reply in English.",
        "es": "Responde en español.",
        "de": "Antworte auf Deutsch.",
        "it": "Rispondi in italiano.",
        "ru": "Отвечай на русском.",
        "ar": "أجب باللغة العربية.",
        "nl": "Antwoord in het Nederlands.",
        "zh": "用中文回答。",
    }.get(lang, "Réponds en français.")

    catalogue_ctx = ""
    try:
        async with httpx.AsyncClient(timeout=10.0) as c:
            r = await c.get(f"{LEGA_SITE_API}/products?status=available&limit=100")
            if r.status_code == 200:
                data = r.json()
                items = data.get("items", data) if isinstance(data, dict) else data
                total_count = data.get("total", len(items)) if isinstance(data, dict) else len(items)
                lines = [
                    f"- {p.get('reference','') + ' ' if p.get('reference') else ''}{p['title']} : {p['price']} {p.get('currency','EUR')}"
                    if p.get("price") else
                    f"- {p.get('reference','') + ' ' if p.get('reference') else ''}{p['title']} : prix sur demande"
                    for p in (items or [])
                ]
                if lines:
                    catalogue_ctx = f"\nCATALOGUE ({total_count} annonces):\n" + "\n".join(lines)
    except Exception:
        pass

    rules = (
        "2 à 4 phrases. Ton chaleureux et professionnel. Ne pas inventer de machines ou prix. "
        "Si demande complexe, mentionner le passage à Tony."
        if is_voice else
        "1 à 2 phrases MAXIMUM. Ton calme et professionnel. Zéro emoji. Réponse directe et naturelle."
    )
    max_tokens = 300 if is_voice else 250

    prompt = (
        f"Tu es Léa, assistante multilingue de LEGA.PT, spécialisée en engins de travaux publics d'occasion.\n"
        f"Langue: {lang_instr}\n"
        f"{catalogue_ctx}\n"
        f"IMPORTANT: LEGA.PT vend uniquement des engins d'occasion. Nous ne faisons PAS de réparations, "
        f"maintenance, location, ni pièces détachées. Si le client demande ces services, explique-lui "
        f"poliment que nous ne proposons pas ce service et que nous vendons uniquement des machines TP d'occasion.\n"
        f"RÈGLES: {rules}\n"
        f"CLIENT: {message}\nLÉA:"
    )

    full_text = ""
    buf = ""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=5.0)) as client:
            async with client.stream(
                "POST", f"{OLLAMA_URL}/api/chat",
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": True, "think": False,
                    "options": {"temperature": 0.3, "num_predict": max_tokens},
                },
            ) as resp:
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        token = json.loads(line).get("message", {}).get("content", "")
                    except json.JSONDecodeError:
                        continue
                    if not token:
                        continue
                    buf += token
                    full_text += token
                    parts = _SENTENCE_RE.split(buf)
                    for sentence in parts[:-1]:
                        sentence = sentence.strip()
                        if not sentence:
                            continue
                        await websocket.send_json({"type": "text_chunk", "payload": sentence + " "})
                        if TTS_ENABLED:
                            audio = await text_to_speech_edge(sentence, lang)
                            if audio:
                                await websocket.send_json({
                                    "type": "audio_chunk",
                                    "payload": base64.b64encode(audio).decode(),
                                    "lang": lang,
                                })
                    buf = parts[-1]

        if buf.strip():
            await websocket.send_json({"type": "text_chunk", "payload": buf.strip()})
            if TTS_ENABLED:
                audio = await text_to_speech_edge(buf.strip(), lang)
                if audio:
                    await websocket.send_json({
                        "type": "audio_chunk",
                        "payload": base64.b64encode(audio).decode(),
                        "lang": lang,
                    })

        await websocket.send_json({
            "type": "agent_response",
            "payload": re.sub(r'\s+', ' ', full_text).strip(),
            "metadata": {"agent": "lea", "canal": canal, "lang": lang, "model": model},
        })
    except Exception as e:
        logger.error(f"lea_streaming error ({canal}): {e}")
```

### run_site_manager() — ligne 1746
```python
async def run_site_manager(payload: dict, lang: str) -> str:
    """
    Agent Site Manager : interprète une commande en langage naturel
    et applique les modifications sur le backend vitrine (port 8003).
    Réservé aux sessions admin (is_admin=True dans le WS).
    """
    message = payload.get("message", "")
    lang_instr = {"fr": "Français.", "pt": "Português europeu.", "en": "English."}.get(lang, "Français.")

    # Récupérer la config actuelle pour contexte
    cfg_context = ""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{LEGA_SITE_API}/config")
            if r.status_code == 200:
                rows = r.json()
                cfg_context = "\n".join(f"  {row['key']}: {row['value']}" for row in rows if row.get("value"))
    except Exception:
        pass

    prompt = f"""Tu es l'Agent Site Manager de LEGA. Tu modifies le site vitrine en répondant UNIQUEMENT avec un JSON d'action.

CONFIG ACTUELLE DU SITE:
{cfg_context or "(indisponible)"}

CLÉS MODIFIABLES (site_config):
- site_name, slogan_fr, slogan_pt, slogan_en, slogan_es, slogan_de, slogan_it
- phone, email, address
- color_primary (hex), color_secondary (hex)
- stat_machines, stat_langues, stat_pays, stat_support

SECTIONS ACTIVABLES (site_sections): hero, stats, search, catalogue, ai_banner, contact, footer

COMMANDE ADMIN ({lang_instr}): {message}

Réponds UNIQUEMENT avec ce JSON (une seule action):
{{"action":"config_update"|"section_toggle"|"product_add"|"product_update"|"product_status",
  "key":"nom_clé","value":"valeur",
  "section":"nom_section","enabled":true|false,
  "product_id":"uuid si update/status",
  "product":{{"title":"","category":"machines_tp|trucks|trailers|vans","brand":"","model":"","year":2020,"hours":5000,"price":45000,"currency":"EUR","location":"","description":"","status":"available|draft|sold|reserved"}},
  "status":"available|draft|sold|reserved",
  "confirmation":"message confirmatif court EN {lang.upper()}"}}

Exemples:
- "Change le slogan FR" → {{"action":"config_update","key":"slogan_fr","value":"Nouveau slogan","confirmation":"Slogan FR mis à jour."}}
- "Désactive la section stats" → {{"action":"section_toggle","section":"stats","enabled":false,"confirmation":"Section stats désactivée."}}
- "Ajoute une pelleteuse CAT 320D 2019 45000€" → {{"action":"product_add","product":{{"title":"CAT 320D","category":"machines_tp","brand":"CAT","model":"320D","year":2019,"price":45000,"currency":"EUR","status":"available"}},"confirmation":"Produit CAT 320D ajouté."}}
- "Passe le produit abc-123 à vendu" → {{"action":"product_status","product_id":"abc-123","status":"sold","confirmation":"Produit marqué vendu."}}
- "Mets le prix du produit abc-123 à 38000€" → {{"action":"product_update","product_id":"abc-123","product":{{"price":38000}},"confirmation":"Prix mis à jour."}}

JSON:"""

    action_json = None
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
            res = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": AGENT_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False, "think": False,
                    "options": {"temperature": 0.1, "num_predict": 200},
                },
            )
            raw = res.json().get("message", {}).get("content", "")
            start, end = raw.find("{"), raw.rfind("}") + 1
            if start >= 0 and end > start:
                action_json = json.loads(raw[start:end])
    except Exception as e:
        logger.error(f"site_manager LLM error: {e}")
        return {"fr": "⚠️ Erreur LLM site_manager.", "pt": "⚠️ Erro LLM site_manager.", "en": "⚠️ LLM site_manager error."}.get(lang, "⚠️ Erreur.")

    if not action_json:
        return {"fr": "❌ Je n'ai pas compris la commande.", "pt": "❌ Não entendi o comando.", "en": "❌ Command not understood."}.get(lang, "❌")

    confirmation = action_json.get("confirmation", "✅ Fait.")
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            action = action_json.get("action", "")
            if action == "config_update":
                key = action_json.get("key", "")
                value = action_json.get("value", "")
                if key and value:
                    r = await client.post(
                        f"{LEGA_SITE_API}/config/bulk",
                        json={key: value},
                    )
                    if r.status_code != 200:
                        return f"❌ Erreur API config: HTTP {r.status_code}"
                    logger.info(f"site_manager: config_update {key}={value[:40]}")
            elif action == "section_toggle":
                section = action_json.get("section", "")
                enabled = action_json.get("enabled", True)
                if section:
                    r = await client.patch(
                        f"{LEGA_SITE_API}/sections/{section}",
                        json={"enabled": enabled},
                    )
                    if r.status_code != 200:
                        return f"❌ Erreur API sections: HTTP {r.status_code}"
                    logger.info(f"site_manager: section_toggle {section}={enabled}")
            elif action == "product_add":
                product_data = action_json.get("product", {})
                if not product_data.get("title"):
                    return {"fr": "❌ Titre produit manquant.", "pt": "❌ Título do produto em falta.", "en": "❌ Product title missing."}.get(lang, "❌")
                r = await client.post(f"{LEGA_SITE_API}/products", json=product_data)
                if r.status_code not in (200, 201):
                    return f"❌ Erreur création produit: HTTP {r.status_code} — {r.text[:80]}"
                new_id = r.json().get("id", "?")
                confirmation = action_json.get("confirmation", f"Produit ajouté (id: {new_id}).")
                logger.info(f"site_manager: product_add id={new_id}")
            elif action == "product_update":
                pid = action_json.get("product_id", "")
                product_data = action_json.get("product", {})
                if not pid:
                    return {"fr": "❌ ID produit manquant.", "pt": "❌ ID do produto em falta.", "en": "❌ Product ID missing."}.get(lang, "❌")
                r = await client.put(f"{LEGA_SITE_API}/products/{pid}", json=product_data)
                if r.status_code != 200:
                    return f"❌ Erreur mise à jour produit: HTTP {r.status_code} — {r.text[:80]}"
                logger.info(f"site_manager: product_update id={pid}")
```

### task_worker() — ligne 1988
```python
async def task_worker():
    """Poll pending tasks every 10s and execute the appropriate agent."""
    logger.info("Task worker started")
    while True:
        try:
            conn = await db_connect()
            rows = await conn.fetch(
                "SELECT task_id, session_id, agent_name, payload, language FROM tasks WHERE status='pending' ORDER BY created_at LIMIT 5"
            )
            await conn.close()

            for row in rows:
                task_id = row["task_id"]
                session_id = row["session_id"]
                agent_name = row["agent_name"]
                payload = json.loads(row["payload"])
                lang = row["language"]

                logger.info(f"Worker: executing task {task_id} → agent {agent_name}")
                await update_task(task_id, "running")

                executor = AGENT_EXECUTORS.get(agent_name)
                if executor:
                    try:
                        result = await executor(payload, lang)

                        # Détecter brouillon Sam en attente de confirmation
                        extra_meta: dict = {}
                        draft_match = re.search(r'___DRAFT_ID:([a-f0-9\-]+)___', result)
                        if draft_match:
                            extra_meta = {"confirm_required": True, "draft_id": draft_match.group(1)}
                            result = result[:draft_match.start()].rstrip()

                        # Détecter résultats max_search stockés
                        search_count = 0
                        search_match = re.search(r'___SEARCH_COUNT:(\d+)___', result)
                        if search_match:
                            search_count = int(search_match.group(1))
                            result = result[:search_match.start()].rstrip()

                        await update_task(task_id, "done", {"text": result})

                        # Push result via WebSocket if client still connected
                        ws = active_connections.get(session_id)
                        if ws:
                            try:
                                await ws.send_json({
                                    "type": "agent_response",
                                    "payload": result,
                                    "metadata": {
                                        "task_id": task_id,
                                        "agent": agent_name,
                                        "done": True,
                                        **extra_meta,
                                    },
                                })
                                # Notification Tony + refresh panel si annonces trouvées
                                if search_count > 0:
                                    tony_notif = {
                                        "fr": f"✅ Max a trouvé {search_count} annonce(s).\nDisponibles dans l'onglet 📋 Annonces.",
                                        "pt": f"✅ Max encontrou {search_count} anúncio(s).\nDisponíveis no separador 📋 Anúncios.",
                                        "en": f"✅ Max found {search_count} listing(s).\nAvailable in the 📋 Listings tab.",
                                    }.get(lang, f"✅ Max a trouvé {search_count} annonce(s).\nDisponibles dans l'onglet 📋 Annonces.")
                                    await ws.send_json({"type": "agent_response", "payload": tony_notif, "metadata": {"agent": "tony", "done": True}})
                                    await ws.send_json({"type": "search_results_ready", "payload": search_count})
                            except Exception as e:
                                logger.warning(f"WS push failed: {e}")
                    except Exception as e:
                        logger.error(f"Agent {agent_name} error: {e}")
                        await update_task(task_id, "failed", error=str(e)[:200])
                        ws = active_connections.get(session_id)
                        if ws:
                            try:
                                msg_fr = f"⚠️ L'agent {agent_name} a rencontré une erreur. Réessayez."
                                msg_pt = f"⚠️ O agente {agent_name} encontrou um erro. Tente novamente."
                                msg = msg_pt if lang == "pt" else msg_fr
                                await ws.send_json({"type": "agent_response", "payload": msg, "metadata": {"error": True}})
                            except Exception:
                                pass
                else:
                    await update_task(task_id, "failed", error=f"Agent {agent_name} non implémenté")

        except Exception as e:
            logger.error(f"Worker error: {e}")

        await asyncio.sleep(10)


async def trial_expiry_cron():
    """Expire les trials toutes les heures."""
    logger.info("Trial expiry cron started")
    while True:
        await asyncio.sleep(3600)
        try:
            conn = await db_connect()
            result = await conn.execute(
                "UPDATE user_subscriptions SET status='expired' WHERE status='trial' AND trial_expires_at < NOW()"
            )
            expired_count = int(result.split()[-1]) if result else 0
            if expired_count:
                logger.info(f"Trial expiry cron: {expired_count} trial(s) expirés")
            await conn.close()
        except Exception as e:
            logger.error(f"Trial expiry cron error: {e}")


# ── Brief matinal Agenda ─────────────────────────────────────────────────────

async def build_morning_brief(lang: str = "fr", user_prefs: dict = None) -> str:
    """Construit le contenu du brief matinal pour l'agent Agenda."""
    prefs = user_prefs or {}
    sections = []

    # 1. Planning du jour (événements de aujourd'hui)
    try:
        conn = await db_connect()
        today_events = await conn.fetch(
            """SELECT title, start_time, location FROM events
               WHERE start_time::date = CURRENT_DATE
               ORDER BY start_time LIMIT 10"""
        )
```

### websocket_endpoint() — ligne 2311
```python
async def websocket_endpoint(ws: WebSocket, token: str = None):
    await ws.accept()
    session_id = str(uuid.uuid4())
    active_connections[session_id] = ws
    user_id = await get_or_create_user(session_id)

    # Vérifier si session admin (JWT valide en query param)
    is_admin = False
    if token:
        try:
            jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            is_admin = True
            logger.info(f"WS admin session: {session_id[:8]}")
        except Exception:
            pass

    logger.info(f"WS connected: {session_id} (user {user_id[:8]}, admin={is_admin})")

    # Mémoire conversationnelle — chargée depuis DB, enrichie en mémoire pendant la session
    conversation_history: list = await _load_conv_history(user_id)
    session_context: dict = {
        "pending_actions": [],
        "last_agent": None,
        "last_intent": None,
        "user_lang": "fr",
    }

    # Envoyer message d'accueil Tony à la connexion
    _tony_welcome = {
        "fr": "Bonjour ! Je suis Tony, votre responsable de bureau LEGA.\nJe coordonne votre équipe d'agents IA. Que puis-je faire pour vous ?",
        "pt": "Olá! Sou o Tony, o seu responsável de bureau LEGA.\nCoordenо a sua equipa de agentes IA. Em que posso ajudar?",
        "en": "Hello! I'm Tony, your LEGA office manager.\nI coordinate your AI agent team. How can I help you?",
    }
    await ws.send_json({
        "type": "welcome",
        "payload": _tony_welcome["fr"],
        "metadata": {"agent": "tony", "texts": _tony_welcome},
    })

    try:
        while True:
            data = await ws.receive_text()
            payload_raw = json.loads(data)

            if payload_raw.get("type") == "ping":
                continue

            # Fast-path : confirmation envoi email Sam
            draft_id = payload_raw.get("draft_id")
            if draft_id and payload_raw.get("payload") == "CONFIRM_SEND":
                draft = sam_pending.pop(draft_id, None)
                if draft and SMTP_FROM and SMTP_PASSWORD:
                    try:
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(None, _smtp_send, draft["to_addr"], draft["subject"], draft["body"])
                        await ws.send_json({"type": "agent_response",
                            "payload": f"✅ Email envoyé à {draft['to_addr']}",
                            "metadata": {"done": True, "agent": "sam_comms"}})
                        logger.info(f"sam_comms: email confirmé → {draft['to_addr']}")
                    except Exception as e:
                        await ws.send_json({"type": "agent_response",
                            "payload": f"⚠️ Envoi échoué : {str(e)[:120]}",
                            "metadata": {"done": True, "agent": "sam_comms", "error": True}})
                elif draft and not SMTP_PASSWORD:
                    await ws.send_json({"type": "agent_response",
                        "payload": "⚠️ SMTP non configuré — email non envoyé.",
                        "metadata": {"done": True, "agent": "sam_comms"}})
                else:
                    await ws.send_json({"type": "agent_response",
                        "payload": "⚠️ Brouillon introuvable ou expiré.",
                        "metadata": {"done": True, "agent": "sam_comms"}})
                continue

            user_msg = payload_raw.get("payload", "")
            if not user_msg.strip():
                continue

            logger.info(f"WS [{session_id[:8]}]: {user_msg[:80]}")

            client_lang = payload_raw.get("lang")
            preferred_agent = payload_raw.get("preferred_agent")

            # Routing agent Léa unifié (web → gemma2:2b, voice → gemma4:e2b)
            if preferred_agent == "lea":
                canal = payload_raw.get("canal", "web")
                lang = detect_language(user_msg, client_lang)
                await run_lea_streaming(user_msg, lang, canal, ws)
                await asyncio.sleep(0.05)
                continue

            # Aliases backward-compat
            if preferred_agent == "vitrine_bot":
                lang = detect_language(user_msg, client_lang)
                await run_lea_streaming(user_msg, lang, "web", ws)
                await asyncio.sleep(0.05)
                continue

            if preferred_agent == "standardiste":
                lang = detect_language(user_msg, client_lang)
                await run_lea_streaming(user_msg, lang, "voice", ws)
                await asyncio.sleep(0.05)
                continue

            # Ajouter message user à l'historique local
            conversation_history.append({"role": "user", "content": user_msg})
            if len(conversation_history) > 20:
                conversation_history[:] = conversation_history[-20:]

            # Étape 1 — Accusé réception instantané (keyword, zéro LLM)
            quick_ack = tony_quick_ack(user_msg, client_lang)
            await ws.send_json({
                "type": "thinking",
                "payload": quick_ack,
                "metadata": {"stage": "thinking"},
            })

            # Étape 2 — Classification + dispatch en arrière-plan
            asyncio.create_task(
                tony_dispatch(user_msg, client_lang, ws, session_id, user_id, is_admin,
                              conversation_history, session_context)
            )
```

---
## SYSTEM PROMPTS DES AGENTS

```python
34:AGENT_MODEL = "gemma4:e2b"
45:PREMIUM_AGENTS = {"max_search", "lea_extract", "visa_vision", "logistique", "comptable", "traducteur", "demandes_prix"}
89:VITRINE_MODEL = "gemma2:2b"
150:TONY_SYSTEM = """Respond ONLY with valid JSON. No text before or after.
313:    prompt = f"{TONY_SYSTEM}\n\n{lang_hint}\nForce lang=\"{forced_lang}\" in your JSON.{no_greet}\n\n{history_str}MESSAGE: {message}\n\nJSON:"
319:                    "model": AGENT_MODEL,
586:        enriched = await _ollama_quick(AGENT_MODEL, prompt, 300, 20.0)
614:        response = await _ollama_quick(AGENT_MODEL, prompt, 200, 40.0)
699:        if agent in PREMIUM_AGENTS:
935:    prompt = f"""Tu es Max Search, expert en recherche de machines TP pour le marché France→Portugal.
961:                    "model": AGENT_MODEL,
1003:    prompt = f"""Tu es Sam Comms, expert communication B2B pour PME TP.
1019:                    "model": AGENT_MODEL,
1118:    prompt = f"""Tu es l'Agent Documentation de LEGA, expert en machines TP et négoce France-Portugal.
1134:                    "model": AGENT_MODEL,
1150:    prompt = f"""Tu es l'Agent Logistique de LEGA.
1168:                    "model": AGENT_MODEL,
1184:    prompt = f"""Tu es le Secrétaire Comptable de LEGA.
1198:                    "model": AGENT_MODEL,
1214:    prompt = f"""Tu es le Traducteur Multilingue de LEGA.
1231:                    "model": AGENT_MODEL,
1247:    prompt = f"""Tu es l'Agent Demandes de Prix de LEGA.
1260:                    "model": AGENT_MODEL,
1315:    prompt = f"""Tu es Léa, la standardiste multilingue de LEGA, négociant international en engins de travaux publics (pelleteuses, chargeuses, grues, bulldozers, tracteurs TP d'occasion). LEGA opère entre la France et le Portugal.
1333:                    "model": AGENT_MODEL,
1402:                    "model": AGENT_MODEL,
1546:                    "model": VITRINE_MODEL,
1623:    model = AGENT_MODEL if is_voice else VITRINE_MODEL
1766:    prompt = f"""Tu es l'Agent Site Manager de LEGA. Tu modifies le site vitrine en répondant UNIQUEMENT avec un JSON d'action.
1805:                    "model": AGENT_MODEL,
1886:AGENT_EXECUTORS = {
2009:                executor = AGENT_EXECUTORS.get(agent_name)
```

---
## SCHÉMA BASE DE DONNÉES

### Table: products
```
 id          | integer                     |           | not null | nextval('products_id_seq'::regclass)
 title       | character varying(255)      |           | not null | 
 description | text                        |           |          | 
 price       | numeric(10,2)               |           | not null | 
 currency    | character varying(10)       |           |          | '€'::character varying
 category    | character varying(50)       |           |          | 'tp'::character varying
 status      | character varying(20)       |           |          | 'draft'::character varying
 attributes  | jsonb                       |           |          | '{}'::jsonb
 images      | jsonb                       |           |          | '[]'::jsonb
 promotion   | jsonb                       |           |          | '{}'::jsonb
 created_by  | character varying(100)      |           |          | 'system'::character varying
 created_at  | timestamp without time zone |           |          | now()
 updated_at  | timestamp without time zone |           |          | now()

```

### Table: site_products
```
 id          | uuid                     |           | not null | gen_random_uuid()
 title       | text                     |           | not null | 
 category    | text                     |           |          | 
 brand       | text                     |           |          | 
 model       | text                     |           |          | 
 year        | integer                  |           |          | 
 hours       | integer                  |           |          | 
 price       | numeric(10,2)            |           |          | 
 currency    | text                     |           |          | 'EUR'::text
 location    | text                     |           |          | 
 description | text                     |           |          | 
 specs       | jsonb                    |           |          | 
 images      | jsonb                    |           |          | 
 status      | text                     |           |          | 'available'::text
 source_url  | text                     |           |          | 
 created_at  | timestamp with time zone |           |          | now()
 updated_at  | timestamp with time zone |           |          | now()
 reference   | text                     |           |          | 

```

### Table: search_results
```
 id          | uuid                     |           | not null | gen_random_uuid()
 task_id     | uuid                     |           |          | 
 user_id     | text                     |           |          | 
 title       | text                     |           |          | 
 brand       | text                     |           |          | 
 model       | text                     |           |          | 
 year        | integer                  |           |          | 
 price       | text                     |           |          | 
 description | text                     |           |          | 
 photo_url   | text                     |           |          | 
 source_url  | text                     |           |          | 
 status      | text                     |           |          | 'pending'::text
 created_at  | timestamp with time zone |           |          | now()

```

### Table: tasks
```
 id                    | integer                  |           | not null | nextval('tasks_id_seq'::regclass)
 task_id               | text                     |           | not null | 
 session_id            | text                     |           |          | 
 agent_name            | text                     |           |          | 
 payload               | jsonb                    |           |          | 
 status                | text                     |           |          | 'pending'::text
 language              | text                     |           |          | 'fr'::text
 estimated_latency_sec | integer                  |           |          | 
 actual_latency_sec    | integer                  |           |          | 
 result_json           | jsonb                    |           |          | 
 error_message         | text                     |           |          | 
 created_at            | timestamp with time zone |           |          | now()
 started_at            | timestamp with time zone |           |          | 
 completed_at          | timestamp with time zone |           |          | 

```

### Table: agent_registry
```
 id                | integer                  |           | not null | nextval('agent_registry_id_seq'::regclass)
 name              | text                     |           | not null | 
 display_name      | text                     |           |          | 
 model             | text                     |           |          | 
 capabilities      | text[]                   |           |          | 
 avg_latency_sec   | integer                  |           |          | 
 ram_cost_mb       | integer                  |           |          | 
 status            | text                     |           |          | 'active'::text
 endpoint          | text                     |           |          | 
 is_premium        | boolean                  |           |          | false
 price_monthly_eur | integer                  |           |          | 49
 created_at        | timestamp with time zone |           |          | now()
 updated_at        | timestamp with time zone |           |          | now()

```

### Table: conversation_history
```
 id         | integer                  |           | not null | nextval('conversation_history_id_seq'::regclass)
 user_id    | text                     |           | not null | 
 role       | text                     |           | not null | 
 content    | text                     |           | not null | 
 language   | text                     |           |          | 'fr'::text
 created_at | timestamp with time zone |           |          | now()

```

### Table: site_config
```
 id         | integer                  |           | not null | nextval('site_config_id_seq'::regclass)
 key        | text                     |           | not null | 
 value      | text                     |           |          | 
 value_json | jsonb                    |           |          | 
 updated_at | timestamp with time zone |           |          | now()
 updated_by | text                     |           |          | 'manual'::text

```

### Table: site_sections
```
 id           | integer |           | not null | nextval('site_sections_id_seq'::regclass)
 name         | text    |           | not null | 
 display_name | text    |           |          | 
 position     | integer |           |          | 
 enabled      | boolean |           |          | true
 config       | jsonb   |           |          | 

```

### Table: doc_download_requests
```
 id               | integer                  |           | not null | nextval('doc_download_requests_id_seq'::regclass)
 doc_path         | text                     |           | not null | 
 client_name      | text                     |           | not null | 
 client_email     | text                     |           | not null | 
 client_company   | text                     |           |          | 
 motif            | text                     |           |          | 
 status           | text                     |           |          | 'pending'::text
 download_token   | text                     |           |          | 
 token_expires_at | timestamp with time zone |           |          | 
 created_at       | timestamp with time zone |           |          | now()
 reviewed_at      | timestamp with time zone |           |          | 

```

### Table: user_subscriptions
```
 id               | integer                  |           | not null | nextval('user_subscriptions_id_seq'::regclass)
 user_id          | text                     |           |          | 
 agent_name       | text                     |           |          | 
 status           | text                     |           |          | 
 activated_at     | timestamp with time zone |           |          | 
 trial_expires_at | timestamp with time zone |           |          | 

```

### Table: activation_requests
```
 id           | integer                  |           | not null | nextval('activation_requests_id_seq'::regclass)
 session_id   | text                     |           |          | 
 user_email   | text                     |           |          | 
 agent_name   | text                     |           |          | 
 user_message | text                     |           |          | 
 status       | text                     |           |          | 'pending'::text
 admin_notes  | text                     |           |          | 
 created_at   | timestamp with time zone |           |          | now()
 reviewed_at  | timestamp with time zone |           |          | 

```

### Table: events
```
 id          | uuid                     |           | not null | gen_random_uuid()
 title       | text                     |           | not null | 
 description | text                     |           |          | 
 start_time  | timestamp with time zone |           | not null | 
 end_time    | timestamp with time zone |           |          | 
 location    | text                     |           |          | 
 user_id     | text                     |           |          | 
 attendees   | text[]                   |           |          | 
 remind_at   | timestamp with time zone |           |          | 
 reminded    | boolean                  |           |          | false
 created_at  | timestamp with time zone |           |          | now()

```

### Table: team_availability
```
 id          | integer |           | not null | nextval('team_availability_id_seq'::regclass)
 member_name | text    |           | not null | 
 day_of_week | integer |           |          | 
 start_hour  | integer |           |          | 
 end_hour    | integer |           |          | 
 exceptions  | jsonb   |           |          | 

```

---
## VARIABLES ENVIRONNEMENT

```
# === Identité ===
CLIENT_DOMAIN=client.com
CLIENT_NAME=Ma PME Test

# === DB ===
POSTGRES_USER=bvi_user
POSTGRES_PASSWORD=***
POSTGRES_DB=bvi_db
DATABASE_URL=postgresql://bvi_user:BviSecure2026!@db:5432/bvi_db

# === LLM Local (Ollama) ===
OLLAMA_BASE_URL=http://172.17.0.1:11434

# === LLM Fallback (Alibaba DashScope) ===
DASHSCOPE_API_KEY=***
DASHSCOPE_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1

# === Sécurité ===
JWT_SECRET=***
ADMIN_USER=admin
ADMIN_PASS=***

# === CORS ===
CORS_ORIGINS=["*"]

# === Notifications Telegram ===
# Obtenir le token via @BotFather sur Telegram
# Obtenir le chat_id via @userinfobot ou en lisant les updates du bot
TELEGRAM_BOT_TOKEN=***
TELEGRAM_CHAT_ID=8070870984

# === Mode gestion site ===
# "manual" = dashboard standard, "agent" = modifications automatiques par agents
SITE_MANAGEMENT_MODE=manual
# Clé API pour sécuriser l'endpoint agent (laisser vide = pas de vérification)
AGENT_API_KEY=***

# === Agent Agenda — Brief matinal ===
# Heure d'envoi du brief matinal via Telegram (heure locale serveur UTC)
BRIEF_HOUR=7
BRIEF_MINUTE=0

# === SearXNG (recherche web locale pour agents) ===
SEARXNG_URL=http://bvi-searxng-1:8080

# === TTS / Avatar (hooks évolution future) ===
# TTS_ENABLED=true activera Edge-TTS (fr-FR-DeniseNeural / pt-PT-RaquelNeural / en-GB-SoniaNeural)
TTS_ENABLED=true
# AVATAR_ENABLED=true activera le rendu avatar animé via AIIA (Rhubarb lip-sync)
AVATAR_ENABLED=false
# Endpoint du service AIIA (Edge-TTS + lip-sync) quand déployé
AIIA_ENDPOINT=http://localhost:8003/tts

# === Email SAM COMMS ===
SMTP_FROM=escritorio.ai.lega@gmail.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_PASSWORD=***
```

---
## DOCKER COMPOSE BUREAU IA

```yaml
version: "3.8"

networks:
  bvi-net:
    driver: bridge
    name: bvi_bvi-net

services:
  db:
    image: postgres:16-alpine
    restart: always
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - pg_data:/var/lib/postgresql/data
    networks:
      - bvi-net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 5s
      timeout: 5s
      retries: 5

  api:
    build: ./bvi-api
    restart: always
    ports:
      - "8002:8000"
    environment:
      DATABASE_URL: ${DATABASE_URL}
      OLLAMA_BASE_URL: http://host.docker.internal:11434
      DASHSCOPE_API_KEY: ${DASHSCOPE_API_KEY}
      DASHSCOPE_BASE_URL: ${DASHSCOPE_BASE_URL}
      JWT_SECRET: ${JWT_SECRET}
      LOG_LEVEL: INFO
      TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN:-}
      TELEGRAM_CHAT_ID: ${TELEGRAM_CHAT_ID:-}
      SITE_MANAGEMENT_MODE: ${SITE_MANAGEMENT_MODE:-manual}
      AGENT_API_KEY: ${AGENT_API_KEY:-}
      SEARXNG_URL: ${SEARXNG_URL:-http://bvi-searxng-1:8080}
      SMTP_FROM: ${SMTP_FROM:-}
      SMTP_HOST: ${SMTP_HOST:-smtp.gmail.com}
      SMTP_PORT: ${SMTP_PORT:-587}
      SMTP_PASSWORD: ${SMTP_PASSWORD:-}
      TTS_ENABLED: ${TTS_ENABLED:-false}
      AVATAR_ENABLED: ${AVATAR_ENABLED:-false}
      AIIA_ENDPOINT: ${AIIA_ENDPOINT:-http://localhost:8003/tts}
      BRIEF_HOUR: ${BRIEF_HOUR:-7}
      BRIEF_MINUTE: ${BRIEF_MINUTE:-0}
      ADMIN_USER: ${ADMIN_USER:-admin}
      ADMIN_PASS: ${ADMIN_PASS:-Lega2026!}
    volumes:
      - ./docs:/app/docs:ro
    extra_hosts:
      - "host.docker.internal:host-gateway"
    networks:
      - bvi-net
    depends_on:
      db:
        condition: service_healthy

  dashboard:
    image: node:20-alpine
    restart: always
    ports:
      - "3000:3000"
    working_dir: /app
    command: sh -c "npm install -g pnpm && pnpm install && pnpm run dev"
    volumes:
      - ./bvi-dashboard:/app
      - /app/node_modules
    environment:
      NEXT_PUBLIC_API_URL: http://76.13.141.221:8002/api
      NEXT_PUBLIC_WS_URL: ws://76.13.141.221:8002/ws
      NODE_ENV: development
    networks:
      - bvi-net
    depends_on:
      - api

  shop:
    image: node:20-alpine
    restart: always
    ports:
      - "3001:3000"
    working_dir: /app
    command: sh -c "npm install -g pnpm && pnpm install && pnpm run dev"
    volumes:
      - ./bvi-shop:/app
      - /app/node_modules
    environment:
      NEXT_PUBLIC_API_URL: http://76.13.141.221:8002/api
      NODE_ENV: development
    networks:
      - bvi-net
    depends_on:
      - api

  searxng:
    image: searxng/searxng:2025.2.2-ab1e895cc
    container_name: bvi-searxng-1
    restart: always
    ports:
      - "8888:8080"
    volumes:
      - ./searxng:/etc/searxng:rw
    networks:
      - bvi-net
    environment:
      - SEARXNG_BASE_URL=http://localhost:8888/

volumes:
  pg_data:
```

---
## DOCKER COMPOSE VITRINE

```yaml
networks:
  lega-net:
    driver: bridge
    name: lega_net
  bvi-net:
    external: true
    name: bvi_bvi-net

services:
  lega-backend:
    build: ./backend
    restart: always
    ports:
      - "8003:8000"
    environment:
      DATABASE_URL: postgresql://bvi_user:BviSecure2026!@bvi-db-1:5432/bvi_db
      BVI_API_URL: http://bvi-api-1:8000
      DOCS_BASE_PATH: /app/docs
      SITE_BASE_URL: http://76.13.141.221:8003
      TELEGRAM_BOT_TOKEN: "8651107506:AAHQsRBvh8DpyPq_xBw1_YIcKTE6tdRAeUk"
      TELEGRAM_CHAT_ID: "8070870984"
      SMTP_FROM: escritorio.ai.lega@gmail.com
      SMTP_HOST: smtp.gmail.com
      SMTP_PORT: "587"
      SMTP_PASSWORD: "ojkb iask hwfq itli"
      JWT_SECRET_CLIENT: "lega-client-jwt-2026"
    volumes:
      - ./frontend/public/uploads:/app/uploads
      - /opt/bvi/docs:/app/docs:ro
    networks:
      - lega-net
      - bvi-net

  lega-frontend:
    image: node:20-alpine
    restart: always
    ports:
      - "3002:3000"
    working_dir: /app
    command: sh -c "npm install -g pnpm && pnpm install && pnpm run dev"
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    environment:
      NEXT_PUBLIC_SITE_API_URL: http://76.13.141.221:8003/api/site
      NEXT_PUBLIC_BVI_WS_URL: ws://76.13.141.221:8002/ws/stream
      SITE_API_URL: http://lega-backend:8000
      NODE_ENV: development
    networks:
      - lega-net
    depends_on:
      - lega-backend
```

---
## FRONTEND SHOP port 3001 — EXTRAITS CLÉS

```tsx
42:    tabs: { chat: "💬 Chat", annonces: "📋 Annonces", catalogue: "📦 Catalogue", upload: "📸 Photo" },
79:  const [pendingCount, setPendingCount] = useState(0);
84:  const [thinkingStatus, setThinkingStatus] = useState<"waiting" | "thinking" | "done" | null>(null);
85:  const [thinkingText, setThinkingText] = useState("Tony reçoit votre message...");
101:  const ws = useRef<WebSocket | null>(null);
142:    if (ws.current?.readyState === WebSocket.OPEN) {
143:      ws.current.send(JSON.stringify({ type: "user_message", payload: text, lang: stdLang, preferred_agent: "standardiste" }));
156:  // WebSocket
158:    if (ws.current?.readyState === WebSocket.OPEN) return;
160:    const socket = new WebSocket(`${WS_URL}/stream`);
172:    socket.onmessage = (e) => {
202:        if (d.type === "search_results_ready") {
207:        if (d.type === "thinking") {
208:          setThinkingStatus("thinking");
264:      if (ws.current?.readyState === WebSocket.OPEN) {
265:        ws.current.send(JSON.stringify({ type: "ping", payload: "alive" }));
281:    if (ws.current?.readyState === WebSocket.OPEN) {
282:      ws.current.send(JSON.stringify({ type: "user_message", payload: text, lang }));
294:      const res = await fetch(`${API}/products?status=published&limit=50`);
321:  const publishResult = async (id: string) => {
323:      const res = await fetch(`${API}/search-results/${id}/publish`, { method: "POST" });
333:  const rejectResult = async (id: string) => {
335:      await fetch(`${API}/search-results/${id}/reject`, { method: "POST" });
365:      // Use Tony via websocket with image description prompt
369:      if (ws.current?.readyState === WebSocket.OPEN) {
370:        ws.current.send(JSON.stringify({ type: "user_message", payload: prompt, lang }));
384:        @keyframes tonyPulse { 0%,80%,100%{opacity:0} 40%{opacity:1} }
385:        .tony-dot { display:inline-block; animation:tonyPulse 1.4s infinite; font-size:14px; }
386:        .tony-dot:nth-child(2) { animation-delay:0.2s; }
387:        .tony-dot:nth-child(3) { animation-delay:0.4s; }
388:        .tony-thinking { transition: opacity 0.3s ease; }
389:        .tony-thinking.fade-out { opacity:0; }
429:              {thinkingStatus && (
430:                <div className={`tony-thinking${thinkingStatus === "done" ? " fade-out" : ""}`} style={{ display: "flex", flexDirection: "column", alignItems: "flex-start" }}>
436:                    <span style={{ whiteSpace: "pre-wrap" }}>{thinkingText}</span>
443:                      <span className="tony-dot">●</span>
444:                      <span className="tony-dot">●</span>
445:                      <span className="tony-dot">●</span>
452:            {/* Bouton Annonces Max — visible dans le chat quand il y a des résultats */}
458:                  background: pendingCount > 0 ? "#E8641E" : "#1e293b",
459:                  color: pendingCount > 0 ? "#fff" : "#475569",
465:                <span>📋 Annonces trouvées par Max</span>
466:                {pendingCount > 0 ? (
472:                  }}>{pendingCount}</span>
498:              <span style={{ fontWeight: 700, fontSize: 15 }}>📋 Annonces trouvées par Max</span>
539:                        <button onClick={() => publishResult(r.id)} style={{
543:                        <button onClick={() => rejectResult(r.id)} style={{
714:                  {stdLang === "fr" ? "Léa réfléchit..." : stdLang === "pt" ? "Léa a pensar..." : "Lea is thinking..."}
747:              {id === "annonces" && pendingCount > 0 && (
753:                }}>{pendingCount > 9 ? "9+" : pendingCount}</span>
```

---
## FRONTEND VITRINE port 3002 — EXTRAITS CLÉS

```tsx
80:  const [products, setProducts] = useState<Product[]>([]);
85:  const [hasMore, setHasMore]       = useState(false);
87:  const [chatOpen, setChatOpen]   = useState(false);
88:  const [chatMsgs, setChatMsgs]   = useState<{role:string; text:string; streaming?:boolean}[]>([]);
89:  const [chatInput, setChatInput] = useState("");
95:  const [ws, setWs]               = useState<WebSocket|null>(null);
96:  const [leaStatus, setLeaStatus] = useState<'waiting'|'thinking'|'done'|null>(null);
97:  const [leaThinkText, setLeaThinkText] = useState('');
192:  const fetchProducts = useCallback((offset = 0, append = false) => {
194:    const limit = catFilter ? 999 : PROD_LIMIT;
195:    let url = `${SITE_API}/products?limit=${limit}&offset=${offset}&status=available`;
204:        const nextOffset = offset + items.length;
214:    fr: "Bonjour, je suis Léa. Comment puis-je vous aider ?",
215:    pt: "Olá, sou a Léa. Como posso ajudá-lo?",
216:    en: "Hello, I am Léa. How can I help you?",
217:    es: "Hola, soy Léa. ¿En qué puedo ayudarle?",
218:    de: "Hallo, ich bin Léa. Wie kann ich Ihnen helfen?",
219:    it: "Buongiorno, sono Léa. Come posso aiutarla?",
220:    nl: "Hallo, ik ben Léa. Hoe kan ik u helpen?",
221:    zh: "您好，我是Léa。请问有什么可以帮您？",
226:  // WS chat
228:    if (!chatOpen) {
232:    if (ws?.readyState === WebSocket.OPEN) return;
235:    const socket = new WebSocket(`${BVI_WS}?session_id=${sid}&preferred_agent=standardiste`);
258:          setLeaThinkText("Léa rédige sa réponse...");
282:        // Ignorer le greeting Tony — ce chat affiche uniquement Léa
299:    if (!chatInput.trim()) return;
300:    if (!ws || ws.readyState !== WebSocket.OPEN) { openChat(); return; }
301:    setChatMsgs(prev => [...prev, { role: "user", text: chatInput }]);
302:    ws.send(JSON.stringify({ payload: chatInput, lang, preferred_agent: "lea", canal: "web" }));
345:            {["nav_home","nav_catalogue","nav_contact"].map(k => (
390:          <a href="#catalogue" style={s({
423:      <section id="catalogue" style={s({ maxWidth: 1200, margin: "0 auto", padding: "60px 24px" })}>
425:          {T("nav_catalogue")}
428:          {products.length < total
429:            ? `${products.length} / ${total} annonces`
456:        {products.length === 0 ? (
459:            <p>Chargement du catalogue...</p>
464:              {products.map(p => (
469:            {hasMore && (
474:                  {T("load_more") || "Charger plus"} ({total - products.length})
599:      {!chatOpen && (
608:      {chatOpen && (
617:            <span style={s({ fontWeight: 700, fontSize: 14 })}>Léa — LEGA.PT</span>
632:            {chatMsgs.length === 0 && (
634:                {T("ai_chat_placeholder")}
637:            {chatMsgs.map((m, i) => (
648:          {/* ── Indicateur Léa ── */}
650:            @keyframes lea-dot{0%,80%,100%{opacity:.2;transform:scale(.8)}40%{opacity:1;transform:scale(1)}}
651:            @keyframes lea-spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
652:            @keyframes lea-fade{from{opacity:1}to{opacity:0}}
653:            .lea-dot{display:inline-block;width:6px;height:6px;border-radius:50%;background:#E8641E;margin:0 2px;animation:lea-dot 1.4s ease-in-out infinite}
654:            .lea-dot:nth-child(2){animation-delay:.2s}.lea-dot:nth-child(3){animation-delay:.4s}
655:            .lea-spin{display:inline-block;animation:lea-spin 1s linear infinite}
656:            .lea-fade{animation:lea-fade 350ms ease forwards}
658:          {leaStatus && (
659:            <div className={leaStatus === "done" ? "lea-fade" : ""}
663:              {leaStatus === "waiting" ? (
665:                  <span className="lea-dot"/><span className="lea-dot"/><span className="lea-dot"/>
666:                  <span style={s({marginLeft:4})}>Léa reçoit votre message...</span>
```

---

## COMMENT UTILISER CE FICHIER AVEC QWEN 3.6 PLUS

1. Copier tout ce fichier
2. Ouvrir Qwen 3.6 Plus
3. Coller le contenu comme premier message
4. Ajouter à la fin : "Voici ma question : [ta question]"

Qwen a alors tout le contexte pour t'aider à développer,
débugger ou améliorer le projet sans accès au VPS.

## RÈGLES ABSOLUES À RAPPELER À L'ASSISTANT
1. site_manager : activation MANUELLE Antoine UNIQUEMENT
2. sam_comms : jamais envoyer email sans confirmation
3. knowledge_base.json : READ ONLY
4. Ollama : un seul modèle à la fois
5. Tony : gemma2 pour ack rapide, gemma4 pour traitement
6. Frontends Next.js : hot-reload, pas de rebuild
