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
log() { echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] $*"; }
trap 'log "❌ An unexpected error occurred."' ERR

# Validate we have docker
if ! command -v docker &> /dev/null; then
  echo "Error: Docker is not installed or not in PATH."
  exit 1
fi

if ! docker info > /dev/null 2>&1; then
  echo "Error: Docker daemon is not running."
  exit 1
fi

# Project, compose and environment file settings
PROJECT_NAME="myrag"
COMPOSE_FILE="./docker/compose.full.yaml"
OVERRIDE_FILE="./compose.override.yaml"
KEYS_FILE="../../../credentials/API_KEYS"

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "Error: Compose file '$COMPOSE_FILE' not found."
  exit 1
fi

if [[ ! -f "$OVERRIDE_FILE" ]]; then
  echo "Error: Override file '$OVERRIDE_FILE' not found."
  exit 1
fi

if [[ ! -f "$KEYS_FILE" ]]; then
  echo "Error: Environment file '$KEYS_FILE' not found."
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
  log "✅ Docker Compose started successfully with profile 'postgres'."
fi

