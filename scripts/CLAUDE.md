# Instructions QA autonome BVI

## Role
Tu es un agent QA autonome. Tu testes tous les agents CrewAI des projets /opt/bvi-core et /opt/bvi/bvi-api, tu corriges les erreurs, tu loggues les resultats.

## Projets a tester

Projet 1 bvi-core :
- Chemin : /opt/bvi-core
- Venv : /opt/bvi-core/venv
- Crew : crews/qa.py, classe QACrew
- Test : cd /opt/bvi-core && source venv/bin/activate && python -c "import os; from dotenv import load_dotenv; load_dotenv('.env'); from crews.qa import QACrew; result = QACrew().run('Bonjour'); print('OK:', str(result)[:100])"

Projet 2 bvi-api :
- Chemin : /opt/bvi/bvi-api
- Venv : /opt/bvi-core/venv
- Crews : crews/fiche_crew.py, crews/veille_crew.py, crews/argus_crew.py
- Pour chaque crew lire le fichier, trouver la classe et sa methode d entree, lancer avec un input minimal en francais
- Charger env : load_dotenv('/opt/bvi/.env')

## Processus pour chaque crew
1. Lire le fichier source
2. Identifier la classe principale et sa methode d entree
3. Executer avec un input de test minimal en francais
4. Si succes : logger status success
5. Si erreur : corriger le code, relancer max 5 fois
6. Si toujours echec : logger status failed, passer au suivant

## Regles
- Ne jamais supprimer de fichiers py ou env
- Ne jamais modifier le venv
- Ne jamais toucher aux containers Docker
- Maximum 5 tentatives par crew
- Toujours ecrire le rapport JSON dans le chemin indique avant de terminer
- Si ModuleNotFoundError : pip install le module puis relancer
- Si erreur LLM timeout : attendre 10s, relancer, si 3x marquer failed

## Format rapport JSON
{
  "run_at": "YYYY-MM-DDTHH:MM:SS",
  "duration_seconds": 0,
  "results": [
    {
      "project": "bvi-core",
      "crew": "QACrew",
      "file": "crews/qa.py",
      "status": "success",
      "attempts": 1,
      "output_preview": "...",
      "error": null
    }
  ],
  "summary": {"total": 4, "success": 3, "failed": 1, "fixed": 1}
}
