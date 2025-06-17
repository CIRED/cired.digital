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
running_containers=$(docker ps --format '{{.Names}}' | grep -E "${COMPOSE_PROJECT_NAME}" || true)

if [ -n "$running_containers" ]; then
    log -w "Found running containers for $COMPOSE_PROJECT_NAME, stopping them temporarily..."

    # Store container IDs and their start commands
    container_info=$(docker ps --filter "name=${COMPOSE_PROJECT_NAME}" --format '{{.ID}} {{.Command}}')

    # Stop containers
    docker_compose_cmd stop

    # Wait for containers to stop
    sleep 5

    # Verify they're stopped
    if docker ps --format '{{.Names}}' | grep -E "${COMPOSE_PROJECT_NAME}" | grep -q .; then
        log -e "Failed to stop containers, aborting snapshot"
        exit 1
    fi

    # Set flag to restart containers later
    should_restart=true
else
    should_restart=false
fi

log "📦 Creating snapshots for all volumes in project $COMPOSE_PROJECT_NAME"

# Get all volumes for this project
project_volumes=$(docker volume ls --filter "name=${COMPOSE_PROJECT_NAME}" -q)

if [ -z "$project_volumes" ]; then
    log -e "No volumes found for project $COMPOSE_PROJECT_NAME"
    exit 2
fi

# Backup each volume
for volume in $project_volumes; do
    log "Backing up volume: $volume"

    # Extract the short name (without project prefix)
    volume_short_name=$(echo "$volume" | sed "s/${COMPOSE_PROJECT_NAME}_//")

    # Create tar of the volume
    if docker run --rm \
        -v "$volume:/source" \
        -v "$BACKUP_DIR:/backup" \
        alpine tar -cf "/backup/${volume_short_name}.tar" -C /source .; then
        log "✅ Successfully backed up $volume to ${BACKUP_DIR}/${volume_short_name}.tar"
    else
        log -e "Failed to backup volume $volume"
        exit 3
    fi
done

# Create a single archive of all volume backups
log "Creating consolidated archive..."
tar -cf "${ARCHIVES_DIR}/${SNAPSHOT_NAME}.tar" -C "${ARCHIVES_DIR}" "${SNAPSHOT_NAME}"

# Cleanup individual volume backups
rm -rf "$BACKUP_DIR"

# Restart containers if they were running before
if [ "$should_restart" = true ]; then
    log "Restarting previously running containers..."
    docker_compose_cmd start

    # Verify restart was successful
    restarted_containers=$(docker_compose_cmd ps --services)
    if [ -z "$restarted_containers" ]; then
        log -e "Warning: Failed to restart containers"
    else
        log -s "Containers restarted successfully: $restarted_containers"
    fi
fi

log "✅ Snapshot completed: ${ARCHIVES_DIR}/${SNAPSHOT_NAME}.tar"
