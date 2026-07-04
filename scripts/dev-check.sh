#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

set -a
[[ -f .env ]] && source .env
set +a

required_services=(postgres redis qdrant ollama backend frontend n8n)

info() {
  printf '[dev-check] %s\n' "$1"
}

fail() {
  printf '[dev-check] ERROR: %s\n' "$1" >&2
  exit 1
}

command -v docker >/dev/null 2>&1 || fail "Docker is not installed or not on PATH."
docker info >/dev/null 2>&1 || fail "Docker is not running."
info "Docker is running."

[[ -f .env ]] || fail ".env is missing. Run: cp .env.example .env"
info ".env exists."

running_services="$(docker compose ps --services --filter status=running 2>/dev/null || true)"
for service in "${required_services[@]}"; do
  if ! printf '%s\n' "$running_services" | grep -qx "$service"; then
    fail "Container '$service' is not running. Run: docker compose up -d"
  fi
done
info "Required containers are running."

curl -fsS "${BACKEND_PUBLIC_URL:-http://localhost:8000}/health" >/tmp/voice-agent-health.json \
  || fail "Backend /health is not healthy. Check: docker compose logs -f backend"
info "Backend /health works."

docker compose exec -T postgres pg_isready \
  -U "${POSTGRES_USER:-voice_agent}" \
  -d "${POSTGRES_DB:-voice_agent}" >/dev/null \
  || fail "PostgreSQL is not accepting connections."
info "PostgreSQL connection works."

docker compose exec -T redis redis-cli ping | grep -q PONG \
  || fail "Redis ping failed."
info "Redis connection works."

curl -fsS http://localhost:6333/ >/dev/null \
  || fail "Qdrant endpoint is not reachable at http://localhost:6333/."
info "Qdrant endpoint works."

curl -fsS http://localhost:11434/api/tags >/tmp/voice-agent-ollama-tags.json \
  || fail "Ollama endpoint is not reachable at http://localhost:11434/api/tags."
info "Ollama endpoint works."

if grep -Eq '"models"[[:space:]]*:[[:space:]]*\[\]' /tmp/voice-agent-ollama-tags.json; then
  info "No Ollama models are installed."
  info "Run: docker compose exec ollama ollama pull <model-name>"
else
  info "At least one Ollama model is installed."
fi

info "Development stack check complete."
