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
    execute_remote '{
  set -e
  echo "[INFO] Cleaning repo"
  rm -f uv.lock
  git reset --hard
  git clean -fd
  echo "[INFO] Pulling changes"
  git pull
  echo "[INFO] Stopping services"
  deploy/ops/down.sh
  echo "[INFO] Starting services"
  deploy/ops/up.sh
  echo "[INFO] Validating"
  ENVIRONMENT=production deploy/ops/validate.sh
} | tee -a ~/deploy.log'
    log "✅ Running tests on the server."
    BASE_URL=http://cired.digital pytest -n 8
    log "✅ Remote deployment completed."
else
    log "🚀 Starting local deployment..."
    cd "$BASE_DIR/.."
    git pull
    "$SCRIPT_DIR/down.sh"
    "$SCRIPT_DIR/up.sh"
    "$SCRIPT_DIR/validate.sh"
    log "✅ Local deployment completed successfully."
fi
