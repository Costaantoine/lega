from crews.base_crew import load_kb, run

def gen_fiche(desc, lang="fr", model="gemma2:2b"):
    ctx = load_kb()
    prompt = f"""Tu es un expert machines TP d'occasion.
📚 CONTEXTE :
{ctx}
📋 MACHINE : "{desc}"
🎯 FORMAT OBLIGATOIRE :
🚜 TITRE (Marque+Modèle+Année)
⚙️ SPECS (Heures, kW, Poids, Options)
✅ ÉTAT & POINTS FORTS (3 max)
💶 PRIX CONSEILLÉ (€ HT UE)
📝 DESC VENDEUR (3-4 lignes pro)
🔗 SOURCES (citer 1-2 fournisseurs du contexte si pertinent)
Réponds UNIQUEMENT avec ce format. { 'FRANÇAIS.' if lang=='fr' else 'PORTUGAIS EUROPE.' }"""
    try: return {"status":"ok","data":run("Expert TP","Générer fiche produit",prompt,model)}
    except Exception as e: return {"status":"error","error":str(e)[:150]}
