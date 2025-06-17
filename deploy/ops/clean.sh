#!/usr/bin/env bash
#
# Revert the directory to git-only files

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/common_config.sh"

trap 'log "❌ An unexpected error occurred."' ERR

# Change to the base directory to ensure all relative paths work
cd "$BASE_DIR"


log "🧹 Cleaning up files to revert to a fresh-from-repo state..."
log "📍 Working in directory: $BASE_DIR"

log "🧹 Removing R2R upstream configuration files..."
if [[ -d "$CONFIG_UPSTREAM_DIR" ]]; then
    rm -rf "$CONFIG_UPSTREAM_DIR"
    log "✅ Removed $CONFIG_UPSTREAM_DIR directory"
else
    log "ℹ️  $CONFIG_UPSTREAM_DIR directory not found (already clean)"
fi

log "🧹 Removing the expanded user_configs files"


log "🧹 Removing test file..."
if [[ -f "$TEST_FILE" ]]; then
    rm -f "$TEST_FILE"
    log "✅ Removed $TEST_FILE"
else
    log "ℹ️  $TEST_FILE not found (already clean)"
fi

log "🧹 Suppression des __pycache__ et des .ropeproject dans $BASE_DIR"
find "$BASE_DIR" -type d \( -name "__pycache__" -o -name ".ropeproject" \) -exec rm -rf {} +

log "🧹 Suppression des __pycache__ et des .ropeproject dans $BASE_DIR/../src/"
find "$BASE_DIR/../src/" -type d \( -name "__pycache__" -o -name ".ropeproject" \) -exec rm -rf {} +

log "🧹 Suppression des __pycache__ et des .ropeproject dans $BASE_DIR/../tests/"
find "$BASE_DIR/../tests/" -type d \( -name "__pycache__" -o -name ".ropeproject" \) -exec rm -rf {} +


# Prune dangling images, stopped containers, unused networks
log "🧹 Cleaning up Docker resources..."

# Check if Docker is available before attempting cleanup
if command -v docker &> /dev/null && docker info &> /dev/null; then
    log "🧹 Cleaning up dangling Docker images..."
    docker image prune -f

    log "🧹 Cleaning up stopped containers..."
    docker container prune -f

    log "🧹 Cleaning up unused networks..."
    docker network prune -f

    log "✅ Docker cleanup completed"
else
    log "⚠️  Docker not available or not running - skipping Docker cleanup"
fi

rotate_backup_volumes() {
    log "🧹 Checking for backup volumes to rotate..."
    log "📋 Backup retention count set to: $BACKUP_RETENTION_COUNT"

    local backup_volumes
    if ! backup_volumes=$(docker volume ls -f dangling=true -f name=_backup_ --format "{{.Name}}" 2>/dev/null); then
        log "⚠️  Could not list Docker volumes - skipping backup rotation"
        return 0
    fi

    if [[ -z "$backup_volumes" ]]; then
        log "ℹ️  No backup volumes found"
        return 0
    fi

    declare -A volume_groups
    while IFS= read -r volume; do
        if [[ "$volume" =~ ^(.+)_backup_([0-9]+)$ ]]; then
            local stem="${BASH_REMATCH[1]}"
            volume_groups["$stem"]+="$volume "
        fi
    done <<< "$backup_volumes"

    for stem in "${!volume_groups[@]}"; do
        local volumes=(${volume_groups[$stem]})
        local volume_count=${#volumes[@]}

        if [[ $volume_count -le $BACKUP_RETENTION_COUNT ]]; then
            log "ℹ️  Volume group '$stem': keeping all $volume_count backup(s)"
            continue
        fi

        IFS=$'\n' volumes=($(printf '%s\n' "${volumes[@]}" | sort -t_ -k3 -nr))

        local volumes_to_delete=("${volumes[@]:$BACKUP_RETENTION_COUNT}")

        log "📋 Volume group '$stem': found $volume_count backup(s), will keep $BACKUP_RETENTION_COUNT most recent"
        log "📋 Volumes to keep: ${volumes[@]:0:$BACKUP_RETENTION_COUNT}"
        log "📋 Volumes to delete: ${volumes_to_delete[@]}"

        echo -n "Delete ${#volumes_to_delete[@]} old backup volume(s) for '$stem'? [y/N]: "
        read -r confirmation

        if [[ "$confirmation" =~ ^[Yy]$ ]]; then
            for volume in "${volumes_to_delete[@]}"; do
                if docker volume rm "$volume" 2>/dev/null; then
                    log "✅ Deleted backup volume: $volume"
                else
                    log "❌ Failed to delete backup volume: $volume"
                fi
            done
        else
            log "ℹ️  Skipped deletion for volume group '$stem'"
        fi
    done
}

rotate_backup_volumes

log "🎉 Cleanup completed successfully!"
