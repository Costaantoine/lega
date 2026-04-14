import asyncpg
import asyncio
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import aiofiles
import httpx
import web_utils
from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
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

# Agents nécessitant un abonnement
PREMIUM_AGENTS = {"max_search", "sam_comms", "visa_vision"}

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


# ── Tony prompt ──────────────────────────────────────────────────────────────

TONY_SYSTEM = """Tu es Tony, l'interface conversationnelle de LEGA/BVI.

RÈGLE PRIORITAIRE: Réponds UNIQUEMENT avec un objet JSON valide. Aucun texte avant ou après.

RÈGLE LINGUISTIQUE: Détecte la langue de la question (FR/PT/EN) et génère les messages dans cette langue.

FORMAT JSON STRICT:
{
  "intent": "machine_search" | "email_followup" | "image_analysis" | "watch_request" | "general_chat",
  "lang": "fr" | "pt" | "en",
  "agent": "max_search" | "sam_comms" | "visa_vision" | null,
  "ack_message": "Message naturel dans la langue de la question (pour intents avec agent)",
  "estimated_delay": "2-4 minutes" | "45-90 secondes" | "<5 secondes" | null,
  "direct_response": "Réponse complète si intent=general_chat, sinon null"
}

CLASSIFICATION:
- machine_search: pelleteuse, pelle, tracteur, grue, chargeuse, excavadora, escavadora, engins, machines TP, prix <X€
- email_followup: relancer, email, message, contacter, devis, client, follow-up
- image_analysis: photo, image, analyser, voir, badge, VENDU, PROMO, analysa
- watch_request: surveiller, alerter, veille, surveille, monitorizar, alerta
- general_chat: bonjour, aide, question générale, quoi, comment, que fais-tu, olá, hello

EXEMPLES:
- "Trouve pelleteuse 10T <10k€" → machine_search, max_search, "2-4 minutes"
- "Procura escavadora 15T" → machine_search, max_search, "2-4 minutos", lang=pt
- "Relance M. Dupont pour devis" → email_followup, sam_comms, "45-90 secondes"
- "Bonjour que peux-tu faire" → general_chat, agent=null, direct_response="Je suis Tony..."
- "Olá o que fazes?" → general_chat, lang=pt, direct_response en PT-PT"""


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


async def tony_classify(message: str) -> dict:
    """Appelle Tony (gemma2:2b) pour classifier l'intention."""
    prompt = f"{TONY_SYSTEM}\n\nMESSAGE UTILISATEUR: {message}\n\nJSON:"
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0)) as client:
            res = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": TONY_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 400},
                },
            )
            raw = res.json().get("message", {}).get("content", "")
            # Extraire JSON de la réponse
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(raw[start:end])
    except Exception as e:
        logger.warning(f"Tony classify error: {e}")
    # Fallback: general_chat en français
    return {
        "intent": "general_chat",
        "lang": "fr",
        "agent": None,
        "ack_message": None,
        "estimated_delay": None,
        "direct_response": "Je suis Tony, votre assistant LEGA. Comment puis-je vous aider ?",
    }


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
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 800},
                },
            )
            return res.json().get("message", {}).get("content", "Résultat indisponible.")
    except Exception as e:
        logger.error(f"Max Search error: {e}")
        return f"⚠️ Erreur Max Search: {str(e)[:100]}"


async def run_sam_comms(payload: dict, lang: str) -> str:
    """Sam Comms: génération d'emails professionnels (gemma4:e2b)."""
    context_msg = payload.get("message", "")
    lang_instr = "Français professionnel." if lang == "fr" else ("Português europeu profissional (PT-PT)." if lang == "pt" else "Professional English.")
    prompt = f"""Tu es Sam Comms, expert communication B2B pour PME TP.
Langue: {lang_instr}

DEMANDE: {context_msg}

Génère:
📧 OBJET EMAIL
📝 CORPS DU MESSAGE (ton professionnel mais chaleureux, 3-5 paragraphes)
📋 ACTIONS SUGGÉRÉES (suivi, relance, délai)"""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            res = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": AGENT_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {"temperature": 0.4, "num_predict": 600},
                },
            )
            return res.json().get("message", {}).get("content", "Résultat indisponible.")
    except Exception as e:
        return f"⚠️ Erreur Sam Comms: {str(e)[:100]}"


AGENT_EXECUTORS = {
    "max_search": run_max_search,
    "sam_comms": run_sam_comms,
}


# ── DB helpers ───────────────────────────────────────────────────────────────

async def db_connect():
    return await asyncpg.connect(DB_URL)


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


@app.on_event("startup")
async def startup():
    asyncio.create_task(task_worker())
    asyncio.create_task(trial_expiry_cron())
    logger.info("LEGA API v1.0 started — Tony + Worker + Trial cron online")


# ── WebSocket ────────────────────────────────────────────────────────────────

@app.websocket("/ws/stream")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    session_id = str(uuid.uuid4())
    active_connections[session_id] = ws
    user_id = await get_or_create_user(session_id)
    logger.info(f"WS connected: {session_id} (user {user_id[:8]})")

    try:
        await ws.send_json({
            "type": "agent_response",
            "payload": "🚜 Bonjour ! Je suis Tony, votre assistant LEGA. Comment puis-je vous aider ?",
            "metadata": {"session_id": session_id, "llm": TONY_MODEL},
        })

        while True:
            data = await ws.receive_text()
            payload_raw = json.loads(data)

            if payload_raw.get("type") == "ping":
                continue

            user_msg = payload_raw.get("payload", "")
            if not user_msg.strip():
                continue

            logger.info(f"WS [{session_id[:8]}]: {user_msg[:80]}")

            # Tony classifie l'intention
            classification = await tony_classify(user_msg)
            intent = classification.get("intent", "general_chat")
            lang = classification.get("lang", "fr")
            agent = classification.get("agent")

            if intent == "general_chat" or not agent:
                # Réponse directe de Tony
                direct = classification.get("direct_response") or (
                    "Je suis Tony, votre assistant LEGA. Je peux vous aider à rechercher des machines TP, rédiger des emails, analyser des photos, et surveiller le marché."
                    if lang == "fr" else
                    "Sou o Tony, o assistente LEGA. Posso ajudá-lo a pesquisar máquinas TP, redigir e-mails e monitorizar o mercado."
                )
                await ws.send_json({
                    "type": "agent_response",
                    "payload": direct,
                    "metadata": {"intent": intent, "lang": lang, "llm": TONY_MODEL},
                })

            else:
                # Agent requis → vérifier abonnement si premium
                latency_map = {"max_search": 180, "sam_comms": 90, "visa_vision": 10}
                estimated = latency_map.get(agent, 120)

                if agent in PREMIUM_AGENTS:
                    sub_status = await check_subscription(user_id, agent)

                    if sub_status not in ("active", "trial"):
                        # Pas abonné ou trial expiré → activer trial auto + notifier admin
                        is_renewal = sub_status == "expired"
                        await activate_trial(user_id, agent)
                        logger.info(f"Trial activé: user {user_id[:8]} → {agent}")

                        # Message upsell / trial activé
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

                        # Notification Telegram admin
                        tg_msg = (
                            f"🆕 <b>Trial activé</b>\n"
                            f"Agent : <code>{agent}</code>\n"
                            f"Session : <code>{session_id[:12]}</code>\n"
                            f"Message : {user_msg[:200]}\n"
                            f"Langue : {lang}\n"
                            f"Renouvellement : {'oui' if is_renewal else 'non'}"
                        )
                        asyncio.create_task(notify_telegram(tg_msg))

                        # Enregistrer en activation_requests pour suivi admin
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

                # Créer la tâche en DB
                task_id = await create_task(
                    session_id=session_id,
                    agent_name=agent,
                    payload={"message": user_msg, "lang": lang},
                    lang=lang,
                    estimated_latency=estimated,
                )
                logger.info(f"Task created: {task_id} → {agent}")

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
                json={"model": TONY_MODEL, "messages": [{"role": "user", "content": full_prompt}], "stream": False, "options": {"temperature": 0.3, "num_predict": 2048}},
            )
            reply = res.json().get("message", {}).get("content", "Pas de réponse")
        return {"content": reply, "model": TONY_MODEL}
    except Exception as e:
        return {"content": f"Erreur: {str(e)[:100]}", "model": TONY_MODEL}


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
async def get_registry():
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
async def get_task(task_id: str):
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
async def list_tasks(session_id: str = None, status: str = None, limit: int = 20):
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
            res = await client.post(f"{OLLAMA_URL}/api/chat", json={"model": TONY_MODEL, "messages": [{"role": "user", "content": prompt}], "stream": False, "options": {"temperature": 0.3, "num_predict": 500}})
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
            res = await client.post(f"{OLLAMA_URL}/api/chat", json={"model": TONY_MODEL, "messages": [{"role": "user", "content": prompt}], "stream": False, "options": {"temperature": 0.3, "num_predict": 400}})
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
            res = await client.post(f"{OLLAMA_URL}/api/chat", json={"model": TONY_MODEL, "messages": [{"role": "user", "content": prompt}], "stream": False, "options": {"temperature": 0.4, "num_predict": 350}})
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
            res = await client.post(f"{OLLAMA_URL}/api/chat", json={"model": TONY_MODEL, "messages": [{"role": "user", "content": prompt}], "stream": False, "options": {"temperature": 0.4, "num_predict": 400}})
            return {"crew": "veille", "result": res.json().get("message", {}).get("content", "Erreur"), "model": TONY_MODEL, "lang": lang, "sources": listings}
    except Exception as e:
        return {"crew": "veille", "error": str(e)[:100]}


# ── Sources CRUD ──────────────────────────────────────────────────────────────

@app.get("/api/sources")
async def api_get_sources():
    try:
        conn = await db_connect()
        rows = await conn.fetch("SELECT id, url, category, region, added_by, created_at FROM sources ORDER BY created_at DESC")
        await conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/sources/add")
async def add_source(request: dict):
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
async def api_delete_source(source_id: int):
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
async def create_product(product: ProductCreate):
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
async def update_product(product_id: int, product: ProductUpdate):
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
async def delete_product(product_id: int):
    try:
        conn = await db_connect()
        await conn.execute("UPDATE products SET status='archived', updated_at=NOW() WHERE id=$1", product_id)
        await conn.close()
        return {"status": "ok", "message": "Produit archivé"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/products/{product_id}/upload")
async def upload_product_image(product_id: int, file: UploadFile = File(...)):
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
async def patch_product_status(product_id: int, request: dict):
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
async def update_agent_status(name: str, request: dict):
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
async def get_monitoring():
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
async def get_activations(status: str = None):
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
async def review_activation(activation_id: int, request: dict):
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
