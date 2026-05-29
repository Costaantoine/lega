import asyncio, json, sys, time, os

sys.stdout = open("/tmp/test_free_agents.log", "w", buffering=1)

PROMPTS = [
    {"key": "tony", "msg": "Bonjour Tony, présente-toi. Que peux-tu faire pour moi ?",
     "desc": "Tony (orchestrateur) — présentation générale",
     "payload": {"payload": "Bonjour Tony, présente-toi. Que peux-tu faire pour moi ?"}},
    {"key": "lea", "msg": "Bonjour, je cherche une pelle sur chenilles pour chantier. Quels produits avez-vous ?",
     "desc": "Léa (standardiste vitrine) — question catalogue",
     "payload": {"payload": "Bonjour, je cherche une pelle sur chenilles pour chantier. Quels produits avez-vous ?", "preferred_agent": "lea", "canal": "web"}},
    {"key": "cal", "msg": "Quels sont les événements et tâches prévus aujourd'hui dans mon agenda ?",
     "desc": "Cal (Agenda) — planning du jour",
     "payload": {"payload": "Quels sont les événements et tâches prévus aujourd'hui dans mon agenda ?"}},
    {"key": "bell", "msg": "Je veux parler à un commercial pour une machine TP",
     "desc": "Bell (standardiste voix) — demande mise en relation",
     "payload": {"payload": "Je veux parler à un commercial pour une machine TP"}},
]

async def test_one(prompt, timeout_total=120):
    key = prompt["key"]; desc = prompt["desc"]; msg = prompt["msg"]
    print(f"\n{'='*60}\n📋 Test: {desc}\n   Prompt: {msg[:80]}...\n{'='*60}")

    import websockets
    start = time.time()
    try:
        async with websockets.connect("ws://localhost:8002/ws/stream", ping_interval=None, close_timeout=10) as ws:
            welcome_raw = await asyncio.wait_for(ws.recv(), timeout=15)
            welcome = json.loads(welcome_raw)
            print(f"   ✅ Welcome reçu (type={welcome.get('type')}) — +{time.time()-start:.1f}s")

            await ws.send(json.dumps(prompt["payload"]))
            print(f"   📤 Message envoyé — +{time.time()-start:.1f}s")

            final = None
            thinking_count = 0
            deadline = time.time() + timeout_total
            while time.time() < deadline:
                remaining = deadline - time.time()
                if remaining <= 0: break
                try:
                    resp_raw = await asyncio.wait_for(ws.recv(), timeout=min(remaining, 60))
                    data = json.loads(resp_raw)
                    rtype = data.get("type", "?")
                    agent = data.get("metadata", {}).get("agent", "?")
                    status = data.get("metadata", {}).get("status", "")
                    payload = str(data.get("payload", ""))[:250]

                    if rtype == "thinking":
                        thinking_count += 1
                        print(f"   💭 thinking ({thinking_count}) agent={agent} — +{time.time()-start:.1f}s")
                    elif rtype == "agent_response":
                        print(f"   ✅ agent_response | agent={agent} | status={status}")
                        print(f"      \"{payload}\"")
                        final = {"key": key, "desc": desc, "success": status not in ("blocked","error","locked"),
                                 "response_agent": agent, "status": status or "ok", "preview": payload[:150],
                                 "thinking_count": thinking_count, "elapsed": round(time.time()-start, 1)}
                        break
                    elif rtype == "error":
                        print(f"   ❌ error: {payload}")
                        final = {"key": key, "desc": desc, "success": False, "response_agent": agent,
                                 "status": "error", "preview": payload[:150],
                                 "thinking_count": thinking_count, "elapsed": round(time.time()-start, 1)}
                        break
                except asyncio.TimeoutError:
                    print(f"   ⚠️ Timeout attente — +{time.time()-start:.1f}s")
                    break
            if final is None:
                final = {"key": key, "desc": desc, "success": False, "response_agent": "timeout",
                         "status": "timeout", "preview": f"Aucune réponse après {timeout_total}s",
                         "thinking_count": thinking_count, "elapsed": -1}
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        final = {"key": key, "desc": desc, "success": False, "response_agent": "error",
                 "status": f"error: {str(e)[:60]}", "preview": str(e)[:150],
                 "thinking_count": 0, "elapsed": -1}
    return final

async def main():
    print("\n🧪 TEST DES AGENTS GRATUITS LEGA")
    print(f"Heure: {time.strftime('%H:%M:%S')}")

    results = []
    for p in PROMPTS:
        r = await test_one(p, timeout_total=120)
        results.append(r)
        await asyncio.sleep(2)

    # Summary
    print("\n"+"="*60)
    print("📊 RAPPORT DE TEST — AGENTS GRATUITS LEGA")
    print("="*60)
    print(f"{'Agent':<8} {'Statut':<12} {'Temps':<8} {'Réponse':<15} {'Aperçu'}")
    print("-"*60)
    for r in results:
        icon = "✅" if r["success"] else "❌"
        elapsed = f"{r['elapsed']}s" if r["elapsed"] > 0 else "ERR"
        print(f"{icon} {r['key']:<6} {r['status']:<12} {elapsed:<8} {r['response_agent']:<15} {r['preview'][:60]}")

    success = sum(1 for r in results if r["success"])
    print(f"\n📈 Résultat: {success}/{len(results)} succès")

    report = {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"), "total": len(results),
              "success": success, "failed": len(results)-success, "results": results}
    os.makedirs("/opt/bvi/logs", exist_ok=True)
    rp = f"/opt/bvi/logs/qa-free-agents-{time.strftime('%Y-%m-%d-%H')}.json"
    with open(rp, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n📄 Rapport sauvegardé: {rp}")
    print("\n✅ TEST TERMINÉ")
    sys.stdout.close()

asyncio.run(main())
