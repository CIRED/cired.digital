#!/usr/bin/env bash
#
# Install R2R
#

set -euo pipefail
log() { echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] $*"; }
trap 'log "❌ An unexpected error occurred."' ERR

# Validate Docker installation
if ! command -v docker &> /dev/null; then
  echo "Error: Docker is not installed. Please install Docker first."
  exit 1
fi

# Run a test container to validate Docker functionality
log "🚀 Testing Docker installation..."
if ! docker run --rm hello-world &> /dev/null; then
  echo "Error: Docker is installed but not working correctly."
  exit 1
fi
log "✅ Docker test successful."

# Display Docker version
log "🐳 Docker version:"
docker --version

# Project, compose and environment file settings
PROJECT_NAME="myrag"
COMPOSE_FILE="./docker/compose.full.yaml"
OVERRIDE_FILE="./compose.override.yaml"
KEYS_FILE="../../../../credentials/API_KEYS"

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

# Pull images
log "📥 Pulling Docker images..."
docker compose -f "$COMPOSE_FILE" -f "$OVERRIDE_FILE" pull

log "✅ Images pulled successfully."

# Prune dangling images, stopped containers, unused networks
log "🧹 Cleaning up dangling Docker images..."
docker image prune -f

log "🧹 Cleaning up stopped containers..."
docker container prune -f

log "🧹 Cleaning up unused networks..."
docker network prune -f

log "✅ Dangling images, stopped containers, and unused networks cleaned up."
