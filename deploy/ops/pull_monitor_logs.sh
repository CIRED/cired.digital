#!/usr/bin/env bash
# filepath: pull_monitor_logs.sh
# Pull monitor logs from remote server to local machine
# Usage: ./pull_monitor_logs.sh [remote_user] [remote_host] [--execute] [--diagnose]

set -Eeuo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# Expects common_config.sh to define: BASE_DIR, REMOTE_PROJECT_PATH, REMOTE_USER, REMOTE_HOST, and log()
source "$SCRIPT_DIR/common_config.sh"

# --- Args ---------------------------------------------------------------------
EXECUTE_MODE=false
DIAGNOSE_MODE=false
ARGS=()
for arg in "$@"; do
  if [[ "$arg" == "--execute" ]]; then
    EXECUTE_MODE=true
  elif [[ "$arg" == "--diagnose" ]]; then
    DIAGNOSE_MODE=true
  else
    ARGS+=("$arg")
  fi
done

REMOTE_USER="${ARGS[0]:-${REMOTE_USER}}"
REMOTE_HOST="${ARGS[1]:-${REMOTE_HOST}}"

REMOTE_PATH="${REMOTE_PROJECT_PATH}/reports/monitor-logs/"
LOCAL_PROJECT_PATH="$(dirname "$BASE_DIR")"
LOCAL_PATH="${LOCAL_PROJECT_PATH}/reports/monitor-logs/"

usage() {
  cat <<EOF
Usage: $0 [remote_user] [remote_host] [--execute] [--diagnose]

Pull monitor logs from remote server to local machine using rsync.

DEFAULT: DRY-RUN (preview only). Use --execute to actually sync.

Parameters:
  remote_user  Remote SSH username (default: ${REMOTE_USER})
  remote_host  Remote SSH host     (default: ${REMOTE_HOST})
  --execute    Perform the sync (not just preview)
  --diagnose   Show verbose rsync output to identify problematic files

Examples:
  $0
  $0 ${REMOTE_USER} ${REMOTE_HOST}
  $0 --execute
  $0 --diagnose
  $0 --execute --diagnose
  $0 ${REMOTE_USER} ${REMOTE_HOST} --execute

Remote path: ${REMOTE_PROJECT_PATH}/reports/monitor-logs/
Local path:  ${LOCAL_PATH}
EOF
  exit 0
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
fi

# --- Pre-flight ----------------------------------------------------------------
for bin in ssh rsync; do
  if ! command -v "$bin" >/dev/null 2>&1; then
    echo "ERROR: '$bin' is required but not found in PATH." >&2
    exit 127
  fi
done

if [[ "$DIAGNOSE_MODE" == "true" ]]; then
  log "🔬 DIAGNOSE MODE: Verbose rsync output enabled (DRY-RUN only)"
  EXECUTE_MODE=false
fi

if [[ "$EXECUTE_MODE" == "false" ]]; then
  log "🔍 DRY-RUN: Previewing monitor logs sync (no files will be transferred)"
else
  log "🔄 Executing monitor logs sync..."
fi

log "Remote: ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}"
log "Local:  ${LOCAL_PATH}"

mkdir -p "$LOCAL_PATH"

log "Testing connection to remote host..."
if ! ssh -o ConnectTimeout=5 -o BatchMode=yes "${REMOTE_USER}@${REMOTE_HOST}" exit 2>/dev/null; then
  echo "ERROR: Cannot connect to ${REMOTE_HOST}" >&2
  echo "Check:" >&2
  echo "  - Server reachability" >&2
  echo "  - SSH key / agent loaded (try: ssh-add -l)" >&2
  echo "  - Username / hostname" >&2
  exit 1
fi

if ! ssh "${REMOTE_USER}@${REMOTE_HOST}" "[ -d \"$REMOTE_PATH\" ]"; then
  echo "ERROR: Remote directory does not exist: ${REMOTE_PATH}" >&2
  echo "Make sure the monitoring service has created log files." >&2
  exit 2
fi

# Only sync JSON and LOG files; ensure directories are traversed.
RSYNC_FILTER=(
  --include='*/'
  --include='*.json'
  --include='*.log'
  --exclude='*'
)

RSYNC_COMMON_OPTS=(
  -avz
  --human-readable
  --no-perms --no-owner --no-group
  --omit-dir-times --omit-link-times
)

# Add verbose/diagnostic options
if [[ "$DIAGNOSE_MODE" == "true" ]]; then
  RSYNC_COMMON_OPTS+=(
    --verbose
    --verbose
    --itemize-changes
  )
fi

# --- Dry-run (always) ----------------------------------------------------------
log "📋 Files to sync:"
RSYNC_EXIT_CODE=0
rsync "${RSYNC_COMMON_OPTS[@]}" --dry-run \
  --itemize-changes \
  "${RSYNC_FILTER[@]}" \
  "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}" "${LOCAL_PATH}" || RSYNC_EXIT_CODE=$?

if [[ $RSYNC_EXIT_CODE -ne 0 ]]; then
  if [[ $RSYNC_EXIT_CODE -eq 23 ]]; then
    log "⚠️  Some files/attrs were not transferred (rsync code 23)."
    log "    Likely unreadable or vanished files on the remote. Generally safe to ignore."
    if [[ "$DIAGNOSE_MODE" == "false" ]]; then
      log "    Run with --diagnose to see detailed information about problematic files."
    fi
  else
    echo "ERROR: Rsync (dry-run) failed with exit code: $RSYNC_EXIT_CODE" >&2
    exit "$RSYNC_EXIT_CODE"
  fi
fi

if [[ "$EXECUTE_MODE" == "false" ]]; then
  log ""
  log "🎯 Next:"
  log "  Review the list above, then run one of:"
  log "    $0 --execute"
  log "    $0 ${REMOTE_USER} ${REMOTE_HOST} --execute"
  if [[ "$DIAGNOSE_MODE" == "true" ]]; then
    log ""
    log "  Note: --diagnose mode is always DRY-RUN. Remove --diagnose to enable --execute."
  fi
  exit 0
fi

# --- Execute sync --------------------------------------------------------------
log "🚀 Syncing files..."
RSYNC_EXIT_CODE=0
rsync "${RSYNC_COMMON_OPTS[@]}" --progress --partial --stats \
  "${RSYNC_FILTER[@]}" \
  "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}" "${LOCAL_PATH}" || RSYNC_EXIT_CODE=$?

if [[ $RSYNC_EXIT_CODE -ne 0 ]]; then
  if [[ $RSYNC_EXIT_CODE -eq 23 ]]; then
    log "⚠️  Sync completed with some files skipped (exit 23)."
    log "    Regular files (.json, .log) likely transferred fine."
    if [[ "$DIAGNOSE_MODE" == "false" ]]; then
      log "    Run with --diagnose to see which files caused issues."
    fi
  else
    echo "ERROR: Sync failed with exit code: $RSYNC_EXIT_CODE" >&2
    exit 3
  fi
else
  log "✅ Sync completed successfully!"
  log "Files are in: ${LOCAL_PATH}"
  # Safe find with precedence parentheses
  FILE_COUNT=$(find "$LOCAL_PATH" \( -name "*.json" -o -name "*.log" \) | wc -l | tr -d ' ')
  log "Total files in local directory: ${FILE_COUNT}"
  log "Completed at $(date '+%Y-%m-%d %H:%M:%S')"
fi
