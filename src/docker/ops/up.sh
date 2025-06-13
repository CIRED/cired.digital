#!/usr/bin/env bash
#
# Starts R2R
#

set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR"
source "$SCRIPT_DIR/common_config.sh"
ensure_docker
trap 'log "❌ An unexpected error occurred."' ERR

# Validate we have docker
if ! command -v docker &> /dev/null; then
  log "❌ Error: Docker is not installed or not in PATH."
  log "    To install Docker from Docker's official repository:"
  log "    # Add Docker's official GPG key"
  log "    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg"
  log "    # Add Docker repository"
  log "    echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu focal stable' | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null"
  log "    # Install Docker Engine"
  log "    sudo apt update && sudo apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin"
  log "    # Or use the convenience script: curl -fsSL https://get.docker.com | sh"
  log "    For other systems: https://docs.docker.com/get-docker/"
  exit 1
fi

if ! docker info > /dev/null 2>&1; then
  log "Error: Docker is installed but not working correctly."
  log "    Possible causes:"
  log "    - Docker daemon is not running (try: sudo systemctl start docker)"
  log "    - Permission issue (try: sudo usermod -aG docker $USER, then log out/in)"
  log "    - Docker socket permissions"
  exit 1
fi

# Verify configuration files exist
validate_config_files

log "🚀 Starting services..."
docker_compose_cmd up -d
log "✅ Docker Compose started successfully."
