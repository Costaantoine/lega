import json
import os

# Chemin vers la base de connaissances
KB_PATH = os.path.join(os.path.dirname(__file__), "knowledge_base.json")

def search_sources(query: str) -> list:
    """
    COMPÉTENCE AGENT : Sélectionne dynamiquement les meilleures sources
    à scraper selon les mots-clés de la requête.
    """
    try:
        with open(KB_PATH, "r", encoding="utf-8") as f:
            kb = json.load(f)
    except Exception as e:
        print(f"Erreur chargement KB: {e}")
        return []

    query = query.lower()
    relevant_sources = []
    
    # 1. Détection de Marque (Constructeurs)
    brands_map = {"cat": "caterpillar", "volvo": "volvo ce", "jcb": "jcb", "komatsu": "komatsu", "liebherr": "liebherr"}
    
    for brand_key, brand_name in brands_map.items():
        if brand_key in query:
            # Chercher dans Constructeurs
            for item in kb.get("constructeurs", []):
                if brand_key in item["nom"].lower():
                    relevant_sources.append({"name": item["nom"], "url": item["site"], "context": "Source Officielle Constructeur"})
            # Chercher dans Déalers Locaux (ex: Volvo -> V2V TP)
            for item in kb.get("bordeaux_200km", []):
                if brand_key in item["nom"].lower():
                    relevant_sources.append({"name": item["nom"], "url": item["site"], "context": "Déaler Agréé Local"})

    # 2. Détection de Localisation (Bordeaux / Portugal)
    if "bordeaux" in query or "33" in query:
        for item in kb.get("bordeaux_200km", []):
            # Ajouter si pas déjà dans la liste
            if not any(s["url"] == item["site"] for s in relevant_sources):
                relevant_sources.append({"name": item["nom"], "url": item["site"], "context": f"Stock Local ({item['ville']})"})

    if "portugal" in query or "pt" in query:
        for item in kb.get("loueurs_nationaux", []):
            if "PT" in item["nom"] or "ES" in item["nom"]:
                relevant_sources.append({"name": item["nom"], "url": item["site"], "context": "Fournisseur Péninsule Ibérique"})

    # 3. Fallback : Si rien de précis ou recherche générique, ajouter les plateformes
    if not relevant_sources:
        for item in kb.get("plateformes_multi", []):
            relevant_sources.append({"name": item["nom"], "url": item["site"], "context": "Plateforme Multi-marques"})
    
    # Ajouter les plateformes en complément (max 2 pour ne pas surcharger)
    platforms_added = 0
    for item in kb.get("plateformes_multi", []):
        if not any(s["url"] == item["site"] for s in relevant_sources) and platforms_added < 2:
            relevant_sources.append({"name": item["nom"], "url": item["site"], "context": "Plateforme Multi-marques"})
            platforms_added += 1

    return relevant_sources[:8]  # Max 8 sources pour rester rapide
