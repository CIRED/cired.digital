#!/usr/bin/env bash
#
# Install R2R:
# 1. Validates a running docker installation
# 2. Pull R2R docker configurations files from its GitHub repository
# 3. Validates our local overrides files exist
# 4. Pull R2R docker images

set -euo pipefail
log() { echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] $*"; }
trap 'log "❌ An unexpected error occurred."' ERR

#
# 1. Validate Docker installation
#
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

#
# 2. Clone the R2R repository and extract only the docker subdirectory
#
REPO_URL="https://github.com/SciPhi-AI/R2R.git"
TEMP_DIR=".tmp_r2r_clone"
SUBDIR="docker"
TARGET_DIR="$SUBDIR"

log "📥 Fetching $SUBDIR from $REPO_URL..."
rm -rf "$TEMP_DIR"
git clone --filter=blob:none --no-checkout "$REPO_URL" "$TEMP_DIR"
cd "$TEMP_DIR"
git sparse-checkout init --cone
git sparse-checkout set "$SUBDIR"
git checkout
cd -
mv "$TEMP_DIR/$SUBDIR" "./$TARGET_DIR"
rm -rf "$TEMP_DIR"
log "✅ Successfully fetched $SUBDIR from $REPO_URL."

#
# 3. Verify project, compose and environment files
#
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

#
# 4. Pull R2R images
#
log "📥 Pulling Docker images..."
docker compose -f "$COMPOSE_FILE" -f "$OVERRIDE_FILE" pull

log "✅ Images pulled successfully."
