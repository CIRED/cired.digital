#!/usr/bin/env bash
# docker_restore.sh - Restore Docker volumes for cired.digital project

set -Eeuo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR"

source "$SCRIPT_DIR/common_config.sh"

# Verify archive argument
if [ $# -lt 1 ]; then
    log -e "Usage: $0 <archive_file>"
    log "Available archives in ${ARCHIVES_DIR}:"
    if [ -d "${ARCHIVES_DIR}" ]; then
        find "${ARCHIVES_DIR}" -name "*.tar.gz" -printf "%f\n" | sort | while read -r archive; do
            log "  - ${archive}"
        done
    else
        log "  (no archive directory found)"
    fi
    exit 1
fi

ARCHIVE_FILE="$1"
TEMP_DIR="$(mktemp -d)"

# Clean up temp directory on exit
trap 'rm -rf "$TEMP_DIR"' EXIT

# Verify archive exists
if [ ! -f "$ARCHIVE_FILE" ]; then
    log -e "Archive file not found: $ARCHIVE_FILE"
    exit 2
fi

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

# Extract the archive to temp directory
log "Extracting archive: $ARCHIVE_FILE"
if ! tar -xzf "$ARCHIVE_FILE" -C "$TEMP_DIR"; then
    log -e "Failed to extract archive"
    exit 3
fi

# Find all .tar.gz files in the extracted directory
archive_dir=$(find "$TEMP_DIR" -type d | head -1)
volume_archives=$(find "$archive_dir" -name "*.tar.gz")

if [ -z "$volume_archives" ]; then
    log -e "No volume archives found in the extracted directory"
    exit 4
fi

# Restore each volume
for archive in $volume_archives; do
    # Get volume name from archive filename
    volume_name=$(basename "$archive" .tar.gz)
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
        -v "$archive:/backup.tar.gz" \
        alpine sh -c "tar -xzf /backup.tar.gz -C /volume"; then
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
    restarted_containers=$(docker_compose_cmd ps --services)
    if [ -z "$restarted_containers" ]; then
        log -e "Warning: Failed to restart containers"
    else
        log -s "Containers restarted successfully: $restarted_containers"
    fi
fi

log "✅ All volumes have been restored successfully!"
