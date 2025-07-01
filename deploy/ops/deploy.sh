#!/usr/bin/env bash

set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR"
source "$SCRIPT_DIR/common_config.sh"
trap 'log "❌ An unexpected error occurred."' ERR

REMOTE_MODE=false
if [[ "${1:-}" == "--remote" ]]; then
    REMOTE_MODE=true
    shift
fi

if $REMOTE_MODE; then
    log "🚀 Starting remote deployment to $REMOTE_HOST..."
    execute_remote "cd cired.digital && git pull && deploy/ops/down.sh && deploy/ops/up.sh && deploy/ops/validate.sh"
    log "✅ Remote deployment completed successfully."
else
    log "🚀 Starting local deployment..."
    cd "$BASE_DIR/.."
    git pull
    "$SCRIPT_DIR/down.sh"
    "$SCRIPT_DIR/up.sh"
    "$SCRIPT_DIR/validate.sh"
    log "✅ Local deployment completed successfully."
fi
