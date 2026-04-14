from crews.base_crew import load_kb, run

def gen_argus(machine, hours=None, cond="bon", lang="fr", model="gemma2:2b"):
    ctx = load_kb()
    h = f"{hours}h" if hours else "non précisé"
    prompt = f"""Expert cotation machines TP.
📚 CONTEXTE : {ctx}
🔍 MACHINE : {machine} | {h} | État: {cond}
🎯 FORMAT :
💶 FOURCHETTE PRIX (€ HT)
📊 FACTEURS (3 puces)
⏱️ DURÉE VENTE ESTIMÉE
💡 CONSEIL MISE EN VENTE (1 phrase)
Réponds UNIQUEMENT avec ce format. { 'FRANÇAIS.' if lang=='fr' else 'PORTUGAIS EUROPE.' }"""
    try: return {"status":"ok","data":run("Expert Cotation","Estimer prix marché",prompt,model,0.4)}
    except Exception as e: return {"status":"error","error":str(e)[:150]}
