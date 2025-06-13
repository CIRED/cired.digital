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


# Verify configuration files exist
validate_config_files

log "🚀 Starting services..."
docker_compose_cmd up -d
log "✅ Docker Compose started successfully."
