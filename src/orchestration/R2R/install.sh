#!/usr/bin/env bash
#
# Install R2R:
# 1. Validates a running docker installation
# 2. Pull R2R docker configurations files from its GitHub repository
# 3. Validates our local overrides files exist
# 4. Create required volume directories
# 5. Pull R2R docker images

set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR"

source "$SCRIPT_DIR/common_config.sh"

trap 'log "❌ An unexpected error occurred."' ERR

#
# 1. Validate required tools
#
log "🔍 Checking required dependencies..."

# Check for Docker
if ! command -v docker &> /dev/null; then
  log "❌ Error: Docker is not installed. Please install Docker first."
  exit 1
fi

# Run a test container to validate Docker functionality
log "🚀 Testing Docker installation..."
if ! docker run --rm hello-world &> /dev/null; then
  log "❌ Error: Docker is installed but not working correctly."
  exit 1
fi
log "✅ Docker test successful."

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
# 2. Clone the R2R repository and extract only the docker subdirectory
#
REPO_URL="https://github.com/SciPhi-AI/R2R.git"
TEMP_DIR=".tmp_r2r_clone"
TARGET_DIR="$SUBDIR"

log "📥 Fetching directory $SUBDIR from $REPO_URL..."
rm -rf "$TEMP_DIR"
git clone --filter=blob:none --no-checkout "$REPO_URL" "$TEMP_DIR"
cd "$TEMP_DIR"
git sparse-checkout init --cone
git sparse-checkout set "$SUBDIR"
git checkout
cd "$SCRIPT_DIR"

# Remove existing target directory if it exists
if [[ -d "./$TARGET_DIR" ]]; then
  rm -rf "./$TARGET_DIR"
fi
mv "$TEMP_DIR/$SUBDIR" "./$TARGET_DIR"
rm -rf "$TEMP_DIR"
log "✅ Successfully fetched $SUBDIR from $REPO_URL."

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

#
# 3. Create required volume directories
#
log "📁 Creating required volume directories..."

# Check if VOLUMES_DIR exists
if [[ ! -d "$VOLUMES_DIR" ]]; then
  log "Creating volumes directory: $VOLUMES_DIR"
  mkdir -p "$VOLUMES_DIR"
fi

# Create all required subdirectories for bind mounts
REQUIRED_DIRS=(
  "$VOLUMES_DIR/postgres_data"
  "$VOLUMES_DIR/hatchet_rabbitmq_data"
  "$VOLUMES_DIR/hatchet_rabbitmq_conf"
  "$VOLUMES_DIR/hatchet_certs"
  "$VOLUMES_DIR/hatchet_config"
  "$VOLUMES_DIR/hatchet_api_key"
  "$VOLUMES_DIR/hatchet_postgres_data"
)

for dir in "${REQUIRED_DIRS[@]}"; do
  if [[ ! -d "$dir" ]]; then
    log "Creating directory: $dir"
    mkdir -p "$dir"
    chmod 755 "$dir"
  else
    log "Directory already exists: $dir"
  fi
done

log "✅ All required volume directories created."

#
# 4. Pull R2R images
#
log "📥 Pulling Docker images..."
docker compose -f "$COMPOSE_FILE" -f "$OVERRIDE_FILE" pull

log "✅ Images pulled successfully."

#
# 5. Creating Python virtual environment for smoke tests
# Note: Alternative would be to use `uvx` which creates the venv on the fly
#
log "🔧 Creating Python virtual environment for smoke tests..."
if [ ! -d "$VENV_DIR" ]; then
    uv venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    uv pip install -r "$SMOKE_DIR/requirements.txt"
    deactivate
    log "✅ Virtual environment created and dependencies installed."
else
    log "✅ Virtual environment already exists."
fi

log "🎉 Installation completed successfully!"
log "📍 Script directory: $SCRIPT_DIR"
