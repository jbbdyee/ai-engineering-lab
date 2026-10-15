#!/usr/bin/env bash
# Register the course credentials in n8n from the .env file, so the API key is never typed into
# a workflow or committed to git.
#   cd Last3Mon/65/n8n && docker compose up -d && bash register-credentials.sh
#   N8N_CONTAINER=<name> if your n8n container has another name (docker ps).
#
# Creates (or updates) two credentials with fixed ids that the course workflows already use:
#   OpenAI (.env)  id openAiCourse0001  <- OPENAI_API_KEY (and OPENAI_BASE_URL if set)
#   Ollama local   id ollamaLocal0001   <- http://ollama:11434 (fallback model)
#
# Outage drill (day 72): OPENAI_API_KEY=sk-invalid-key-for-drill-000000 bash register-credentials.sh
# Restore: bash register-credentials.sh
set -euo pipefail
cd "$(dirname "$0")"

# The nearest .env (this folder first, then the folders above) that has OPENAI_API_KEY.
env_file=""
dir="$PWD"
while [ "$dir" != "/" ]; do
  if [ -f "$dir/.env" ] && grep -q '^OPENAI_API_KEY=' "$dir/.env"; then
    env_file="$dir/.env"
    break
  fi
  dir="$(dirname "$dir")"
done
if [ -z "$env_file" ]; then
  echo "No .env with OPENAI_API_KEY found. Copy Last3Mon/.env.example to Last3Mon/.env and fill it in." >&2
  exit 1
fi

value() { { grep -E "^$1=" "$env_file" || true; } | tail -1 | cut -d= -f2- | sed -e 's/^["'\'']//' -e 's/["'\'']$//'; }
key="${OPENAI_API_KEY:-$(value OPENAI_API_KEY)}"   # a key exported in the shell wins (used for outage drills)
base_url="$(value OPENAI_BASE_URL)"
base_url="${base_url:-https://api.openai.com/v1}"
if ! printf '%s' "$key" | grep -Eq '^[A-Za-z0-9_-]{20,}$'; then
  echo "OPENAI_API_KEY in $env_file is empty or does not look like an API key." >&2
  exit 1
fi

credentials=$(printf '[{"id":"openAiCourse0001","name":"OpenAI (.env)","type":"openAiApi","data":{"apiKey":"%s","url":"%s"}},{"id":"ollamaLocal0001","name":"Ollama local","type":"ollamaApi","data":{"baseUrl":"http://ollama:11434"}}]' "$key" "$base_url")

# The JSON goes through stdin into a temporary file inside the container, then is deleted.
container="${N8N_CONTAINER:-day65-n8n-n8n-1}"
docker inspect "$container" >/dev/null 2>&1 || { echo "n8n container '$container' not found. Start n8n first: cd Last3Mon/65/n8n && docker compose up -d" >&2; exit 1; }
printf '%s' "$credentials" | docker exec -i "$container" sh -c \
  'cat > /tmp/course-credentials.json && n8n import:credentials --input=/tmp/course-credentials.json; status=$?; rm -f /tmp/course-credentials.json; exit $status'

echo "Registered 'OpenAI (.env)' and 'Ollama local' from $env_file"
