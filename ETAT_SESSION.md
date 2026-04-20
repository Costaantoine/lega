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
