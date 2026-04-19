import asyncpg
import asyncio
import json
import logging
import os
import re
import smtplib
import time
import uuid
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import aiofiles
import httpx
import jwt
import web_utils
from fastapi import Depends, FastAPI, File, HTTPException, Security, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_URL = os.getenv("DATABASE_URL", "postgresql://bvi_user:BviSecure2026!@bvi-db:5432/bvi_db")
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://172.17.0.1:11434")
TONY_MODEL = "gemma2:2b"
AGENT_MODEL = "gemma4:e2b"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

SMTP_FROM = os.getenv("SMTP_FROM", "")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

# Agents nécessitant un abonnement
PREMIUM_AGENTS = {"max_search", "lea_extract", "visa_vision", "logistique", "comptable", "traducteur", "demandes_prix"}

# Mode gestion site : "agent" (automatique) ou "manual" (dashboard)
SITE_MANAGEMENT_MODE = os.getenv("SITE_MANAGEMENT_MODE", "manual")
AGENT_API_KEY = os.getenv("AGENT_API_KEY", "")

# URL backend vitrine (pour site_manager)
LEGA_SITE_API = os.getenv("LEGA_SITE_API_URL", "http://lega-site-lega-backend-1:8000/api/site")

# JWT Auth dashboard
JWT_SECRET = os.getenv("JWT_SECRET", "changeme-secret-key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin")

security_bearer = HTTPBearer(auto_error=False)

def create_jwt_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Security(security_bearer)) -> str:
    if not credentials:
        raise HTTPException(status_code=401, detail="Token manquant")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalide")

# TTS / Avatar — hooks pour évolution future (Edge-TTS + Rhubarb lip-sync)
# TTS_ENABLED=true  → text_to_speech(text, lang) active, audio base64 envoyé via WS
# AVATAR_ENABLED=true → rendu avatar animé via AIIA endpoint
TTS_ENABLED = os.getenv("TTS_ENABLED", "false").lower() == "true"
AVATAR_ENABLED = os.getenv("AVATAR_ENABLED", "false").lower() == "true"
AIIA_ENDPOINT = os.getenv("AIIA_ENDPOINT", "http://localhost:8003/tts")

VITRINE_MODEL = "gemma2:2b"
TTS_VOICES: dict[str, str] = {
    "fr": "fr-FR-DeniseNeural",
    "pt": "pt-PT-RaquelNeural",
    "en": "en-GB-SoniaNeural",
    "es": "es-ES-ElviraNeural",
    "de": "de-DE-KatjaNeural",
    "it": "it-IT-ElsaNeural",
    "ar": "ar-SA-ZariyahNeural",
    "ru": "ru-RU-SvetlanaNeural",
}

# Brouillons Sam en attente de confirmation (en mémoire, TTL ~30min via cron)
sam_pending: dict[str, dict] = {}

app = FastAPI(title="LEGA/BVI API", version="1.0.0")
app.mount("/uploads", StaticFiles(directory="/app/uploads"), name="uploads")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active WebSocket connections: {session_id: WebSocket}
active_connections: dict[str, WebSocket] = {}


# ── Pydantic models ──────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    title: str
    description: str
    price: float
    currency: str = "€"
    category: str = "tp"
    attributes: dict = {}
    images: list = []
    status: str = "draft"

class ProductUpdate(BaseModel):
    title: str = None
    description: str = None
    price: float = None
    currency: str = None
    category: str = None
    attributes: dict = None
    images: list = None
    status: str = None

class AgentSiteAction(BaseModel):
    action: str          # create | update | delete | publish | unpublish
    product_id: int = None
    data: dict = {}      # champs produit pour create/update
    reason: str = ""     # justification de l'action (pour logs)
    agent_name: str = "" # agent émetteur


# ── Tony prompt ──────────────────────────────────────────────────────────────

TONY_SYSTEM = """Respond ONLY with valid JSON. No text before or after.

Detect language from these signals:
- Portuguese words (escavadora, encontra, procura, máquina, abaixo, euros, quero, olá, bom dia) → lang=pt
- English words (excavator, find, search, machine, under, price, hello, good morning) → lang=en
- Spanish words (hola, buenos dias, buenas, máquina, excavadora, busca) → lang=es
- French words (pelleteuse, trouve, cherche, bonjour, devis, quel, temps, demain) → lang=fr

JSON format:
{"intent":"machine_search|email_followup|image_analysis|documentation_search|modifier_site|watch_request|logistique|comptable|traducteur|demandes_prix|general_chat","lang":"fr|pt|en|es","agent":"max_search|sam_comms|visa_vision|documentation|site_manager|logistique|comptable|traducteur|demandes_prix|null","ack_message":"short ack IN DETECTED LANGUAGE or null","estimated_delay":"string or null","direct_response":"full reply IN DETECTED LANGUAGE if general_chat, else null"}

Rules:
- machine_search (pelleteuse/escavadora/excavator/excavatrice/excavadora/grue/tracteur/bulldozer/dumper/tombereau/nacelle/chariot/elevateur/compacteur/niveleuse) → agent=max_search
- email_followup (email/devis/relancer/contactar) → agent=sam_comms
- image_analysis (photo/image/analyser) → agent=visa_vision
- documentation_search (fiche technique/ficha técnica/technical spec/certificat CE/douane/customs/transport/poids/dimensions/prix marché/documentation) → agent=documentation
- modifier_site (changer slogan/couleur/téléphone/adresse/logo/section/modifier le site/atualizar site/ajouter produit/modifier produit) → agent=site_manager
- logistique (transport/logistique/livraison/devis transport/fret/bateau/camion plateau/grue chargement) → agent=logistique
- comptable (devis/facture/bon de commande/comptabilité/paiement/TVA/avoir/relance paiement) → agent=comptable
- traducteur (traduis/traduire/translation/tradução/en portugais/en français/en anglais) → agent=traducteur
- demandes_prix (demande de prix/prix fournisseur/tarif transporteur/combien coûte/quel prix/prix grue) → agent=demandes_prix
- general_chat → agent=null, direct_response MUST be a helpful answer IN DETECTED LANGUAGE
- NEVER use direct_response to repeat a greeting or introduction — give a real answer
- For off-topic questions (météo, etc.): redirect politely and suggest an alternative
- For questions about internet/web access: answer honestly about SearXNG access

Examples:
"Trouve-moi une pelleteuse 10T moins de 10000 euros" → {"intent":"machine_search","lang":"fr","agent":"max_search","ack_message":"Je recherche une pelleteuse 10T sous 10 000€...","estimated_delay":"2-4 minutes","direct_response":null}
"Encontra-me uma escavadora 10T abaixo de 10000 euros" → {"intent":"machine_search","lang":"pt","agent":"max_search","ack_message":"A pesquisar escavadora 10T abaixo de 10 000€...","estimated_delay":"2-4 minutos","direct_response":null}
"Find me a 10T excavator under 10000 euros" → {"intent":"machine_search","lang":"en","agent":"max_search","ack_message":"Searching for a 10T excavator under €10,000...","estimated_delay":"2-4 minutes","direct_response":null}
"Bonjour que peux-tu faire" → {"intent":"general_chat","lang":"fr","agent":null,"ack_message":null,"estimated_delay":null,"direct_response":"Je peux rechercher des machines TP (pelleteuses, grues, chargeuses), rédiger des emails professionnels, estimer des prix et surveiller le marché. Posez votre question."}
"Olá o que fazes?" → {"intent":"general_chat","lang":"pt","agent":null,"ack_message":null,"estimated_delay":null,"direct_response":"Pesquiso máquinas TP, redijo e-mails profissionais, estimo preços e monitorizo o mercado. Qual é a sua questão?"}
"quel temps fait-il demain ?" → {"intent":"general_chat","lang":"fr","agent":null,"ack_message":null,"estimated_delay":null,"direct_response":"Je suis spécialisé dans les machines TP. Pour la météo, consultez météo.fr ou weather.com."}
"what will the weather be tomorrow?" → {"intent":"general_chat","lang":"en","agent":null,"ack_message":null,"estimated_delay":null,"direct_response":"I specialize in construction machinery. For weather forecasts, check weather.com or your local service."}
"tu as accès à internet ?" → {"intent":"general_chat","lang":"fr","agent":null,"ack_message":null,"estimated_delay":null,"direct_response":"Oui, j'ai accès à SearXNG pour rechercher des annonces de machines TP en temps réel. Donnez-moi vos critères."}
"tu n'as pas un agent qui se connecte au web" → {"intent":"general_chat","lang":"fr","agent":null,"ack_message":null,"estimated_delay":null,"direct_response":"Si, j'utilise SearXNG pour trouver des annonces machines en temps réel. Donnez-moi vos critères de recherche."}
"buenas dias" → {"intent":"general_chat","lang":"es","agent":null,"ack_message":null,"estimated_delay":null,"direct_response":"Buenos días. Busco maquinaria de construcción (excavadoras, grúas, cargadoras), redacto correos y analizo precios. ¿En qué puedo ayudarle?"}
"Quelle est la fiche technique de la pelleteuse CAT 320?" → {"intent":"documentation_search","lang":"fr","agent":"documentation","ack_message":"Je consulte la documentation technique...","estimated_delay":"30 secondes","direct_response":null}
"What is the transport weight of a Volvo EC220?" → {"intent":"documentation_search","lang":"en","agent":"documentation","ack_message":"Checking technical documentation...","estimated_delay":"30 seconds","direct_response":null}
"Change le slogan en français par Votre partenaire machines TP" → {"intent":"modifier_site","lang":"fr","agent":"site_manager","ack_message":"Je modifie le slogan français du site...","estimated_delay":"5 secondes","direct_response":null}
"Mets le téléphone à +351 912 000 000" → {"intent":"modifier_site","lang":"fr","agent":"site_manager","ack_message":"Je mets à jour le numéro de téléphone...","estimated_delay":"5 secondes","direct_response":null}
"Combien coûte le transport d'une pelleteuse de Lyon à Porto ?" → {"intent":"logistique","lang":"fr","agent":"logistique","ack_message":"Je calcule le coût de transport...","estimated_delay":"15 secondes","direct_response":null}
"Génère un devis pour la vente d'un CAT 320 à 45000€" → {"intent":"comptable","lang":"fr","agent":"comptable","ack_message":"Je génère le devis...","estimated_delay":"20 secondes","direct_response":null}
"Traduis cette fiche technique en portugais" → {"intent":"traducteur","lang":"fr","agent":"traducteur","ack_message":"Je traduis le document...","estimated_delay":"20 secondes","direct_response":null}
"Rédige une demande de prix à un fournisseur pour une excavatrice 20T" → {"intent":"demandes_prix","lang":"fr","agent":"demandes_prix","ack_message":"Je rédige la demande de prix...","estimated_delay":"15 secondes","direct_response":null}"""


async def notify_telegram(text: str) -> None:
    """Envoie une notification Telegram à l'admin."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram non configuré (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID manquants)")
        return
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
            )
    except Exception as e:
        logger.warning(f"Telegram notification failed: {e}")


async def get_or_create_user(session_id: str) -> str:
    """Retourne l'user_id lié à la session, le crée si absent."""
    conn = await db_connect()
    try:
        row = await conn.fetchrow("SELECT id FROM users WHERE session_id=$1", session_id)
        if row:
            return row["id"]
        row = await conn.fetchrow(
            "INSERT INTO users (session_id) VALUES ($1) ON CONFLICT (session_id) DO UPDATE SET session_id=EXCLUDED.session_id RETURNING id",
            session_id,
        )
        return row["id"]
    finally:
        await conn.close()


async def check_subscription(user_id: str, agent_name: str) -> str | None:
    """Retourne le statut d'abonnement ou None si pas de ligne. 'expired' si trial périmé."""
    conn = await db_connect()
    try:
        row = await conn.fetchrow(
            "SELECT status, trial_expires_at FROM user_subscriptions WHERE user_id=$1 AND agent_name=$2",
            user_id, agent_name,
        )
    finally:
        await conn.close()
    if not row:
        return None
    if row["status"] == "trial" and row["trial_expires_at"]:
        if row["trial_expires_at"] < datetime.now(timezone.utc):
            return "expired"
    return row["status"]


async def activate_trial(user_id: str, agent_name: str) -> None:
    """Active un trial 24h pour cet agent."""
    conn = await db_connect()
    try:
        await conn.execute(
            """INSERT INTO user_subscriptions (user_id, agent_name, status, activated_at, trial_expires_at)
               VALUES ($1, $2, 'trial', NOW(), NOW() + INTERVAL '24 hours')
               ON CONFLICT (user_id, agent_name) DO UPDATE
               SET status='trial', activated_at=NOW(), trial_expires_at=NOW() + INTERVAL '24 hours'""",
            user_id, agent_name,
        )
    finally:
        await conn.close()


_SUPPORTED_LANGS = {"pt","en","fr","es","de","it","ru","ar","nl","zh"}

def detect_language(text: str, client_lang: str = None) -> str:
    """Pré-détection de langue. client_lang hint du client WS — toujours respecté si valide."""
    if client_lang in _SUPPORTED_LANGS:
        return client_lang
    t = text.lower()
    # Arabic script detection (any Arabic character)
    if any("\u0600" <= c <= "\u06FF" for c in text):
        return "ar"
    # Chinese script detection
    if any("\u4E00" <= c <= "\u9FFF" for c in text):
        return "zh"
    # Cyrillic
    if any("\u0400" <= c <= "\u04FF" for c in text):
        return "ru"
    pt_kw = {"escavadora","escavadoras","máquina","maquina","quero","olá","ola","obrigado",
             "preço","preco","pesquisar","comprar","encontrar","procura","vender","giratória"}
    en_kw = {"excavator","excavators","find","search","loader","crane","tractor",
             "buy","sell","equipment","hello","what","how","can you","please"}
    es_kw = {"excavadora","excavadoras","máquina","maquinaria","hola","busco","quiero",
             "precio","comprar","vender","grúa","cargadora","camión","tractor"}
    de_kw = {"bagger","kran","lader","kaufen","verkaufen","suche","preis","maschine",
             "hallo","guten","wie viel","bulldozer","radlader"}
    it_kw = {"escavatore","escavatori","gru","pala","bulldozer","cerco","prezzo",
             "comprare","vendere","buongiorno","salve","macchina"}
    nl_kw = {"graafmachine","kraan","lader","kopen","verkopen","zoek","prijs",
             "machine","hallo","goedendag","bulldozer"}
    scores = {
        "pt": sum(1 for w in pt_kw if w in t),
        "en": sum(1 for w in en_kw if w in t),
        "es": sum(1 for w in es_kw if w in t),
        "de": sum(1 for w in de_kw if w in t),
        "it": sum(1 for w in it_kw if w in t),
        "nl": sum(1 for w in nl_kw if w in t),
    }
    best = max(scores, key=scores.get)
    if scores[best] > 0:
        return best
    return "fr"


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
    m_low = message.lower()
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
    if any(w in m_low for w in _logistique_kw):
        return {"intent":"logistique","lang":forced_lang,"agent":"logistique",
                "ack_message":{"fr":"Je calcule le transport...","pt":"A calcular o transporte...","en":"Calculating transport..."}.get(forced_lang,"Je calcule..."),
                "estimated_delay":"15s","direct_response":None}
    if any(w in m_low for w in _comptable_kw):
        return {"intent":"comptable","lang":forced_lang,"agent":"comptable",
                "ack_message":{"fr":"Je génère le document...","pt":"A gerar o documento...","en":"Generating document..."}.get(forced_lang,"Je génère..."),
                "estimated_delay":"20s","direct_response":None}
    if any(w in m_low for w in _demandes_kw):
        return {"intent":"demandes_prix","lang":forced_lang,"agent":"demandes_prix",
                "ack_message":{"fr":"Je rédige la demande de prix...","pt":"A redigir o pedido de preço...","en":"Writing price request..."}.get(forced_lang,"Je rédige..."),
                "estimated_delay":"15s","direct_response":None}
    _traducteur_kw = {"traduis","traduire","traduza","tradução","translation","translate","traducir",
                      "en portugais","en français","en anglais","in portuguese","in french","in english",
                      "em português","em francês"}
    if any(w in m_low for w in _traducteur_kw):
        return {"intent":"traducteur","lang":forced_lang,"agent":"traducteur",
                "ack_message":{"fr":"Je traduis le texte...","pt":"A traduzir o texto...","en":"Translating..."}.get(forced_lang,"Je traduis..."),
                "estimated_delay":"20s","direct_response":None}
    _site_kw = {"ajoute produit","ajouter produit","ajoute une annonce","ajouter annonce",
                "crée une fiche","créer fiche","nouveau produit","ajouter au catalogue",
                "modifie le statut","modifier le statut","passe le produit","mettre en vente",
                "modifie le site","modifier le site","change le slogan","changer slogan",
                "configure le site","configurer le site","gestion du site","gérer le site",
                "adicionar produto","atualizar site","mudar slogan","novo produto"}
    if any(w in m_low for w in _site_kw):
        return {"intent":"modifier_site","lang":forced_lang,"agent":"site_manager",
                "ack_message":{"fr":"Je modifie le site vitrine...","pt":"A modificar o site...","en":"Updating the site..."}.get(forced_lang,"Je modifie..."),
                "estimated_delay":"10s","direct_response":None}
    machine_kw = {"escavadora","excavadora","pelleteuse","excavatrice","excavator","grue","crane",
                  "tracteur","tractor","chargeuse","loader","pelle","engin","engins",
                  "machine tp","machines tp","bulldozer","compacteur","tombereau","nacelle",
                  "chariot élévateur","chargeur","niveleuse"}
    if any(w in m_low for w in machine_kw):
        ack_by_lang = {"pt": "A pesquisar...", "en": "Searching...", "fr": "Je recherche..."}
        return {
            "intent": "machine_search", "lang": forced_lang, "agent": "max_search",
            "ack_message": ack_by_lang[forced_lang], "estimated_delay": "2-4 min",
            "direct_response": None,
        }
    fallback_msg = {
        "pt": "Pesquiso máquinas TP, redijo e-mails e monitorizo o mercado. Qual é a sua questão?",
        "en": "I search for construction machinery, write professional emails and monitor the market. What do you need?",
        "fr": "Je recherche des machines TP, rédige des emails et surveille le marché. Quelle est votre demande ?",
        "es": "Busco maquinaria TP, redacto correos y monitorizo el mercado. ¿En qué puedo ayudarle?",
    }
    return {
        "intent": "general_chat", "lang": forced_lang, "agent": None,
        "ack_message": None, "estimated_delay": None,
        "direct_response": fallback_msg.get(forced_lang, fallback_msg["fr"]),
    }


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
                    await conn_act.execute(
                        """INSERT INTO activation_requests (session_id, agent_name, user_message, status)
                           VALUES ($1, $2, $3, 'approved')""",
                        session_id, agent, user_msg[:500],
                    )
                    await conn_act.close()
                except Exception as e:
                    logger.warning(f"activation_requests insert failed: {e}")

        ack = classification.get("ack_message") or (
            f"✅ Je délègue à {agent}... Résultat dans {classification.get('estimated_delay','quelques minutes')}."
            if lang != "pt" else
            f"✅ A delegar para {agent}... Resultado em {classification.get('estimated_delay','alguns minutos')}."
        )
        await ws.send_json({
            "type": "agent_response",
            "payload": ack,
            "metadata": {"intent": intent, "lang": lang, "agent": agent, "status": "delegated"},
        })

        task_id = await create_task(
            session_id=session_id,
            agent_name=agent,
            payload={"message": user_msg, "lang": lang},
            lang=lang,
            estimated_latency=estimated,
        )
        logger.info(f"Task created: {task_id} → {agent}")

    except Exception as e:
        logger.error(f"tony_dispatch error [{session_id[:8]}]: {e}")
        try:
            await ws.send_json({
                "type": "agent_response",
                "payload": "Une erreur est survenue. Veuillez réessayer.",
                "metadata": {"error": str(e)[:100]},
            })
        except Exception:
            pass


# ── Agents ───────────────────────────────────────────────────────────────────

def load_kb(path: str = "/app/knowledge_base.json", max_items: int = 8) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return "\n".join([f"• {json.dumps(item, ensure_ascii=False)}" for item in data[:max_items]])
        return json.dumps(data, ensure_ascii=False)[:2000]
    except Exception as e:
        return f"Contexte indisponible: {e}"


async def run_max_search(payload: dict, lang: str) -> str:
    """Max Search: recherche machines TP (gemma4:e2b)."""
    query = payload.get("message", "")
    context = load_kb()
    lang_instr = "Français." if lang == "fr" else ("Português europeu (PT-PT)." if lang == "pt" else "English.")

    # Recherche sur tob.pt en parallèle
    listings = []
    try:
        listings = await web_utils.search_smart(query, max_results=5)
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
            return res.json().get("message", {}).get("content", "Résultat indisponible.")
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
        "de": "Deutsch. Dein Name ist Léa, du bist die Empfangsdame von LEGA.",
    }.get(lang, "Français. Tu t'appelles Léa.")

    catalogue_context = ""
    try:
        async with httpx.AsyncClient(timeout=10.0) as c:
            r = await c.get(f"{LEGA_SITE_API}/products?status=available&limit=100")
            if r.status_code == 200:
                data = r.json()
                items_list = data.get("items", data) if isinstance(data, dict) else data
                total_count = data.get("total", len(items_list)) if isinstance(data, dict) else len(items_list)
                lines = [
                    f"• {p['title']} — {p['price']} {p.get('currency','EUR')}"
                    if p.get("price") else
                    f"• {p['title']} — Prix sur demande"
                    for p in (items_list or [])
                ]
                if lines:
                    catalogue_context = f"\nCATALOGUE DISPONIBLE ({total_count} annonces):\n" + "\n".join(lines)
    except Exception:
        pass

    prompt = (
        f"Tu es Léa, la standardiste multilingue de LEGA, négociant en engins TP d'occasion. "
        f"Langue: {lang_instr}\n{catalogue_context}\n"
        "Règles: 2-3 phrases max, professionnel, chaleureux, AUCUN emoji, AUCUN symbole spécial.\n"
        "Si question machine → cite le catalogue. Si demande complexe → dis que tu passes à Tony.\n"
        f"DEMANDE: {message}\nRÉPONSE LÉA:"
    )

    full_text = ""
    buf = ""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=5.0)) as client:
            async with client.stream(
                "POST",
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": AGENT_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": True, "think": False,
                    "options": {"temperature": 0.3, "num_predict": 250},
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
            "metadata": {"agent": "standardiste", "lang": lang},
        })

    except Exception as e:
        logger.error(f"standardiste_streaming error: {e}")
        fb = {
            "fr": "Je rencontre une difficulté. Veuillez réessayer.",
            "pt": "Encontrei uma dificuldade. Por favor, tente novamente.",
            "en": "I'm having a technical issue. Please try again.",
        }
        await websocket.send_json({
            "type": "agent_response",
            "payload": fb.get(lang, fb["fr"]),
            "metadata": {"agent": "standardiste", "lang": lang},
        })


async def text_to_speech_edge(text: str, lang: str) -> bytes | None:
    """Génère audio MP3 via Edge-TTS. Retourne None si TTS_ENABLED=false ou erreur."""
    if not TTS_ENABLED or not text.strip():
        return None
    try:
        import base64 as _b64
        import io
        import edge_tts
        voice = TTS_VOICES.get(lang, TTS_VOICES["fr"])
        communicate = edge_tts.Communicate(text.strip(), voice)
        buf = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buf.write(chunk["data"])
        return buf.getvalue() or None
    except Exception as e:
        logger.warning(f"TTS edge error: {e}")
        return None


_SENTENCE_RE = re.compile(r'(?<=[.!?:])\s+')


async def run_vitrine_bot_streaming(message: str, lang: str, websocket: "WebSocket") -> None:
    """vitrine_bot : streaming Ollama gemma2:2b → phrases → TTS → WS audio_chunk."""
    import base64

    lang_instr = {
        "fr": "Réponds en français.",
        "pt": "Responde em português europeu (PT-PT).",
        "en": "Reply in English.",
        "es": "Responde en español.",
        "de": "Antworte auf Deutsch.",
        "it": "Rispondi in italiano.",
        "ru": "Отвечай на русском языке.",
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

    prompt = (
        f"Tu es Léa, assistante de la vitrine LEGA.PT, spécialisée en engins TP d'occasion.\n"
        f"RÈGLE ABSOLUE DE LANGUE: détecte la langue du message client et réponds TOUJOURS dans cette même langue.\n"
        f"Si message en espagnol → réponds en espagnol. Si en arabe → réponds en arabe. "
        f"Si en allemand → réponds en allemand. Si en italien → réponds en italien. "
        f"Si en anglais → réponds en anglais. Indice langue actuel: {lang_instr}\n"
        f"Ne réponds JAMAIS en français si le message n'est pas en français.\n"
        f"{catalogue_ctx}\n"
        "RÈGLES: 1 à 2 phrases MAXIMUM. Ton calme et professionnel. "
        "Zéro emoji. Zéro symbole. Zéro majuscules abusives. Réponse directe et naturelle.\n"
        f"CLIENT: {message}\nLÉA:"
    )

    full_text = ""
    buf = ""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=5.0)) as client:
            async with client.stream(
                "POST",
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": VITRINE_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": True, "think": False,
                    "options": {"temperature": 0.3, "num_predict": 250},
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

                    # Flush complete sentences
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

        # Flush remaining buffer
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
            "metadata": {"agent": "vitrine_bot", "lang": lang},
        })

    except Exception as e:
        logger.error(f"vitrine_bot_streaming error: {e}")
        fb = {
            "fr": "Je rencontre une difficulté technique. Veuillez réessayer.",
            "pt": "Encontrei uma dificuldade técnica. Por favor tente novamente.",
            "en": "I encountered a technical issue. Please try again.",
        }
        await websocket.send_json({
            "type": "agent_response",
            "payload": fb.get(lang, fb["fr"]),
            "metadata": {"agent": "vitrine_bot", "lang": lang},
        })


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
        fb = {
            "fr": "Je rencontre une difficulté technique. Veuillez réessayer.",
            "pt": "Encontrei uma dificuldade técnica. Por favor tente novamente.",
            "en": "I encountered a technical issue. Please try again.",
        }
        await websocket.send_json({
            "type": "agent_response",
            "payload": fb.get(lang, fb["fr"]),
            "metadata": {"agent": "lea", "canal": canal, "lang": lang},
        })


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
            elif action == "product_status":
                pid = action_json.get("product_id", "")
                status_val = action_json.get("status", "available")
                if not pid:
                    return {"fr": "❌ ID produit manquant.", "pt": "❌ ID do produto em falta.", "en": "❌ Product ID missing."}.get(lang, "❌")
                r = await client.patch(f"{LEGA_SITE_API}/products/{pid}/status", json={"status": status_val})
                if r.status_code != 200:
                    return f"❌ Erreur statut produit: HTTP {r.status_code} — {r.text[:80]}"
                logger.info(f"site_manager: product_status id={pid} → {status_val}")
            else:
                return {"fr": "❌ Action non reconnue.", "pt": "❌ Ação não reconhecida.", "en": "❌ Unknown action."}.get(lang, "❌")
    except Exception as e:
        logger.error(f"site_manager API call error: {e}")
        return f"⚠️ Erreur appel API vitrine: {str(e)[:80]}"

    await notify_telegram(f"🔧 <b>Site modifié</b> via site_manager\nCommande: {message[:150]}\nRésultat: {confirmation}")
    return f"✅ {confirmation}"


AGENT_EXECUTORS = {
    "max_search": run_max_search,
    "sam_comms": run_sam_comms,
    "documentation": run_documentation,
    "site_manager": run_site_manager,
    "standardiste": lambda payload, lang: run_standardiste(payload.get("message", ""), lang),
    "logistique": run_logistique,
    "comptable": run_comptable,
    "traducteur": run_traducteur,
    "demandes_prix": run_demandes_prix,
}


# ── DB helpers ───────────────────────────────────────────────────────────────

async def db_connect():
    return await asyncpg.connect(DB_URL)


# ── Conversation memory helpers ───────────────────────────────────────────────

def _build_history_str(history: list, max_turns: int = 3) -> str:
    if not history:
        return ""
    lines = []
    for h in history[-(max_turns * 2):]:
        role = "Utilisateur" if h["role"] == "user" else "Tony"
        lines.append(f"{role} : {h['content'][:120]}")
    return "HISTORIQUE (derniers échanges) :\n" + "\n".join(lines) + "\n\n"


async def _load_conv_history(user_id: str) -> list:
    try:
        conn = await db_connect()
        rows = await conn.fetch(
            "SELECT role, content FROM conversation_history WHERE user_id=$1 ORDER BY created_at DESC LIMIT 10",
            user_id,
        )
        await conn.close()
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]
    except Exception as e:
        logger.warning(f"load_conv_history failed: {e}")
        return []


async def _save_conv_history(user_id: str, user_msg: str, assistant_msg: str, lang: str) -> None:
    try:
        conn = await db_connect()
        await conn.execute(
            "INSERT INTO conversation_history (user_id, role, content, language) VALUES ($1,$2,$3,$4)",
            user_id, "user", user_msg[:1000], lang,
        )
        await conn.execute(
            "INSERT INTO conversation_history (user_id, role, content, language) VALUES ($1,$2,$3,$4)",
            user_id, "assistant", assistant_msg[:1000], lang,
        )
        await conn.close()
    except Exception as e:
        logger.debug(f"save_conv_history failed: {e}")


async def create_task(session_id: str, agent_name: str, payload: dict, lang: str, estimated_latency: int) -> str:
    task_id = str(uuid.uuid4())
    conn = await db_connect()
    try:
        await conn.execute(
            """INSERT INTO tasks (task_id, session_id, agent_name, payload, status, language, estimated_latency_sec)
               VALUES ($1, $2, $3, $4, 'pending', $5, $6)""",
            task_id, session_id, agent_name, json.dumps(payload), lang, estimated_latency,
        )
    finally:
        await conn.close()
    return task_id


async def update_task(task_id: str, status: str, result_json: dict = None, error: str = None):
    conn = await db_connect()
    try:
        if status == "running":
            await conn.execute(
                "UPDATE tasks SET status='running', started_at=NOW() WHERE task_id=$1", task_id
            )
        elif status == "done":
            await conn.execute(
                """UPDATE tasks SET status='done', completed_at=NOW(),
                   actual_latency_sec=EXTRACT(EPOCH FROM (NOW()-started_at))::int,
                   result_json=$2 WHERE task_id=$1""",
                task_id, json.dumps(result_json),
            )
        elif status == "failed":
            await conn.execute(
                "UPDATE tasks SET status='failed', completed_at=NOW(), error_message=$2 WHERE task_id=$1",
                task_id, error,
            )
    finally:
        await conn.close()


# ── Background worker ────────────────────────────────────────────────────────

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
        await conn.close()
        if today_events:
            lines = [f"  • {r['start_time'].strftime('%H:%M')} — {r['title']}" + (f" ({r['location']})" if r['location'] else "") for r in today_events]
            header = {"fr": "📅 PLANNING DU JOUR", "pt": "📅 AGENDA DO DIA", "en": "📅 TODAY'S SCHEDULE"}[lang]
            sections.append(header + "\n" + "\n".join(lines))
        else:
            header = {"fr": "📅 PLANNING DU JOUR", "pt": "📅 AGENDA DO DIA", "en": "📅 TODAY'S SCHEDULE"}[lang]
            empty = {"fr": "  Aucun événement planifié", "pt": "  Sem eventos agendados", "en": "  No events scheduled"}[lang]
            sections.append(header + "\n" + empty)
    except Exception as e:
        logger.warning(f"Brief events error: {e}")

    # 2. Catalogue — produits récents
    try:
        conn = await db_connect()
        recent_products = await conn.fetch(
            "SELECT title, price, currency FROM products WHERE status='published' ORDER BY created_at DESC LIMIT 3"
        )
        await conn.close()
        if recent_products:
            lines = [f"  • {r['title']} — {r['price']}{r['currency']}" for r in recent_products]
            header = {"fr": "🚜 MACHINES EN VENTE", "pt": "🚜 MÁQUINAS À VENDA", "en": "🚜 MACHINES FOR SALE"}[lang]
            sections.append(header + "\n" + "\n".join(lines))
    except Exception as e:
        logger.warning(f"Brief products error: {e}")

    # 3. Opportunités marché via SearXNG (si activé dans prefs)
    if prefs.get("alertes_opportunites", True):
        try:
            queries = {
                "fr": "pelleteuse occasion vente france portugal prix",
                "pt": "escavadoras usadas venda portugal espanha preço",
                "en": "used excavator for sale europe price",
            }
            results = await web_utils.search_web(queries.get(lang, queries["fr"]), max_results=3, lang=lang)
            if results:
                lines = [f"  • {r['title'][:80]}" for r in results[:3]]
                header = {"fr": "📈 OPPORTUNITÉS MARCHÉ", "pt": "📈 OPORTUNIDADES DE MERCADO", "en": "📈 MARKET OPPORTUNITIES"}[lang]
                sections.append(header + "\n" + "\n".join(lines))
        except Exception as e:
            logger.warning(f"Brief search error: {e}")

    # 4. Tâches récentes (agents actifs hier)
    try:
        conn = await db_connect()
        recent_tasks = await conn.fetch(
            """SELECT agent_name, COUNT(*) as cnt FROM tasks
               WHERE completed_at > NOW() - INTERVAL '24 hours' AND status='done'
               GROUP BY agent_name ORDER BY cnt DESC LIMIT 3"""
        )
        await conn.close()
        if recent_tasks:
            lines = [f"  • {r['agent_name']} : {r['cnt']} tâche(s)" for r in recent_tasks]
            header = {"fr": "⚡ ACTIVITÉ (24H)", "pt": "⚡ ATIVIDADE (24H)", "en": "⚡ ACTIVITY (24H)"}[lang]
            sections.append(header + "\n" + "\n".join(lines))
    except Exception as e:
        logger.warning(f"Brief tasks error: {e}")

    # Assemblage
    date_str = datetime.now().strftime("%A %d %B %Y")
    greet = {
        "fr": f"🌅 <b>Brief Matinal LEGA</b> — {date_str}\n\n",
        "pt": f"🌅 <b>Briefing Matinal LEGA</b> — {date_str}\n\n",
        "en": f"🌅 <b>LEGA Morning Brief</b> — {date_str}\n\n",
    }[lang]
    footer = {
        "fr": "\n\n💡 Répondez à ce message ou ouvrez le chat Tony pour agir.",
        "pt": "\n\n💡 Responda a esta mensagem ou abra o chat Tony para agir.",
        "en": "\n\n💡 Reply to this message or open the Tony chat to take action.",
    }[lang]

    return greet + "\n\n".join(sections) + footer


async def send_morning_brief():
    """Envoie le brief matinal à tous les utilisateurs avec brief_enabled=true."""
    logger.info("Morning brief: building...")
    try:
        conn = await db_connect()
        users = await conn.fetch(
            """SELECT id, preferred_language, preferences, telegram_chat_id
               FROM users
               WHERE (preferences->>'brief_enabled')::boolean IS NOT FALSE"""
        )
        await conn.close()

        sent = 0
        already_sent: set = set()  # éviter doublons si plusieurs users partagent le même chat_id
        for user in users:
            lang = user["preferred_language"] or "fr"
            raw_prefs = user["preferences"]
            if isinstance(raw_prefs, str):
                try:
                    raw_prefs = json.loads(raw_prefs)
                except Exception:
                    raw_prefs = {}
            prefs = raw_prefs or {}
            chat_id = user["telegram_chat_id"] or TELEGRAM_CHAT_ID  # fallback admin
            if not chat_id or chat_id in already_sent:
                continue
            already_sent.add(chat_id)
            brief_text = await build_morning_brief(lang=lang, user_prefs=prefs)
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    await client.post(
                        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                        json={"chat_id": chat_id, "text": brief_text, "parse_mode": "HTML"},
                    )
                sent += 1
            except Exception as e:
                logger.warning(f"Brief Telegram send error (user {str(user['id'])[:8]}): {e}")

        logger.info(f"Morning brief sent to {sent} user(s)")
    except Exception as e:
        logger.error(f"Morning brief error: {e}")


async def morning_brief_cron():
    """Cron : envoie le brief matinal tous les jours à l'heure configurée (défaut 07:00)."""
    logger.info("Morning brief cron started")
    brief_hour = int(os.getenv("BRIEF_HOUR", "7"))
    brief_minute = int(os.getenv("BRIEF_MINUTE", "0"))
    while True:
        now_dt = datetime.now()
        # Calculer les secondes jusqu'au prochain déclenchement
        next_run = now_dt.replace(hour=brief_hour, minute=brief_minute, second=0, microsecond=0)
        if next_run <= now_dt:
            from datetime import timedelta
            next_run = next_run + timedelta(days=1)
        wait_secs = (next_run - now_dt).total_seconds()
        logger.info(f"Morning brief cron: prochain envoi dans {int(wait_secs//3600)}h{int((wait_secs%3600)//60)}m")
        await asyncio.sleep(wait_secs)
        await send_morning_brief()


@app.on_event("startup")
async def startup():
    build_rag_index()
    asyncio.create_task(task_worker())
    asyncio.create_task(trial_expiry_cron())
    asyncio.create_task(morning_brief_cron())
    try:
        conn = await db_connect()
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_history (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                language TEXT DEFAULT 'fr',
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_conv_hist_user ON conversation_history(user_id, created_at DESC)"
        )
        await conn.close()
        logger.info("conversation_history table ready")
    except Exception as e:
        logger.warning(f"conversation_history table init failed: {e}")
    logger.info("LEGA API v1.0 started — Tony + Worker + Trial cron + Morning brief + RAG online")


# ── Endpoint déclencher brief manuellement ───────────────────────────────────

@app.post("/api/agenda/brief-now")
async def trigger_brief_now(lang: str = "fr"):
    """Déclenche le brief matinal immédiatement (test / usage admin)."""
    asyncio.create_task(send_morning_brief())
    return {"status": "ok", "message": f"Brief matinal déclenché (lang={lang})"}


# ── WebSocket ────────────────────────────────────────────────────────────────

@app.websocket("/ws/stream")
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

            await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        logger.info(f"WS disconnected: {session_id[:8]}")
    except Exception as e:
        logger.error(f"WS fatal [{session_id[:8]}]: {e}")
    finally:
        active_connections.pop(session_id, None)


# ── REST Chat (fallback HTTP) ─────────────────────────────────────────────────

@app.post("/api/chat")
async def chat_rest(message: dict):
    user_msg = message.get("message", "")
    lang = message.get("lang", "fr")
    context = load_kb()
    system_prompt = "Tu es un expert en sourcing de machines TP pour l'export France→Portugal. Réponds en français, cite les sources du contexte."
    full_prompt = f"{system_prompt}\n\n📚 CONTEXTE:\n{context}\n\n❓ QUESTION: {user_msg}\n\n✅ RÉPONSE:"
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            res = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={"model": TONY_MODEL, "messages": [{"role": "user", "content": full_prompt}], "stream": False, "think": False, "options": {"temperature": 0.3, "num_predict": 2048}},
            )
            reply = res.json().get("message", {}).get("content", "Pas de réponse")
        return {"content": reply, "model": TONY_MODEL}
    except Exception as e:
        return {"content": f"Erreur: {str(e)[:100]}", "model": TONY_MODEL}


# ── Auth ─────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/auth/login")
async def auth_login(req: LoginRequest):
    if req.username != ADMIN_USER or req.password != ADMIN_PASS:
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    token = create_jwt_token(req.username)
    return {"access_token": token, "token_type": "bearer", "expires_in": JWT_EXPIRE_HOURS * 3600}

@app.get("/api/auth/me")
async def auth_me(username: str = Depends(verify_jwt_token)):
    return {"username": username, "role": "admin"}


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "active_ws": len(active_connections),
        "uptime": int(time.time()),
    }


# ── Registry endpoints ────────────────────────────────────────────────────────

@app.get("/api/agents/registry")
async def get_registry(_: str = Depends(verify_jwt_token)):
    try:
        conn = await db_connect()
        rows = await conn.fetch(
            "SELECT name, display_name, model, capabilities, avg_latency_sec, ram_cost_mb, status, is_premium, price_monthly_eur FROM agent_registry ORDER BY id"
        )
        await conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/agents/{name}/status")
async def get_agent_status(name: str):
    try:
        conn = await db_connect()
        row = await conn.fetchrow("SELECT * FROM agent_registry WHERE name=$1", name)
        await conn.close()
        if not row:
            raise HTTPException(404, "Agent non trouvé")
        return dict(row)
    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e)}


# ── Tasks endpoints ───────────────────────────────────────────────────────────

@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str, _: str = Depends(verify_jwt_token)):
    try:
        conn = await db_connect()
        row = await conn.fetchrow("SELECT * FROM tasks WHERE task_id=$1", task_id)
        await conn.close()
        if not row:
            raise HTTPException(404, "Tâche non trouvée")
        return dict(row)
    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/tasks")
async def list_tasks(session_id: str = None, status: str = None, limit: int = 20, _: str = Depends(verify_jwt_token)):
    try:
        conn = await db_connect()
        query = "SELECT task_id, session_id, agent_name, status, language, created_at, completed_at, estimated_latency_sec, actual_latency_sec FROM tasks WHERE 1=1"
        params = []
        if session_id:
            query += f" AND session_id=${len(params)+1}"
            params.append(session_id)
        if status:
            query += f" AND status=${len(params)+1}"
            params.append(status)
        query += f" ORDER BY created_at DESC LIMIT ${len(params)+1}"
        params.append(limit)
        rows = await conn.fetch(query, *params)
        await conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        return {"error": str(e)}


# ── Crews directs (mode non-async) ───────────────────────────────────────────

@app.post("/api/crew/devis")
async def crew_devis(request: dict):
    desc = request.get("description", "")
    if not desc:
        return {"error": "Description requise."}
    prompt = f"""Expert travaux publics. Devis estimatif pour : "{desc}"
Format:
📋 TITRE DU DEVIS
📐 Surface/Volume estimé
🧱 Matériaux principaux
⏱️ Durée estimée
💰 Fourchette de prix (HT, €)
⚠️ Points de vigilance
Sois concis et réaliste."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=10.0)) as client:
            res = await client.post(f"{OLLAMA_URL}/api/chat", json={"model": TONY_MODEL, "messages": [{"role": "user", "content": prompt}], "stream": False, "think": False, "options": {"temperature": 0.3, "num_predict": 500}})
            return {"crew": "devis", "result": res.json().get("message", {}).get("content", "Erreur"), "model": TONY_MODEL}
    except Exception as e:
        return {"crew": "devis", "error": str(e)[:100]}


@app.post("/api/crew/fiche")
async def crew_fiche(request: dict):
    desc = request.get("description", "")
    lang = request.get("lang", "fr")
    if not desc:
        return {"error": "Description requise."}
    try:
        from crews.fiche_crew import gen_fiche
        return gen_fiche(desc, lang)
    except Exception:
        lang_instr = "Français." if lang == "fr" else "Portugais européen (PT-PT)."
        prompt = f"""Expert machines TP d'occasion. Fiche produit pour : "{desc}"
Langue: {lang_instr}
Format:
🚜 TITRE (Marque+Modèle+Année)
⚙️ SPECS (Heures, kW, Poids, Options)
✅ ÉTAT & POINTS FORTS
💶 PRIX CONSEILLÉ (€ HT)
📝 DESCRIPTION VENDEUR (3-4 lignes)"""
        async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=10.0)) as client:
            res = await client.post(f"{OLLAMA_URL}/api/chat", json={"model": TONY_MODEL, "messages": [{"role": "user", "content": prompt}], "stream": False, "think": False, "options": {"temperature": 0.3, "num_predict": 400}})
            return {"crew": "fiche", "result": res.json().get("message", {}).get("content", "Erreur"), "model": TONY_MODEL, "lang": lang}


@app.post("/api/crew/argus")
async def crew_argus(request: dict):
    machine = request.get("machine", "")
    lang = request.get("lang", "fr")
    if not machine:
        return {"error": "Modèle/Heures/État requis."}
    try:
        from crews.argus_crew import gen_argus
        return gen_argus(machine, None, "bon", lang)
    except Exception:
        lang_instr = "Français." if lang == "fr" else "Portugais européen (PT-PT)."
        prompt = f"""Expert estimation machines TP. Estimation prix pour : "{machine}"
Langue: {lang_instr}
Donne: Fourchette basse/haute, facteurs influençant le prix, conseil de mise en vente."""
        async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=10.0)) as client:
            res = await client.post(f"{OLLAMA_URL}/api/chat", json={"model": TONY_MODEL, "messages": [{"role": "user", "content": prompt}], "stream": False, "think": False, "options": {"temperature": 0.4, "num_predict": 350}})
            return {"crew": "argus", "result": res.json().get("message", {}).get("content", "Erreur"), "model": TONY_MODEL, "lang": lang}


@app.post("/api/crew/veille")
async def crew_veille(request: dict):
    criteres = request.get("criteres", "")
    lang = request.get("lang", "fr")
    if not criteres:
        return {"error": "Critères requis."}
    listings = await web_utils.search_smart(criteres, max_results=5)
    listings_text = "\n".join([f"- {l['title']} | {l.get('price','N/A')}" for l in listings]) if listings else "Aucune annonce trouvée."
    lang_instr = "Français." if lang == "fr" else "Portugais européen (PT-PT)."
    prompt = f"""Assistant veille marché TP. Critères : "{criteres}"
Langue: {lang_instr}
Annonces tob.pt:
{listings_text}
Génère: 1) 3 alertes basées sur ces annonces, 2) Conseils prix, 3) Message client prêt à envoyer."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=10.0)) as client:
            res = await client.post(f"{OLLAMA_URL}/api/chat", json={"model": TONY_MODEL, "messages": [{"role": "user", "content": prompt}], "stream": False, "think": False, "options": {"temperature": 0.4, "num_predict": 400}})
            return {"crew": "veille", "result": res.json().get("message", {}).get("content", "Erreur"), "model": TONY_MODEL, "lang": lang, "sources": listings}
    except Exception as e:
        return {"crew": "veille", "error": str(e)[:100]}


# ── Sources CRUD ──────────────────────────────────────────────────────────────

@app.get("/api/sources")
async def api_get_sources(_: str = Depends(verify_jwt_token)):
    try:
        conn = await db_connect()
        rows = await conn.fetch("SELECT id, url, category, region, added_by, created_at FROM sources ORDER BY created_at DESC")
        await conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/sources/add")
async def add_source(request: dict, _: str = Depends(verify_jwt_token)):
    url = request.get("url", "").strip()
    if not url or not url.startswith("http"):
        return {"error": "URL valide requise"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers={"User-Agent": "LEGA-Bot/1.0"}, follow_redirects=True)
            if resp.status_code >= 400:
                return {"status": "warning", "message": f"URL accessible mais code {resp.status_code}", "url": url}
        return {"status": "ok", "url": url, "message": "Source validée"}
    except Exception as e:
        return {"status": "error", "message": str(e)[:100]}


@app.delete("/api/sources/{source_id}")
async def api_delete_source(source_id: int, _: str = Depends(verify_jwt_token)):
    try:
        conn = await db_connect()
        await conn.execute("DELETE FROM sources WHERE id=$1", source_id)
        await conn.close()
        return {"status": "ok", "message": "Source supprimée"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ── Products CRUD ─────────────────────────────────────────────────────────────

@app.get("/api/products")
async def get_products(category: str = None, status: str = None, limit: int = 50):
    try:
        conn = await db_connect()
        query = "SELECT id, title, description, price, currency, category, attributes, images, status, created_at FROM products WHERE 1=1"
        params = []
        if category:
            query += f" AND category=${len(params)+1}"
            params.append(category)
        if status:
            query += f" AND status=${len(params)+1}"
            params.append(status)
        query += f" ORDER BY created_at DESC LIMIT ${len(params)+1}"
        params.append(limit)
        rows = await conn.fetch(query, *params)
        await conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/products/{product_id}")
async def get_product(product_id: int):
    try:
        conn = await db_connect()
        row = await conn.fetchrow("SELECT * FROM products WHERE id=$1", product_id)
        await conn.close()
        if not row:
            raise HTTPException(404, "Produit non trouvé")
        return dict(row)
    except HTTPException:
        raise
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/products")
async def create_product(product: ProductCreate, _: str = Depends(verify_jwt_token)):
    try:
        conn = await db_connect()
        row = await conn.fetchrow(
            "INSERT INTO products (title, description, price, currency, category, attributes, images, status, created_at) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,NOW()) RETURNING id",
            product.title, product.description, product.price, product.currency,
            product.category, json.dumps(product.attributes), json.dumps(product.images), product.status,
        )
        await conn.close()
        return {"status": "ok", "id": row["id"]}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.put("/api/products/{product_id}")
async def update_product(product_id: int, product: ProductUpdate, _: str = Depends(verify_jwt_token)):
    try:
        conn = await db_connect()
        updates, params = [], [product_id]
        for field in ["title", "description", "price", "currency", "category", "status"]:
            val = getattr(product, field)
            if val is not None:
                updates.append(f"{field}=${len(params)+1}")
                params.append(val)
        for field in ["attributes", "images"]:
            val = getattr(product, field)
            if val is not None:
                updates.append(f"{field}=${len(params)+1}")
                params.append(json.dumps(val))
        if not updates:
            await conn.close()
            return {"status": "error", "message": "Aucun champ à mettre à jour"}
        updates.append("updated_at=NOW()")
        row = await conn.fetchrow(f"UPDATE products SET {','.join(updates)} WHERE id=$1 RETURNING id", *params)
        await conn.close()
        if not row:
            raise HTTPException(404, "Produit non trouvé")
        return {"status": "ok", "id": row["id"]}
    except HTTPException:
        raise
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.delete("/api/products/{product_id}")
async def delete_product(product_id: int, _: str = Depends(verify_jwt_token)):
    try:
        conn = await db_connect()
        await conn.execute("UPDATE products SET status='archived', updated_at=NOW() WHERE id=$1", product_id)
        await conn.close()
        return {"status": "ok", "message": "Produit archivé"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/products/{product_id}/upload")
async def upload_product_image(product_id: int, file: UploadFile = File(...), _: str = Depends(verify_jwt_token)):
    """Upload image for a product, save to /app/uploads/, update images array in DB."""
    allowed = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if file.content_type not in allowed:
        raise HTTPException(400, "Format non supporté (jpg/png/webp uniquement)")
    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
    filename = f"{product_id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = UPLOAD_DIR / filename
    try:
        contents = await file.read()
        async with aiofiles.open(filepath, "wb") as f:
            await f.write(contents)
        url = f"/uploads/{filename}"
        # Append to product's images array
        conn = await db_connect()
        row = await conn.fetchrow("SELECT images FROM products WHERE id=$1", product_id)
        if row:
            images = json.loads(row["images"] or "[]")
            images.append(url)
            await conn.execute("UPDATE products SET images=$1, updated_at=NOW() WHERE id=$2", json.dumps(images), product_id)
        await conn.close()
        return {"status": "ok", "url": url, "filename": filename}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.patch("/api/products/{product_id}/status")
async def patch_product_status(product_id: int, request: dict, _: str = Depends(verify_jwt_token)):
    """Update product status: draft→pending→published or →archived."""
    new_status = request.get("status")
    if new_status not in ("draft", "pending", "published", "archived"):
        raise HTTPException(400, "Statut invalide")
    try:
        conn = await db_connect()
        row = await conn.fetchrow(
            "UPDATE products SET status=$1, updated_at=NOW() WHERE id=$2 RETURNING id, status",
            new_status, product_id
        )
        await conn.close()
        if not row:
            raise HTTPException(404, "Produit non trouvé")
        return {"status": "ok", "id": row["id"], "new_status": row["status"]}
    except HTTPException:
        raise
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ── Agent status update ────────────────────────────────────────────────────────

@app.put("/api/agents/{name}/status")
async def update_agent_status(name: str, request: dict, _: str = Depends(verify_jwt_token)):
    new_status = request.get("status")
    if new_status not in ("active", "maintenance", "overloaded"):
        raise HTTPException(400, "Statut invalide")
    try:
        conn = await db_connect()
        row = await conn.fetchrow(
            "UPDATE agent_registry SET status=$1, updated_at=NOW() WHERE name=$2 RETURNING name, status",
            new_status, name
        )
        await conn.close()
        if not row:
            raise HTTPException(404, "Agent non trouvé")
        return {"status": "ok", "name": row["name"], "agent_status": row["status"]}
    except HTTPException:
        raise
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ── Monitoring ────────────────────────────────────────────────────────────────

@app.get("/api/monitoring")
async def get_monitoring(_: str = Depends(verify_jwt_token)):
    result: dict = {"timestamp": int(time.time()), "ollama": {}, "tasks": {}, "db": "ok", "ram": {}}

    # RAM (host via /proc/meminfo)
    try:
        with open("/proc/meminfo") as f:
            mem = {line.split(":")[0].strip(): int(line.split(":")[1].strip().split()[0]) for line in f if ":" in line}
        total_mb = mem.get("MemTotal", 0) // 1024
        free_mb = (mem.get("MemFree", 0) + mem.get("Buffers", 0) + mem.get("Cached", 0)) // 1024
        used_mb = total_mb - free_mb
        result["ram"] = {"total_mb": total_mb, "used_mb": used_mb, "free_mb": free_mb, "pct": round(used_mb / total_mb * 100) if total_mb else 0}
    except Exception as e:
        result["ram"] = {"error": str(e)}

    # Ollama: installed models
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            tags = await client.get(f"{OLLAMA_URL}/api/tags")
            models = [m["name"] for m in tags.json().get("models", [])]
            result["ollama"]["models"] = models
    except Exception:
        result["ollama"]["models"] = []

    # Ollama: currently loaded model
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            ps = await client.get(f"{OLLAMA_URL}/api/ps")
            loaded = [m["name"] for m in ps.json().get("models", [])]
            result["ollama"]["loaded"] = loaded
    except Exception:
        result["ollama"]["loaded"] = []

    # Task stats
    try:
        conn = await db_connect()
        rows = await conn.fetch("SELECT status, COUNT(*) as cnt FROM tasks GROUP BY status")
        result["tasks"] = {r["status"]: r["cnt"] for r in rows}
        # Recent tasks
        recent = await conn.fetch(
            "SELECT task_id, agent_name, status, language, created_at, completed_at FROM tasks ORDER BY created_at DESC LIMIT 8"
        )
        result["recent_tasks"] = [dict(r) for r in recent]
        await conn.close()
    except Exception as e:
        result["db"] = str(e)

    # Active WS connections
    result["active_ws"] = len(active_connections)

    return result


# ── Activations ───────────────────────────────────────────────────────────────

@app.get("/api/activations")
async def get_activations(status: str = None, _: str = Depends(verify_jwt_token)):
    try:
        conn = await db_connect()
        query = "SELECT id, session_id, user_email, agent_name, user_message, status, admin_notes, created_at, reviewed_at FROM activation_requests"
        params = []
        if status:
            query += " WHERE status=$1"
            params.append(status)
        query += " ORDER BY created_at DESC"
        rows = await conn.fetch(query, *params)
        await conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/activations")
async def create_activation(request: dict):
    try:
        conn = await db_connect()
        row = await conn.fetchrow(
            """INSERT INTO activation_requests (session_id, user_email, agent_name, user_message)
               VALUES ($1, $2, $3, $4) RETURNING id""",
            request.get("session_id"), request.get("user_email"), request.get("agent_name"), request.get("user_message")
        )
        await conn.close()
        return {"status": "ok", "id": row["id"]}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.put("/api/activations/{activation_id}")
async def review_activation(activation_id: int, request: dict, _: str = Depends(verify_jwt_token)):
    new_status = request.get("status")
    if new_status not in ("approved", "rejected"):
        raise HTTPException(400, "Status must be approved or rejected")
    admin_notes = request.get("admin_notes", "")
    try:
        conn = await db_connect()
        row = await conn.fetchrow(
            """UPDATE activation_requests SET status=$1, admin_notes=$2, reviewed_at=NOW()
               WHERE id=$3 RETURNING id, status, agent_name, session_id""",
            new_status, admin_notes, activation_id
        )
        await conn.close()
        if not row:
            raise HTTPException(404, "Demande non trouvée")
        # If approved: create trial subscription
        if new_status == "approved" and row["agent_name"] and row["session_id"]:
            conn2 = await db_connect()
            try:
                user = await conn2.fetchrow("SELECT id FROM users WHERE session_id=$1", row["session_id"])
                if user:
                    await conn2.execute(
                        """INSERT INTO user_subscriptions (user_id, agent_name, status, activated_at, trial_expires_at)
                           VALUES ($1, $2, 'trial', NOW(), NOW() + INTERVAL '24 hours')
                           ON CONFLICT (user_id, agent_name) DO UPDATE SET status='trial', trial_expires_at=NOW() + INTERVAL '24 hours'""",
                        user["id"], row["agent_name"]
                    )
                # Push WS notification to user
                ws = active_connections.get(row["session_id"])
                if ws:
                    await ws.send_json({
                        "type": "agent_response",
                        "payload": f"✅ Votre accès trial à l'agent {row['agent_name']} a été approuvé ! Valable 24h.",
                        "metadata": {"type": "trial_approved", "agent": row["agent_name"]},
                    })
            finally:
                await conn2.close()
        return {"status": "ok", "id": row["id"], "result": new_status}
    except HTTPException:
        raise
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ── Agent Site Management ─────────────────────────────────────────────────────

@app.post("/api/agent/manage-site")
async def agent_manage_site(action: AgentSiteAction, x_agent_key: str = None):
    """
    Endpoint réservé aux agents pour modifier le site automatiquement.
    Actif uniquement si SITE_MANAGEMENT_MODE=agent.
    Authentification par param x_agent_key (ou header X-Agent-Key à venir).
    """
    # Vérifier le mode
    if SITE_MANAGEMENT_MODE != "agent":
        raise HTTPException(
            403,
            detail={
                "error": "mode_manual",
                "message": "Le site est en mode gestion manuelle. Passez SITE_MANAGEMENT_MODE=agent pour activer les modifications automatiques.",
                "current_mode": SITE_MANAGEMENT_MODE,
            }
        )

    # Vérifier la clé API agent
    if AGENT_API_KEY and x_agent_key != AGENT_API_KEY:
        raise HTTPException(401, detail={"error": "invalid_key", "message": "Clé API agent invalide."})

    conn = await db_connect()
    try:
        result_data = {}

        if action.action == "create":
            required = ["title", "price"]
            missing = [f for f in required if not action.data.get(f)]
            if missing:
                raise HTTPException(400, detail={"error": "missing_fields", "fields": missing})
            row = await conn.fetchrow(
                """INSERT INTO products (title, description, price, currency, category, attributes, images, status, created_at)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,'draft',NOW()) RETURNING id""",
                action.data.get("title"), action.data.get("description", ""),
                float(action.data.get("price", 0)), action.data.get("currency", "€"),
                action.data.get("category", "tp"),
                json.dumps(action.data.get("attributes", {})),
                json.dumps(action.data.get("images", [])),
            )
            result_data = {"id": row["id"], "status": "draft"}

        elif action.action == "update":
            if not action.product_id:
                raise HTTPException(400, detail={"error": "missing_product_id"})
            fields, params = [], [action.product_id]
            for f in ["title", "description", "currency", "category", "status"]:
                if f in action.data:
                    fields.append(f"{f}=${len(params)+1}"); params.append(action.data[f])
            if "price" in action.data:
                fields.append(f"price=${len(params)+1}"); params.append(float(action.data["price"]))
            for f in ["attributes", "images"]:
                if f in action.data:
                    fields.append(f"{f}=${len(params)+1}"); params.append(json.dumps(action.data[f]))
            if not fields:
                raise HTTPException(400, detail={"error": "no_fields_to_update"})
            fields.append("updated_at=NOW()")
            row = await conn.fetchrow(
                f"UPDATE products SET {','.join(fields)} WHERE id=$1 RETURNING id, status", *params
            )
            if not row:
                raise HTTPException(404, detail={"error": "product_not_found"})
            result_data = {"id": row["id"], "status": row["status"]}

        elif action.action == "delete":
            if not action.product_id:
                raise HTTPException(400, detail={"error": "missing_product_id"})
            await conn.execute(
                "UPDATE products SET status='archived', updated_at=NOW() WHERE id=$1", action.product_id
            )
            result_data = {"id": action.product_id, "status": "archived"}

        elif action.action == "publish":
            if not action.product_id:
                raise HTTPException(400, detail={"error": "missing_product_id"})
            row = await conn.fetchrow(
                "UPDATE products SET status='published', updated_at=NOW() WHERE id=$1 RETURNING id, title", action.product_id
            )
            if not row:
                raise HTTPException(404, detail={"error": "product_not_found"})
            result_data = {"id": row["id"], "title": row["title"], "status": "published"}

        elif action.action == "unpublish":
            if not action.product_id:
                raise HTTPException(400, detail={"error": "missing_product_id"})
            row = await conn.fetchrow(
                "UPDATE products SET status='draft', updated_at=NOW() WHERE id=$1 RETURNING id, title", action.product_id
            )
            if not row:
                raise HTTPException(404, detail={"error": "product_not_found"})
            result_data = {"id": row["id"], "title": row["title"], "status": "draft"}

        else:
            raise HTTPException(400, detail={"error": "unknown_action", "valid_actions": ["create","update","delete","publish","unpublish"]})

    finally:
        await conn.close()

    # Notification Telegram
    tg_msg = (
        f"🤖 <b>Action agent site</b>\n"
        f"Action : <code>{action.action}</code>\n"
        f"Agent : <code>{action.agent_name or 'inconnu'}</code>\n"
        f"Produit ID : {action.product_id or result_data.get('id', '—')}\n"
        f"Résultat : {result_data}\n"
        f"Raison : {action.reason or '—'}"
    )
    asyncio.create_task(notify_telegram(tg_msg))
    logger.info(f"Agent site action: {action.action} → {result_data}")

    return {
        "status": "ok",
        "action": action.action,
        "mode": SITE_MANAGEMENT_MODE,
        "result": result_data,
    }


@app.get("/api/agent/manage-site/mode")
async def get_site_mode():
    """Retourne le mode de gestion actuel du site."""
    return {
        "mode": SITE_MANAGEMENT_MODE,
        "agent_enabled": SITE_MANAGEMENT_MODE == "agent",
        "description": "Gestion automatique par agents" if SITE_MANAGEMENT_MODE == "agent" else "Gestion manuelle via dashboard",
    }
