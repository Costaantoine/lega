# BRIEFING — Refonte système d'activation agents (2026-04-24)

## Ce qui a changé

### Architecture agents — nouvelle logique d'accès

**Avant** : les agents premium se déverrouillaient automatiquement avec un trial 24h à la première utilisation.

**Après** : tous les agents sont **verrouillés par défaut**. L'activation est manuelle, via le dashboard admin avec le code `191070`.

---

## Les 3 agents toujours gratuits (jamais bloqués)

| Agent | Rôle |
|---|---|
| **Tony** (`tony_interface`) | Orchestre tous les agents, routing, accueil, general_chat |
| **Léa** (`lea` / `standardiste`) | Standardiste vitrine lega.pt — répond aux clients sur le catalogue, peut escalader vers Tony |
| **Agenda** (`agenda`) | Gestion planning, brief matinal Telegram 7h00 |

---

## Les 9 agents verrouillés (activation requise)

| Agent | Rôle |
|---|---|
| `max_search` | Recherche machines TP, prix marché |
| `sam_comms` | Emails professionnels B2B *(était gratuit — maintenant verrouillé)* |
| `lea_extract` | Extraction specs HTML |
| `visa_vision` | Analyse photos / OCR |
| `logistique` | Transport France↔Portugal |
| `comptable` | Devis & factures TVA FR/PT |
| `traducteur` | Traduction FR/PT/EN/ES/DE/IT |
| `demandes_prix` | Demandes prix fournisseurs |
| `documentation` | RAG technique /docs/ *(était gratuit — maintenant verrouillé)* |

`site_manager` reste admin-only (garde séparée, non activable via code client).

---

## Nouveau comportement quand un agent est demandé sans accès

1. Tony renvoie un message de type `status: "locked"` dans la langue du client
2. Une `activation_request` avec `status='pending'` est créée en DB (sans doublon)
3. Notification Telegram admin avec session_id + agent + message original
4. Le client voit : *"Votre demande a été transmise à notre équipe. Vous serez notifié dès que l'accès est accordé."*

---

## Dashboard — Page Activations (port 3000)

### Nouveau panneau "Activation client (code 191070)"

Bouton dépliable en haut de la page Activations. Permet :
- Saisir un `session_id` (copiable depuis les demandes en attente ci-dessous)
- Entrer le code `191070`
- Choisir le mode :
  - **Client** → accès actif 30 jours
  - **Premium** → accès permanent (pas d'expiration)
- Choisir les agents : "Tous" ou sélection manuelle
- Cliquer **Activer** → notification WS live si le client est connecté

### Sur chaque demande pending

Directement sur la carte de demande : champ code + mode + bouton **Activer**, plus bouton **Rejeter**.

Le `session_id` est affiché et cliquable pour copier.

---

## Léa → Tony (escalade)

`run_lea_streaming` retourne maintenant un `bool`. Si Léa dit "Je vous passe Tony" / "Je transfère" dans sa réponse, le handler WS appelle automatiquement `tony_dispatch` en arrière-plan. Le client reçoit d'abord la réponse de Léa, puis Tony prend le relais.

---

## Fichiers modifiés

- `/opt/bvi/bvi-api/main.py` — constantes PREMIUM_AGENTS, logique verrouillage, endpoint POST `/api/admin/activate-client`, escalade Léa→Tony
- `/opt/bvi/bvi-dashboard/app/components/ActivationsPage.tsx` — panneau activation + actions rapides sur demandes pending

## DB

- `sam_comms` : `is_premium` passé à `true` dans `agent_registry`
- Aucune migration de schéma requise (tables existantes suffisent)

## Containers

- `bvi-api-1` : rebuild complet ✅
- `bvi-dashboard-1` : restart ✅

---

## Points d'attention pour la session de test en cours

- **Plus de trial automatique** — si des tests supposaient un auto-trial 24h, ils recevront maintenant un message `status: "locked"`
- **sam_comms et documentation** sont maintenant verrouillés (étaient gratuits avant)
- Le code `191070` est nécessaire pour activer depuis le dashboard
- `site_manager` n'est pas dans PREMIUM_AGENTS — il garde sa propre gate admin-only
