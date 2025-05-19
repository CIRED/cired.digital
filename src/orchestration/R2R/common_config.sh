#!/usr/bin/env bash
# Common configuration for R2R orchestration scripts

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Logging function used by all scripts. Logs to stderr.
log() { echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] $*" >&2; }

# Project settings
PROJECT_NAME="myrag"
SUBDIR="docker"
COMPOSE_FILE="${SCRIPT_DIR}/docker/compose.full.yaml"
OVERRIDE_FILE="${SCRIPT_DIR}/compose.override.yaml"
KEYS_FILE="${SCRIPT_DIR}/../../../../credentials/API_KEYS"
VENV_DIR="${SCRIPT_DIR}/venv"

# Volume settings (exported, it needs to be available to docker compose)
export VOLUMES_BASE="$(realpath "$SCRIPT_DIR/../../../data")"
export VOLUMES_DIR="${VOLUMES_BASE}/active/R2R"
ARCHIVES_DIR="${VOLUMES_BASE}/archived/R2R"
ACTIVE_DIR="${VOLUMES_DIR}"
SNAPSHOT_PREFIX="snapshot_$(date +%F)"

# Ensure directories exist
mkdir -p "${VOLUMES_DIR}" "${ARCHIVES_DIR}"

# Utility functions
validate_dir() {
    local dir="$1"
    if [ ! -d "$dir" ]; then
        log "ERROR: Directory $dir does not exist"
        return 1
    fi
    return 0
}

validate_file() {
    local file="$1"
    if [ ! -f "$file" ]; then
        log "ERROR: File $file does not exist"
        return 1
    fi
    return 0
}

# Docker settings
DOCKER_IMAGE="docker.io/sciphiai/r2r:latest"
DASHBOARD_IMAGE="docker.io/sciphiai/r2r-dashboard:1.0.3"

# Network settings
SERVER_URL="http://localhost:7272"
HEALTH_ENDPOINT="$SERVER_URL/v3/health"

# Timeout settings
HEALTH_CHECK_TIMEOUT=10
DOCKER_STOP_TIMEOUT=15

# Test settings
SMOKE_DIR="${SCRIPT_DIR}/smoke-tests"
TEST_FILE="test.txt"
TEST_CONTENT="QuetzalX is a person that works at CIRED."
TEST_QUERY="Who is QuetzalX?"
