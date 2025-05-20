#!/usr/bin/env bash
# docker_snapshot.sh - Snapshot Docker volumes for myrag project

set -Eeuo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR"

source "$SCRIPT_DIR/common_config.sh"

SNAPSHOT_NAME="${1:-${SNAPSHOT_PREFIX}}"
BACKUP_DIR="${ARCHIVES_DIR}/${SNAPSHOT_NAME}"
mkdir -p "$BACKUP_DIR"

log "Checking for running containers..."
if docker ps --format '{{.Names}}' | grep -E "${PROJECT_NAME}" | grep -q .; then
    log -e "Aborting: Docker containers for $PROJECT_NAME are running. Please stop them before taking a snapshot."
    exit 1
fi

log "📦 Creating snapshots for all volumes in project $PROJECT_NAME"

# Get all volumes for this project
project_volumes=$(docker volume ls --filter "name=${PROJECT_NAME}" -q)

if [ -z "$project_volumes" ]; then
    log -e "No volumes found for project $PROJECT_NAME"
    exit 2
fi

# Backup each volume
for volume in $project_volumes; do
    log "Backing up volume: $volume"

    # Extract the short name (without project prefix)
    volume_short_name=$(echo "$volume" | sed "s/${PROJECT_NAME}_//")

    # Create tar.gz of the volume
    if docker run --rm \
        -v "$volume:/source" \
        -v "$BACKUP_DIR:/backup" \
        alpine tar -czf "/backup/${volume_short_name}.tar.gz" -C /source .; then
        log "✅ Successfully backed up $volume to ${BACKUP_DIR}/${volume_short_name}.tar.gz"
    else
        log -e "Failed to backup volume $volume"
        exit 3
    fi
done

# Create a single archive of all volume backups
log "Creating consolidated archive..."
tar -czf "${ARCHIVES_DIR}/${SNAPSHOT_NAME}.tar.gz" -C "${ARCHIVES_DIR}" "${SNAPSHOT_NAME}"

# Cleanup individual volume backups
rm -rf "$BACKUP_DIR"

log "✅ Snapshot completed: ${ARCHIVES_DIR}/${SNAPSHOT_NAME}.tar.gz"
