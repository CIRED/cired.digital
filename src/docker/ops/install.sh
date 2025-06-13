#!/usr/bin/env bash
#
# Install R2R:
# 1. Validates a running docker installation
# 2. Pull R2R docker configurations files from its GitHub repository
# 3. Pull R2R docker images

set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR"

source "$SCRIPT_DIR/common_config.sh"
ensure_docker --smoke-test

trap 'log "❌ An unexpected error occurred."' ERR

#
# 1. Validate required tools
#
log "🔍 Checking required dependencies..."


# Display Docker version
log "🐳 Docker version:"
docker --version

# Check for uv (required for validate.sh)
if ! command -v uv &> /dev/null; then
  log "❌ Error: 'uv' is not installed. Please install uv first."
  log "   You can install it with: pipx install uv"
  exit 1
fi

#
# 2. Pulling the docker/ subdir of the R2R repository
#
REPO_URL="https://github.com/SciPhi-AI/R2R.git"
SOURCE_DIR="docker"
TEMP_DIR=".tmp_r2r_clone"
TARGET_DIR="$CONFIG_UPSTREAM_DIR"

log "📥 Fetching directory $SOURCE_DIR from $REPO_URL..."
rm -rf "$TEMP_DIR"
git clone --filter=blob:none --no-checkout "$REPO_URL" "$TEMP_DIR"
cd "$TEMP_DIR"
git sparse-checkout init --cone
git sparse-checkout set "$SOURCE_DIR"
git checkout
cd "$SCRIPT_DIR"

# Remove existing target directory if it exists
if [[ -d "$TARGET_DIR" ]]; then
  rm -rf "$TARGET_DIR"
fi
mv "$TEMP_DIR/$SOURCE_DIR" "$TARGET_DIR"
rm -rf "$TEMP_DIR"
log "✅ Successfully fetched $SOURCE_DIR from $REPO_URL into $TARGET_DIR."

# Verify configuration files exist
validate_config_files

#
# 3. Pull R2R images
#
log "📥 Pulling Docker images..."
docker compose pull

log "✅ Images pulled successfully."

log "🎉 Installation completed successfully!"
log "📍 Script directory: $SCRIPT_DIR"
