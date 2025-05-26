#!/usr/bin/env bash
#
# Revert the directory to git-only files

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/common_config.sh"

trap 'log "❌ An unexpected error occurred."' ERR

# Change to the base directory to ensure all relative paths work
cd "$BASE_DIR"


log "🧹 Cleaning up files to revert to a fresh-from-repo state..."
log "📍 Working in directory: $BASE_DIR"

log "🧹 Removing R2R upstream configuration files..."
if [[ -d "$CONFIG_UPSTREAM_DIR" ]]; then
    rm -rf "$CONFIG_UPSTREAM_DIR"
    log "✅ Removed $CONFIG_UPSTREAM_DIR directory"
else
    log "ℹ️  $CONFIG_UPSTREAM_DIR directory not found (already clean)"
fi

log "🧹 Removing test file..."
if [[ -f "$TEST_FILE" ]]; then
    rm -f "$TEST_FILE"
    log "✅ Removed $TEST_FILE"
else
    log "ℹ️  $TEST_FILE not found (already clean)"
fi

log "🧹 Removing Python cache files..."
# Remove cache in smoke-tests directory if it exists
if [[ -d "$SMOKE_DIR" ]]; then
    rm -rf "$SMOKE_DIR"/__pycache__
    rm -rf "$SMOKE_DIR"/.ropeproject
    log "✅ Cleaned Python cache in smoke-tests directory"
else
    log "ℹ️  Smoke-tests directory not found"
fi

# Remove ropeproject in the script directory
if [[ -d "$SCRIPT_DIR/.ropeproject" ]]; then
    rm -rf "$SCRIPT_DIR/.ropeproject"
    log "✅ Removed .ropeproject in script directory"
else
    log "ℹ️  .ropeproject not found in script directory"
fi

# Prune dangling images, stopped containers, unused networks
log "🧹 Cleaning up Docker resources..."

# Check if Docker is available before attempting cleanup
if command -v docker &> /dev/null && docker info &> /dev/null; then
    log "🧹 Cleaning up dangling Docker images..."
    docker image prune -f

    log "🧹 Cleaning up stopped containers..."
    docker container prune -f

    log "🧹 Cleaning up unused networks..."
    docker network prune -f

    log "✅ Docker cleanup completed"
else
    log "⚠️  Docker not available or not running - skipping Docker cleanup"
fi

log "🎉 Cleanup completed successfully!"
