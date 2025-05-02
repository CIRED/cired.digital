#!/usr/bin/env bash
#
# Starts R2R
#
# Instead of adding the keys in clear into docker/env/r2r-full.env,
# we use a local compose override file to pass the secrets
# from the file credentials/API_KEYS which contains
#  OPENAI_API_KEY=sk_...
#  MISTRAL_API_KEY=...

set -euo pipefail
source "./common_config.sh"
trap 'log "❌ An unexpected error occurred."' ERR

# Validate we have docker
if ! command -v docker &> /dev/null; then
  log "Error: Docker is not installed or not in PATH."
  exit 1
fi

if ! docker info > /dev/null 2>&1; then
  log "Error: Docker daemon is not running."
  exit 1
fi

# Verify configuration files exist
if [[ ! -f "$COMPOSE_FILE" ]]; then
  log "Error: Compose file '$COMPOSE_FILE' not found."
  exit 1
fi

if [[ ! -f "$OVERRIDE_FILE" ]]; then
  log "Error: Override file '$OVERRIDE_FILE' not found."
  exit 1
fi

if [[ ! -f "$KEYS_FILE" ]]; then
  log "Error: Environment file '$KEYS_FILE' not found."
  exit 1
fi

log "📦 Project: $PROJECT_NAME"
log "🔧 Compose file: $COMPOSE_FILE"
log "🔧🔧 Override file: $OVERRIDE_FILE"
log "🔑 Env file: $KEYS_FILE"

# Bring up the service
if docker compose -f "$COMPOSE_FILE" -f "$OVERRIDE_FILE" --project-name "$PROJECT_NAME" ps | grep -q 'Up'; then
  log "⚠️ Services are already running."
  docker compose -f "$COMPOSE_FILE" -f "$OVERRIDE_FILE" --project-name "$PROJECT_NAME" ps
else
  source "$KEYS_FILE"
  docker compose -f "$COMPOSE_FILE" -f "$OVERRIDE_FILE" --project-name "$PROJECT_NAME" --profile postgres up -d
  log "✅ Docker Compose started successfully."
fi
