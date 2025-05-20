#!/usr/bin/env bash
# Common configuration for R2R orchestration scripts

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"


# Project settings
PROJECT_NAME="cidir2r"
SUBDIR="docker"
COMPOSE_FILE="${SCRIPT_DIR}/docker/compose.full.yaml"
OVERRIDE_FILE="${SCRIPT_DIR}/compose.override.yaml"
KEYS_FILE="${SCRIPT_DIR}/../../../../credentials/API_KEYS"
VENV_DIR="${SCRIPT_DIR}/venv"

# Volume settings (exported, it needs to be available to docker compose)
export VOLUMES_BASE="$(realpath "$SCRIPT_DIR/../../../data")"
ARCHIVES_DIR="${VOLUMES_BASE}/archived/R2R"
SNAPSHOT_PREFIX="snapshot_$(date +%F_%H%M%S)"

# Docker compose command (used by all scripts)
docker_compose_cmd() {
  docker compose \
    --project-name "$PROJECT_NAME" \
    -f "$COMPOSE_FILE" \
    -f "$OVERRIDE_FILE" \
    "$@"
}

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

# Enhanced logging function with levels (used by all scripts)
log() {
    local level="INFO"
    if [[ "$1" == "-e" ]]; then level="ERROR"; shift
    elif [[ "$1" == "-w" ]]; then level="WARN"; shift
    elif [[ "$1" == "-d" ]]; then level="DEBUG"; shift; fi
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] [$level] $*" >&2
}
