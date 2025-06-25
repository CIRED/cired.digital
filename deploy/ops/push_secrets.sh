#!/usr/bin/env bash
# push_secrets.sh - Push secrets directory to remote server
# Usage: ./push_secrets.sh [remote_user] [remote_host] [remote_path]

set -Eeuo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)
SECRETS_DIR="$PROJECT_ROOT/../secrets"

source "$SCRIPT_DIR/common_config.sh"

REMOTE_USER="${1:-admin}"
REMOTE_HOST="${2:-157.180.70.232}"
REMOTE_PATH="${3:-/home/admin/secrets/}"

usage() {
    echo "Usage: $0 [remote_user] [remote_host] [remote_path]"
    echo ""
    echo "Push the project's secrets directory to a remote server."
    exit 1
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
fi

if [ ! -d "$SECRETS_DIR" ]; then
    log -e "Secrets directory not found: $SECRETS_DIR"
    exit 1
fi

log "Preparing to push secrets from $SECRETS_DIR"
log "Destination: $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH"

log "Ensuring remote directory exists..."
if ! ssh "$REMOTE_USER@$REMOTE_HOST" "mkdir -p '$REMOTE_PATH'"; then
    log -e "Failed to create remote directory $REMOTE_PATH"
    exit 2
fi

log "Starting rsync upload..."
if rsync -avz --progress "$SECRETS_DIR/" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH"; then
    log "Setting remote permissions..."
    if ssh "$REMOTE_USER@$REMOTE_HOST" "find '$REMOTE_PATH' -type d -exec chmod 700 {} \; && find '$REMOTE_PATH' -type f -exec chmod 600 {} \;"; then
        log -s "✅ Successfully pushed secrets and set permissions on remote server"
    else
        log -e "Failed to set remote permissions on remote server"
        exit 4
    fi
else
    log -e "Failed to push secrets to remote server"
    exit 3
fi
