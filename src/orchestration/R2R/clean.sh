#!/usr/bin/env bash
#
# Revert the directory to git-only files

set -euo pipefail
source "./common_config.sh"
trap 'log "❌ An unexpected error occurred."' ERR

log "🧹 Removing R2R upstream configuration files..."
rm -rf "$SUBDIR"

log "🧹 Removing test file..."
rm -f "$TEST_FILE"

log "🧹 Removing any Python virtual environment..."
rm -rf "$VENV_DIR"

log "🧹 Removing Python cache..."
rm -rf "$SMOKE_DIR"/__pycache__
rm -rf "$SMOKE_DIR"/.ropeproject
rm -rf .ropeproject

# Prune dangling images, stopped containers, unused networks
log "🧹 Cleaning up dangling Docker images..."
docker image prune -f

log "🧹 Cleaning up stopped containers..."
docker container prune -f

log "🧹 Cleaning up unused networks..."
docker network prune -f
