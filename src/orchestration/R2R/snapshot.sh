#!/usr/bin/env bash
#
# Creates a snapshot of R2R data with validation checks
#
# Exit codes:
#   0 - Success
#   1 - Initial state invalid
#   2 - Final state invalid

set -Eeuo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR"
source "$SCRIPT_DIR/common_config.sh"

# Initialize variables
SNAPSHOT_FILE="${ARCHIVES_DIR}/${SNAPSHOT_PREFIX}.tar.gz"
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

# Logging function with timestamp and level
log() {
    local level="INFO"
    if [[ "$1" == "-e" ]]; then level="ERROR"; shift
    elif [[ "$1" == "-w" ]]; then level="WARN"; shift
    elif [[ "$1" == "-d" ]]; then level="DEBUG"; shift; fi
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] [$level] $*" >&2
}

# Validate R2R state
validate_r2r() {
    log "🔍 Validating R2R state..."
    if ! "$SCRIPT_DIR/validate.sh" --quick; then
        log -e "R2R validation failed"
        return 1
    fi
    return 0
}

# Create snapshot archive
create_snapshot() {
    log "📦 Creating snapshot at $SNAPSHOT_FILE"
    mkdir -p "$ARCHIVES_DIR"
    
    if ! tar -czf "$SNAPSHOT_FILE" -C "$VOLUMES_DIR" .; then
        log -e "Failed to create snapshot archive"
        return 1
    fi
    
    # Verify archive integrity
    if ! tar -tzf "$SNAPSHOT_FILE" >/dev/null 2>&1; then
        log -e "Snapshot archive verification failed"
        return 1
    fi
    
    log "✅ Snapshot created successfully ($(du -h "$SNAPSHOT_FILE" | cut -f1))"
    return 0
}

# Main execution
main() {
    log "🚀 Starting R2R snapshot process"
    
    # Step 1: Validate initial state
    if ! validate_r2r; then
        log -e "Aborting snapshot - R2R is not in a valid state"
        exit 1
    fi
    
    # Step 2: Stop R2R
    log "🛑 Stopping R2R services..."
    if ! "$SCRIPT_DIR/down.sh"; then
        log -e "Failed to stop R2R services"
        exit 1
    fi
    
    # Step 3: Create snapshot
    if ! create_snapshot; then
        log -e "Snapshot creation failed"
        exit 1
    fi
    
    # Step 4: Restart R2R
    log "🔁 Restarting R2R services..."
    if ! "$SCRIPT_DIR/up.sh"; then
        log -e "Failed to restart R2R services"
        exit 1
    fi
    
    # Step 5: Validate final state
    if ! validate_r2r; then
        log -e "R2R is not in a valid state after restart"
        exit 2
    fi
    
    log "🎉 Snapshot process completed successfully"
    exit 0
}

main "$@"
