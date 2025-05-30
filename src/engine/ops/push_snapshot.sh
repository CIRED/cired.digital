#!/usr/bin/env bash
# push_snapshot.sh - Push Docker volume snapshots to remote server
# Usage: ./push_snapshot.sh [snapshot_name] [remote_user] [remote_host] [remote_path]

set -Eeuo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR"

source "$SCRIPT_DIR/common_config.sh"

# Default values and parameters
SNAPSHOT_NAME="${1:-}"
REMOTE_USER="${2:-admin}"
REMOTE_HOST="${3:-157.180.70.232}"
REMOTE_PATH="${4:-/home/admin/cired.digital/data/archived/R2R/}"

# Function to display usage information
usage() {
    echo "Usage: $0 [snapshot_name] [remote_user] [remote_host] [remote_path]"
    echo ""
    echo "Push Docker volume snapshots to a remote server."
    echo ""
    echo "Parameters:"
    echo "  snapshot_name  - Name of the snapshot to push (default: latest snapshot)"
    echo "  remote_user    - Remote SSH username (default: admin)"
    echo "  remote_host    - Remote SSH host (default: 157.180.70.232)"
    echo "  remote_path    - Remote path to store snapshots (default: /home/admin/cired.digital/data/archived/R2R/)"
    echo ""
    echo "Example:"
    echo "  $0 snapshot_2025-05-21_120000 admin 157.180.70.232 /home/admin/backups"
    exit 1
}


# Check if help is requested
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
fi

# If snapshot name not provided, find the latest snapshot
if [ -z "$SNAPSHOT_NAME" ]; then
    log "No snapshot name provided, finding the latest snapshot..."
    
    # Check if archives directory exists
    if [ ! -d "$ARCHIVES_DIR" ]; then
        log -e "Archives directory $ARCHIVES_DIR does not exist"
        exit 1
    fi
    
    # Find the latest snapshot file
    LATEST_SNAPSHOT=$(find "$ARCHIVES_DIR" -name "*.tar" -type f -print0 | xargs -0 ls -t | head -n 1)
    
    if [ -z "$LATEST_SNAPSHOT" ]; then
        log -e "No snapshots found in $ARCHIVES_DIR"
        exit 1
    fi
    
    SNAPSHOT_NAME=$(basename "$LATEST_SNAPSHOT" .tar)
    SNAPSHOT_FILE="$LATEST_SNAPSHOT"
    
    log "Found latest snapshot: $SNAPSHOT_NAME"
else
    # Construct snapshot file path from provided name
    SNAPSHOT_FILE="${ARCHIVES_DIR}/${SNAPSHOT_NAME}.tar"
    
    # Check if specified snapshot exists
    if [ ! -f "$SNAPSHOT_FILE" ]; then
        log -e "Snapshot file not found: $SNAPSHOT_FILE"
        exit 1
    fi
fi

log "Preparing to push snapshot: $SNAPSHOT_NAME"
log "  Source file: $SNAPSHOT_FILE"
log "  Destination: $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH"

# Create remote directory if it doesn't exist
log "Ensuring remote directory exists..."
if ! ssh "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $REMOTE_PATH"; then
    log -e "Failed to create remote directory $REMOTE_PATH"
    exit 2
fi

# Calculate file size for logging
FILE_SIZE=$(du -h "$SNAPSHOT_FILE" | cut -f1)
log "Snapshot size: $FILE_SIZE"

# Upload the snapshot with progress indication
log "Starting upload..."
if rsync -avz --progress "$SNAPSHOT_FILE" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"; then
    log -s "✅ Successfully pushed snapshot to remote server"
    log -s "Remote location: $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/$(basename "$SNAPSHOT_FILE")"
else
    log -e "Failed to push snapshot to remote server"
    exit 3
fi

# Verify the upload was successful by checking the remote file
log "Verifying upload..."
if ssh "$REMOTE_USER@$REMOTE_HOST" "[ -f \"$REMOTE_PATH/$(basename "$SNAPSHOT_FILE")\" ]"; then
    log -s "Remote file verified successfully"
else
    log -e "Remote file verification failed"
    exit 4
fi

# Log completion timestamp for record-keeping
log "Snapshot push completed at $(date '+%Y-%m-%d %H:%M:%S')"
