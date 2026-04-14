from crews.base_crew import load_kb, run
import web_utils

async def gen_veille(criteres, lang="fr", model="gemma2:2b"):
    try:
        listings = await web_utils.search_smart(criteres, max_results=4)
        txt = "\n".join([f"- {l.get('title','')} | {l.get('price','')}" for l in listings]) if listings else "Aucune annonce tob.pt"
    except: txt = "Scraping indisponible"
    ctx = load_kb()
    prompt = f"""Assistant veille marché TP.
📚 CONTEXTE : {ctx}
🌐 ANNONCES RÉELLES : {txt}
🔍 CRITÈRES : "{criteres}"
🎯 FORMAT :
🚨 3 ALERTES MARCHÉ
💡 CONSEILS PRIX (vs annonces / vs FR)
📩 MESSAGE CLIENT (1-2 lignes pro)
Réponds UNIQUEMENT avec ce format. { 'FRANÇAIS.' if lang=='fr' else 'PORTUGAIS EUROPE.' }"""
    try: return {"status":"ok","data":run("Expert Veille","Générer veille marché",prompt,model,0.4)}
    except Exception as e: return {"status":"error","error":str(e)[:150]}
