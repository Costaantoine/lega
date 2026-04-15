# BRIEFING SESSION 2 — Projet Bureau IA / LEGA-BVI

## CORRECTIONS PRIORITAIRES

1. Swap Sam ↔ Léa en DB :
UPDATE agent_registry SET is_premium = false WHERE name = 'sam_comms';
UPDATE agent_registry SET is_premium = true WHERE name = 'lea_extract';

2. Fix réseau Docker permanent dans docker-compose.yml (bvi-api-1 perd son réseau au restart)

3. Ajouter dans .env et main.py :
TTS_ENABLED=false
AVATAR_ENABLED=false
AIIA_ENDPOINT=http://localhost:8003/tts
(hooks pour évolution future avatar animé — Tony ET Standardiste)

4. Installer SearXNG sur le VPS en Docker pour donner accès web à tous les agents :
- Gemma2:2b (Tony) et Gemma4 ne se connectent PAS directement au web
- Le Python fait la recherche via SearXNG, injecte les résultats dans le prompt
- Brancher sur : brief matinal, agent veille, agent recherche, Tony si question sur actualité

## NOUVEAUX AGENTS À AJOUTER EN DB

INSERT INTO agent_registry (name, display_name, model, capabilities, avg_latency_sec, ram_cost_mb, is_premium) VALUES
('standardiste', 'Standardiste Multilingue', 'gemma4:e2b', ARRAY['detection_langue','reponse_client','consultation_catalogue','consultation_rag','reponse_vocale','transfert_agent'], 10, 7200, false),
('agenda', 'Agent Agenda', 'gemma2:2b', ARRAY['planification','gestion_rdv','detection_conflits','rappel_automatique','proposition_creneaux','vocal_agenda','optimisation_tournee'], 2, 1600, false),
('comptable', 'Secrétaire Comptable', 'gemma4:e2b', ARRAY['generation_devis','generation_facture','bon_transport','avoir','relance_client','conformite_fiscale'], 90, 7200, true),
('documentation', 'Agent Documentation Technique', 'gemma4:e2b', ARRAY['recherche_documentation','classement_rag','indexation_manuel','recherche_par_machine'], 120, 7200, true),
('traducteur', 'Traducteur Multilingue', 'gemma4:e2b', ARRAY['traduction_document','preservation_mise_en_page','ajout_logo_client','traduction_technique'], 120, 7200, true),
('logistique', 'Agent Logistique', 'gemma4:e2b', ARRAY['estimation_transport','calcul_logistique','frais_bateau','frais_gardiennage','calcul_grue'], 90, 7200, true),
('demandes_prix', 'Agent Demandes de Prix', 'gemma4:e2b', ARRAY['demande_prix_transport','demande_prix_grue','contact_fournisseur','comparaison_offres','mise_a_jour_tarifs'], 90, 7200, true);

## VOIX VOCALE TONY ET STANDARDISTE (Edge-TTS)

- Voix FR : fr-FR-DeniseNeural
- Voix PT-PT : pt-PT-RaquelNeural
- Voix EN : en-GB-SoniaNeural
- Langue TOUJOURS adaptée à l'interlocuteur
- Fonction text_to_speech(text, lang) dans main.py
- Activée par TTS_ENABLED=true
- Audio base64 envoyé via WebSocket
- Bouton 🔊 sur frontend port 3001
- Compatible PC et mobile

## AGENT AGENDA — RÉVOLUTIONNAIRE

LEGA = négociant achat/vente engins TP (PAS de chantier)
Brief matinal via Telegram chaque matin (heure configurable) :
- Vocal (Edge-TTS) + texte
- Langue adaptée à l'utilisateur
- Planning du jour
- Opportunités marché (nouvelles annonces qui matchent les recherches)
- Suivi clients (sans réponse depuis X jours + meilleur moment pour appeler)
- Transports en cours
- Météo UNIQUEMENT si pertinent pour transport ou visite machine
- Si l'utilisateur veut plus de météo → il demande à Tony

TOUT EST DÉSACTIVABLE PAR TONY À LA VOIX :
"Tony, arrête les suggestions automatiques" → Tony désactive et propose de garder certaines options

Ajouter colonne preferences JSONB dans table users :
ALTER TABLE users ADD COLUMN IF NOT EXISTS preferences JSONB DEFAULT '{
  "suggestions_creneaux": true,
  "alertes_prix_marche": true,
  "alertes_opportunites": true,
  "brief_meteo": true,
  "brief_livraisons": true,
  "brief_enabled": true,
  "brief_time": "07:00",
  "optimisation_tournee": true
}';

ALTER TABLE users ADD COLUMN IF NOT EXISTS brief_time TIME DEFAULT '07:00';
ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_chat_id TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS role_type TEXT DEFAULT 'owner';

Nouvelles tables agenda :
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    location TEXT,
    user_id TEXT,
    attendees TEXT[],
    remind_at TIMESTAMPTZ,
    reminded BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS team_availability (
    id SERIAL PRIMARY KEY,
    member_name TEXT NOT NULL,
    day_of_week INTEGER,
    start_hour INTEGER,
    end_hour INTEGER,
    exceptions JSONB
);

## EMAIL SAM COMMS

Adresse : escritorio.ai.lega@gmail.com
⚠️ Demander le mot de passe Gmail à Antoine AVANT de configurer
Variables dans .env :
SMTP_FROM=escritorio.ai.lega@gmail.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_PASSWORD=À_DEMANDER_À_ANTOINE

## VÉRIFICATION DEUX VPS

Un seul VPS trouvé au scan (76.13.141.221). 
Demander à Antoine : y a-t-il un second VPS et quelle est son IP ?

## TRAEFIK EN ERREUR

Traefik est en état "Restarting" — diagnostiquer et corriger.
docker logs traefik --tail=50

## ORDRE DE DÉVELOPPEMENT

1. Corrections DB (swap Sam/Léa + nouvelles tables)
2. Fix Docker réseau + Traefik
3. SearXNG installation Docker
4. Hooks TTS dans .env et main.py
5. Widget Standardiste sur port 3001 (chat écrit d'abord)
6. Brief matinal Agenda via Telegram
7. Agent Documentation + structure RAG /opt/bvi/docs/
8. Demander mot de passe Gmail avant configurer Sam Comms
9. Commit et push après chaque étape

## ARCHITECTURE AVATAR — PRINCIPE FONDAMENTAL

Tout le code doit être prévu pour évoluer vers avatar animé parlant.
Compatible projet AIIA existant (Edge-TTS + Rhubarb lip-sync).
TTS_ENABLED=false aujourd'hui → true demain → avatar après-demain.
Tony ET Standardiste auront un avatar à terme.

Commence maintenant dans cet ordre. Commit et push après chaque étape terminée et testée.
