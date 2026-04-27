# État Session — 2026-04-27

## Ce qui a été fait cette session

### Fix Tony classify docstring
- L313 main.py : docstring corrigé (gemma4:e2b → gemma2:2b via TONY_MODEL)
- Confirmé : TONY_MODEL = "gemma2:2b" depuis le MVP

### Tests Léa (WS /ws/stream) — Score 9/10
- TEST1 Accueil : PASS (2.74s)
- TEST2 Pelles en stock : WARN (ACK 3.1s, contenu OK)
- TEST3 Réparations : WARN (ACK 15.4s — swap Ollama)
- TEST4 Redirect docs : PASS (0.07s, no LLM)

### Tests Tony routing — Score 7/10 → 8/10 après fixes
FIX 1 — sam_comms : ajout _sam_kw dans fallback (main.py L457)
FIX 2 — comptable : ajout "fais un devis","fais moi un devis" dans _comptable_kw (L439)
FIX 3 — general_chat timeout : 40s → 15s + try/except ws.send_json (L630)
Résiduel TEST5 : classify fail (~15s) + gchat (~15s) = 30s race — fix restant = skip LLM si direct_response déjà set

### BUG B — Modale activation premium
- ActivationsPage.tsx : bouton "⚡ Activer" → slide-down mini-modale
- autoFocus sur champ code, Enter pour confirmer, bouton Annuler
- showActModal state par id de demande

### BUG A — SearXNG hors sujet
- web_utils.py : mojeek → google, filtre TLD whitelist (.fr/.pt/.es/.de/.be/.ch/.com/.net/.org/.eu/.uk)
- main.py : query += ' excavateur engin TP annonce avec photo'
- LIMITE : Bing via SearXNG retourne "pelle jardinage" en cache — pipeline search_smart (scraping direct) reste le bon path pour annonces TP

## Tâches restantes

P0 — FIX TEST5 Tony : dans handle_general_chat, si classification.get("direct_response") → servir direct sans appel AGENT_MODEL
P1 — SearXNG : tester engines=google seul ou DuckDuckGo pour éviter cache Bing jardinage
P1 — Léa RAG docs : brancher /app/docs/ dans run_lea_streaming() canal=web
P2 — Bug catalogue vitrine 66 annonces : vérifier limit frontend port 3002
P2 — Dashboard Demandes docs port 3000
P2 — SSL lega.pt : désactiver traefik dans Coolify avant

## Fichiers modifiés
- /opt/bvi/bvi-api/main.py (classify docstring, sam_kw, comptable_kw, gchat timeout, query TP)
- /opt/bvi/bvi-api/web_utils.py (TLD filter, TP_DOMAINS log, engines, locale)
- /opt/bvi/bvi-dashboard/app/components/ActivationsPage.tsx (showActModal slide-down)
