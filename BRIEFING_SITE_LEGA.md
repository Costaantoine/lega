# BRIEFING SITE VITRINE — LEGA.PT

## OBJECTIF
Créer le nouveau site vitrine de TOB Trading sur le domaine lega.pt
Remplacement de tob.pt — moderne, IA intégrée, 8 langues, CMS 100% paramétrable.
Architecture multi-clients : réutilisable pour n'importe quel secteur/client.

## INFORMATIONS CLIENT
Nom          : TOB Trading, Lda. — affiché "LEGA Trading"
Domaine      : lega.pt
Téléphone    : 00351 912 406 089
Email        : escritorio.ai.lega@gmail.com
Adresse      : Rua Santo António, 120 — 4770-082 Cabeçudos, Vila Nova de Famalicão, Portugal
NIF          : PT 510 245 447
Horaires     : Lundi–Samedi 07h00–19h00
Logo         : /opt/lega-site/public/logo_vector.pdf
Couleur 1    : #1B3F6E (bleu marine)
Couleur 2    : #E8641E (orange)

## ARCHITECTURE
/opt/lega-site/
├── frontend/    ← Next.js 14 + TypeScript (port 3002)
│   ├── app/     ← Pages publiques vitrine
│   ├── locales/ ← Traductions JSON par langue
│   └── public/  ← Logo, images, uploads
├── backend/     ← FastAPI (port 8003)
└── docker-compose.yml

Base de données : utiliser bvi-db-1 existant — ajouter tables site_* dedans.

## DESIGN
Style : professionnel industriel — bleu marine + orange
Hero : grande photo réelle d'engin (Unsplash pour le MVP)
Pas de texte tape-à-l'oeil — photos professionnelles qui parlent
Navbar sombre + stats orange + grille cards produits
Widget chat flottant orange en bas à droite

## LANGUES — 8 actives dès le MVP
PT-PT · FR · EN · ES · DE · IT · RU · AR (RTL pour l'arabe)
Système i18n : fichiers JSON par langue dans /frontend/locales/
Zéro texte hardcodé — tout passe par les clés de traduction.

## CATÉGORIES PRODUITS
Machines TP · Camions · Semi-remorques · Vans
Sous-catégories configurables depuis le CMS.

## FONCTIONNALITÉS

### Frontend vitrine (port 3002)
- Page d'accueil : Hero + stats + recherche + catalogue
- Catalogue avec filtres : catégorie, prix, année, statut
- Page détail produit : photos, specs, prix, bouton devis
- Formulaire contact + demande de devis en ligne
- Chat Standardiste IA (widget flottant connecté Bureau IA port 8002)
- Sélecteur 8 langues dans la navbar
- Support RTL pour l'arabe
- Responsive : PC, tablette, smartphone

### Backend CMS — TOUT PARAMÉTRABLE SANS TOUCHER AU CODE
Modifiable manuellement ET par Tony (agent site_manager quand activé)

Identité & coordonnées : nom, slogan par langue, téléphone, email, adresse, logo
Apparence : couleur principale + secondaire, police, image hero
Sections : ordre glisser-déposer, activer/désactiver, chiffres clés
Langues : activer/désactiver, traductions par clé
Catalogue : CRUD produits, upload photos, statuts

## AGENT GESTIONNAIRE SITE
name         : site_manager
is_premium   : true — ACTIVATION MANUELLE ANTOINE UNIQUEMENT
price        : 49€/mois
model        : gemma4:e2b
capabilities : modifier_textes, changer_couleurs, update_coordonnees,
               activer_sections, modifier_traductions, update_catalogue

RÈGLES ABSOLUES :
- Agent PREMIUM — jamais de trial automatique
- Antoine valide manuellement depuis le dashboard
- Tant qu'inactif → CMS 100% manuel uniquement
- Chaque modification → log d'audit (qui, quand, quoi)
- Ne peut PAS supprimer — seulement archiver
- Demande confirmation avant changements visuels majeurs

## TABLES DB À CRÉER dans bvi-db-1

CREATE TABLE site_config (
    id SERIAL PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    value TEXT,
    value_json JSONB,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by TEXT DEFAULT 'manual'
);

CREATE TABLE site_translations (
    id SERIAL PRIMARY KEY,
    lang TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(lang, key)
);

CREATE TABLE site_sections (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    display_name TEXT,
    position INTEGER,
    enabled BOOLEAN DEFAULT true,
    config JSONB
);

CREATE TABLE site_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    category TEXT,
    brand TEXT,
    model TEXT,
    year INTEGER,
    hours INTEGER,
    price NUMERIC(10,2),
    currency TEXT DEFAULT 'EUR',
    location TEXT,
    description TEXT,
    specs JSONB,
    images JSONB,
    status TEXT DEFAULT 'available'
        CHECK (status IN ('available','sold','reserved','new','archived')),
    source_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE site_audit_log (
    id SERIAL PRIMARY KEY,
    action TEXT NOT NULL,
    field TEXT,
    old_value TEXT,
    new_value TEXT,
    done_by TEXT DEFAULT 'manual',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO site_config (key, value) VALUES
('site_name',       'LEGA Trading'),
('slogan_fr',       'Équipements qui font bouger le monde'),
('slogan_pt',       'Equipamentos que movem o mundo'),
('slogan_en',       'Equipment that moves the world'),
('phone',           '00351 912 406 089'),
('email',           'escritorio.ai.lega@gmail.com'),
('address',         'Rua Santo António, 120 — Vila Nova de Famalicão, Portugal'),
('color_primary',   '#1B3F6E'),
('color_secondary', '#E8641E'),
('font',            'Inter'),
('stat_machines',   '400+'),
('stat_langues',    '8'),
('stat_pays',       '15+'),
('stat_support',    '24/7');

INSERT INTO site_sections (name, display_name, position, enabled) VALUES
('hero',      'Hero + image principale', 1, true),
('stats',     'Barre de statistiques',   2, true),
('search',    'Recherche rapide',        3, true),
('catalogue', 'Catalogue produits',      4, true),
('ai_banner', 'Bandeau assistante IA',   5, true),
('contact',   'Formulaire de contact',   6, true),
('footer',    'Pied de page',            7, true);

INSERT INTO agent_registry
  (name, display_name, model, capabilities, avg_latency_sec, ram_cost_mb, is_premium, price_monthly_eur)
VALUES
  ('site_manager', 'Gestionnaire Site Web', 'gemma4:e2b',
   ARRAY['modifier_textes','changer_couleurs','update_coordonnees',
         'activer_sections','modifier_traductions','update_catalogue'],
   30, 7200, true, 49)
ON CONFLICT (name) DO NOTHING;

## IMPORT TOB.PT (étape 4)
Script /opt/lega-site/backend/import_tobpt.py :
1. Scraper machinery.aspx, truck.aspx, trailertruck.aspx, vans.aspx
2. Récupérer : titre, marque, modèle, année, photos, statut
3. Télécharger photos dans /public/uploads/
4. INSERT dans site_products avec source_url = URL tob.pt
5. À lancer une seule fois au déploiement

## ORDRE DE DÉVELOPPEMENT
ÉTAPE 1 : Infrastructure Docker /opt/lega-site/ + ports 3002/8003 + tables DB
ÉTAPE 2 : Frontend vitrine (8 langues, RTL, responsive)
ÉTAPE 3 : Backend CMS (couleurs, sections, logo, textes)
ÉTAPE 4 : Import tob.pt
ÉTAPE 5 : Agent site_manager (premium, jamais de trial)
ÉTAPE 6 : Tests finaux

Travaille dans /opt/lega-site/ et push sur https://github.com/Costaantoine/lega-vitrine
PAS sur le repo lega principal.
Commit après chaque étape terminée et testée.
Commence maintenant par l'étape 1.
