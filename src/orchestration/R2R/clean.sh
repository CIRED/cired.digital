#!/usr/bin/env bash
#
# Revert the directory to git-only files

set -euo pipefail
log() { echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] $*"; }


SUBDIR="docker"
TEST_FILE="test.txt"

log "🧹 Removing R2R upstream configuration files..."
rm -rf "$SUBDIR"

log "🧹 Removing test file..."
rm -f "$TEST_FILE"

log "🧹 Removing any Python virtual environment..."
rm -rf venv

log "🧹 Removing Python cache..."
rm -rf smoke-tests/__pycache__
rm -rf smoke-tests/.ropeproject

# Prune dangling images, stopped containers, unused networks
log "🧹 Cleaning up dangling Docker images..."
docker image prune -f

log "🧹 Cleaning up stopped containers..."
docker container prune -f

log "🧹 Cleaning up unused networks..."
docker network prune -f
