# BRIEFING SESSION 3 — Projet Bureau IA / LEGA-BVI
**Date prévue** : prochaine session
**VPS** : srv1332127 — 76.13.141.221
**Statut entrant** : Session 2 complète ✅

---

## Checklist départ

```bash
docker ps                                          # tous les containers up ?
curl http://localhost:8002/api/health              # API OK ?
docker network connect bvi_bvi-net bvi-api-1      # si nécessaire
curl http://localhost:8888/healthz                 # SearXNG OK ?
```

---

## Ordre de développement Session 3

### 1. Sam Comms — SMTP Gmail ⚠️ MOT DE PASSE REQUIS
**Demander à Antoine** : mot de passe app Gmail pour `escritorio.ai.lega@gmail.com`
(Compte Gmail → Sécurité → Mots de passe des applications)

Une fois obtenu :
- Ajouter `SMTP_PASSWORD=xxx` dans `.env`
- Implémenter `send_email(to, subject, body)` dans `web_utils.py` via `aiosmtplib`
- `run_sam_comms()` : email envoyé si SMTP configuré, sinon retourne le texte seul
- Dashboard : afficher statut envoi dans les tâches Sam

### 2. JWT Dashboard admin
- Variables `.env` : `ADMIN_USER`, `ADMIN_PASS` (hash bcrypt)
- `POST /api/auth/login` → retourne JWT HS256 (24h)
- Middleware FastAPI `verify_jwt` sur toutes routes `/api/*` sauf `/api/health` et `/ws/stream`
- Dashboard Next.js : page `/login`, localStorage JWT, redirect 401 → `/login`

### 3. Tony — routing vers agent Documentation
Ajouter intent `documentation_search` dans `TONY_SYSTEM` :
- Déclencheurs : "fiche technique", "gabarit", "poids", "prix marché", "transport", "douane", "CE", "homologation"
- Routing → agent `documentation`
- Enrichir aussi `docs/` : fiches constructeurs CAT/Volvo/Komatsu, prix marché 2026

### 4. Enrichir la base docs/
Créer les fichiers manquants :
- `docs/constructeurs/caterpillar.md`
- `docs/constructeurs/volvo.md`
- `docs/prix/marche_2026.md`
- `docs/reglementation/portugal.md`

### 5. Traefik conflit
- Désactiver `traefik-c9es-traefik-1` depuis l'interface **Coolify** (pas CLI)
- Le `coolify-proxy` gère déjà ports 80/443

### 6. Confirmer second VPS avec Antoine
- Y a-t-il un second VPS ? Si oui, IP et usage prévu ?

---

## État infrastructure au départ Session 3

| Service | Port | Statut |
|---|---|---|
| bvi-api | 8002 | ✅ up |
| bvi-dashboard | 3000 | ✅ up |
| bvi-shop | 3001 | ✅ up (widget Standardiste Léa) |
| bvi-db | 5432 | ✅ healthy |
| SearXNG | 8888 | ✅ up (Mojeek+Wikipedia) |
| Traefik | — | ⚠️ restarting (conflit coolify-proxy) |

## Agents en DB (12 total)

| Agent | Premium | Implémenté |
|---|---|---|
| tony_interface | non | ✅ |
| standardiste | non | ✅ |
| agenda | non | ✅ cron brief |
| max_search | oui | ✅ |
| lea_extract | oui | enregistré |
| visa_vision | oui | enregistré |
| documentation | oui | ✅ RAG |
| comptable | oui | enregistré |
| traducteur | oui | enregistré |
| logistique | oui | enregistré |
| demandes_prix | oui | enregistré |
| sam_comms | non | ✅ (sans SMTP) |

## Rappels techniques

- Rebuild API : `docker compose up -d --build api` + `docker network connect bvi_bvi-net bvi-api-1`
- Brief manuel : `curl -X POST http://localhost:8002/api/agenda/brief-now`
- RAG reindex : redémarrer l'API (build_rag_index au startup)
- SearXNG test : `curl "http://localhost:8888/search?q=pelleteuse&format=json"`
- DB : `docker exec bvi-db-1 psql -U bvi_user -d bvi_db`
- Push GitHub : `git push origin main`
