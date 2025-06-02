#!/usr/bin/env bash
# docker_restore.sh - Restore Docker volumes for cired.digital project

set -Eeuo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR"

source "$SCRIPT_DIR/common_config.sh"

# Verify archive argument and integrity first
if [ $# -lt 1 ]; then
    log -e "Usage: $0 <archive_file>"
    log "Available archives in ${ARCHIVES_DIR}:"
    if [ -d "${ARCHIVES_DIR}" ]; then
        find "${ARCHIVES_DIR}" -name "*.tar" -printf "%f\n" | sort | while read -r archive; do
            log "  - ${archive}"
        done
    else
        log "  (no archive directory found)"
    fi
    exit 1
fi

SNAPSHOT_FILE="$1"

# Resolve snapshot file path
if [[ "$SNAPSHOT_FILE" != */* ]]; then
  log "📂 No path in argument. Looking for snapshot in $ARCHIVES_DIR..."
  SNAPSHOT_FILE="$ARCHIVES_DIR/$SNAPSHOT_FILE"
fi

# Check if the snapshot file exists
if [[ ! -f "$SNAPSHOT_FILE" ]]; then
  log "❌ Snapshot not found: $SNAPSHOT_FILE"
  exit 1
else
  log "📦 Using snapshot file: $SNAPSHOT_FILE"
fi

# Verify archive exists and is readable
if [ ! -f "$SNAPSHOT_FILE" ]; then
    log -e "Archive file not found: $SNAPSHOT_FILE"
    exit 2
fi

if ! tar -tf "$SNAPSHOT_FILE" >/dev/null 2>&1; then
    log -e "Archive is corrupt or invalid: $SNAPSHOT_FILE"
    exit 3
fi

# Use disk-based local tmp rather than RAM-based default mktemp
# because archives will be big.
TEMP_DIR="$(mktemp -d -p .)"
TEMP_DIR="$(realpath "$TEMP_DIR")"

# Clean up temp directory on exit
trap 'rm -rf "$TEMP_DIR"' EXIT

# Now safe to stop containers
# Check and stop running containers
running_containers=$(docker ps --format '{{.Names}}' | grep -E "${PROJECT_NAME}" || true)

if [ -n "$running_containers" ]; then
    log -w "Stopping running containers for $PROJECT_NAME..."
    docker_compose_cmd stop
    sleep 5
    should_restart=true
else
    should_restart=false
fi

# Extract the archive to temp directory (already validated)
log "Extracting archive: $SNAPSHOT_FILE"
tar -xf "$SNAPSHOT_FILE" -C "$TEMP_DIR"

# Find all .tar files in the extracted directory
archive_dir=$(find "$TEMP_DIR" -type d | head -1)
volume_archives=$(find "$archive_dir" -name "*.tar")

if [ -z "$volume_archives" ]; then
    log -e "No volume archives found in the extracted directory"
    exit 4
fi

# Restore each volume
for archive in $volume_archives; do
    # Get volume name from archive filename
    volume_name=$(basename "$archive" .tar)
    full_volume_name="${PROJECT_NAME}_${volume_name}"

    log "Restoring volume: $full_volume_name"

    # Check if volume exists
    if docker volume inspect "$full_volume_name" &>/dev/null; then
        log "Volume $full_volume_name already exists, renaming old volume as backup"
        backup_volume="${full_volume_name}_backup_$(date +%s)"
        docker volume create "$backup_volume"

        # Copy data from old volume to backup
        docker run --rm \
            -v "$full_volume_name:/source" \
            -v "$backup_volume:/backup" \
            alpine sh -c "cp -a /source/. /backup/"

        log "Created backup volume: $backup_volume"
    else
        log "Creating new volume: $full_volume_name"
        docker volume create "$full_volume_name"
    fi

    # Restore from archive
    if docker run --rm \
        -v "$full_volume_name:/volume" \
        -v "$archive:/backup.tar" \
        alpine sh -c "tar -xf /backup.tar -C /volume"; then
        log "✅ Successfully restored $full_volume_name"
    else
        log -e "Failed to restore volume $full_volume_name"
        exit 6
    fi
done

# Restart containers if they were running before
if [ "$should_restart" = true ]; then
    log "Restarting previously running containers..."
    docker_compose_cmd start

    # Verify restart was successful
    # TODO: never executed if the start failed ?
    # TODO: suspect rabbitmq may fail to restart if a browser is still connected
    restarted_containers=$(docker_compose_cmd ps --services)
    if [ -z "$restarted_containers" ]; then
        log -e "Warning: Failed to restart containers"
    else
        log -s "Containers restarted successfully: $restarted_containers"
    fi
fi

log "✅ All volumes have been restored successfully!"
