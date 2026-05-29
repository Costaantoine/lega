#!/bin/bash
set -euo pipefail

PROJECT_ROOT=/opt/bvi
LOGS_DIR=/opt/bvi/logs
WORKSPACE=/opt/claude-code/workspace
DATE=$(date +%Y-%m-%d)
HOUR=$(date +%H)
LOG_FILE=${LOGS_DIR}/qa-${DATE}-${HOUR}.json

source <(grep -E '^TELEGRAM_' ${PROJECT_ROOT}/.env)

notify() {
  curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d chat_id="${TELEGRAM_CHAT_ID}" \
    -d text="$1" \
    -d parse_mode="HTML" > /dev/null 2>&1 || true
}

mkdir -p ${LOGS_DIR}

if ! docker exec claude-code-standalone claude --version > /dev/null 2>&1; then
  notify "BVI QA ERREUR : Claude Code inaccessible"
  exit 1
fi

cp /opt/bvi/scripts/CLAUDE.md ${WORKSPACE}/CLAUDE.md

notify "BVI QA demarre - $(date '+%d/%m/%Y %H:%M') - Test agents CrewAI en cours"

timeout 2700 docker exec \
  -u node \
  claude-code-standalone \
  claude \
  --dangerously-skip-permissions \
  --output-format json \
  -p "Mode QA autonome. Lis CLAUDE.md dans /workspace. Teste tous les agents CrewAI des deux projets BVI. Ecris le rapport JSON complet dans ${LOG_FILE} quand tu as fini." \
  >> ${LOGS_DIR}/claude-raw-${DATE}-${HOUR}.log 2>&1 || true

if [ -f "${LOG_FILE}" ]; then
  TOTAL=$(python3 -c "import json; d=json.load(open('${LOG_FILE}')); print(d['summary']['total'])" 2>/dev/null || echo '?')
  SUCCESS=$(python3 -c "import json; d=json.load(open('${LOG_FILE}')); print(d['summary']['success'])" 2>/dev/null || echo '?')
  FAILED=$(python3 -c "import json; d=json.load(open('${LOG_FILE}')); print(d['summary']['failed'])" 2>/dev/null || echo '?')
  FIXED=$(python3 -c "import json; d=json.load(open('${LOG_FILE}')); print(d['summary']['fixed'])" 2>/dev/null || echo '?')
  notify "BVI QA termine - $(date '+%d/%m/%Y %H:%M') - Total:${TOTAL} Succes:${SUCCESS} Echecs:${FAILED} Corriges:${FIXED}"
else
  notify "BVI QA termine SANS rapport JSON - verifier ${LOGS_DIR}/claude-raw-${DATE}-${HOUR}.log"
fi

find ${LOGS_DIR} -name 'qa-*.json' -mtime +30 -delete 2>/dev/null || true
find ${LOGS_DIR} -name 'claude-raw-*.log' -mtime +7 -delete 2>/dev/null || true
