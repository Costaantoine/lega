#!/bin/bash
# benchmark_models.sh — Comparaison gemma2:2b vs gemma4:e4b pour LEGA

echo "🚀 BENCHMARK LEGA — Qualité & Vitesse des modèles"
echo "=================================================="

# Prompt test : question RAG qui devrait utiliser knowledge_base.json
PROMPT='Quels sont les fournisseurs de mini-pelles près de Bordeaux avec leurs téléphones ?'

# Fonction pour tester un modèle
test_model() {
  local model=$1
  echo -e "\n🔹 Modèle : $model"
  echo "⏱️  Mesure du temps de réponse..."
  
  start=$(date +%s%N)
  
  response=$(curl -s -X POST http://localhost:11434/api/generate \
    -H "Content-Type: application/json" \
    -d "{
      \"model\": \"$model\",
      \"prompt\": \"$PROMPT\",
      \"stream\": false,
      \"options\": {\"temperature\": 0.3, \"num_predict\": 1024}
    }" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('response',''))")
  
  end=$(date +%s%N)
  duration=$(( (end - start) / 1000000 ))  # en millisecondes
  
  echo "⏱️  Temps : ${duration} ms"
  echo "📝 Réponse (extrait) :"
  echo "$response" | head -c 500
  echo -e "\n..."
  
  # Vérifier si la réponse cite des fournisseurs du rapport
  if echo "$response" | grep -qiE "bergerat|monnoyeur|m3 jcb|codimatra|eysines|mérignac"; then
    echo "✅ Cite des sources du rapport LEGA"
  else
    echo "❌ Réponse générique (pas de citation du contexte)"
  fi
}

# Tester les deux modèles
test_model "gemma2:2b"
test_model "gemma4:e4b"

echo -e "\n✅ Benchmark terminé."
