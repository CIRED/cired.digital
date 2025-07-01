#!/usr/bin/env bash
#
# Starts R2R
#

REMOTE_MODE=false
if [[ "${1:-}" == "--remote" ]]; then
    REMOTE_MODE=true
    shift
fi

set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR"
source "$SCRIPT_DIR/common_config.sh"
trap 'log "❌ An unexpected error occurred."' ERR

if $REMOTE_MODE; then
    log "🚀 Starting services remotely on $REMOTE_HOST..."
    execute_remote "git pull && deploy/ops/up.sh"
    log "✅ Remote deployment completed successfully."
    exit 0
fi

validate_config_files
ensure_docker

log "🚀 Starting services..."
docker_compose_cmd up -d
log "✅ Docker Compose started successfully."
