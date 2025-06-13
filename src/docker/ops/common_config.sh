#!/usr/bin/env bash
# Common configuration for R2R orchestration scripts
# Version: 1.1.0
# Provides shared variables, functions and utilities for all R2R management scripts

# Strict mode and error handling
set -o errexit
set -o nounset
set -o pipefail

# Get the absolute path of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# --- Project Configuration ---
export COMPOSE_PROJECT_NAME="cidir2r"  # Used as prefix for Docker resources
export PROJECT_DESCRIPTION="CIRED R2R Deployment"
CONFIG_UPSTREAM_DIR="${BASE_DIR}/config.upstream"
COMPOSE_FILE="${BASE_DIR}/compose.yaml"
SECRETS_FILE="${BASE_DIR}/../../credentials/r2r-cidi.env"
VENV_DIR="${BASE_DIR}/venv"

# Volume settings
# data/ is at the same level as src/ but in .gitignore
DATA_BASE="$(realpath "$BASE_DIR/../../data")"
ARCHIVES_DIR="${DATA_BASE}/archived/R2R"
SNAPSHOT_PREFIX="snapshot_$(date +%F_%H%M%S)"

BACKUP_RETENTION_COUNT=0  # Number of backup volumes to keep per volume type

# Docker Compose Command Builder
# Wrapper for consistent docker compose command usage across all scripts
docker_compose_cmd() {
    if ! validate_file "$COMPOSE_FILE"; then
        return 1
    fi

    local cmd=(docker compose -p "$COMPOSE_PROJECT_NAME")

    # Add any passed arguments
    cmd+=("$@")

    # Log the command in debug mode
    log -d "Executing: ${cmd[*]}"

    "${cmd[@]}"
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

# Vérifie que Docker est installé et que le démon tourne
ensure_docker() {
    local smoke_test=false
    if [[ "${1:-}" == "--smoke-test" ]]; then
        smoke_test=true
    fi

    if ! command -v docker &> /dev/null; then
        log -e "❌ Docker introuvable. Veuillez installer Docker avant de continuer."
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log -e "❌ Docker installé mais inopérant (daemon arrêté ou problème de permissions)."
        exit 1
    fi

    if $smoke_test; then
        log "🚀 Test smoke: exécution de hello-world"
        if ! docker run --rm hello-world &> /dev/null; then
            log -e "❌ Test smoke 'hello-world' a échoué."
            exit 1
        fi
        log "✅ Test smoke 'hello-world' réussi."
    fi
}

validate_file() {
    local file="$1"
    if [ ! -f "$file" ]; then
        log "ERROR: File $file does not exist"
        return 1
    fi
    return 0
}

validate_config_files() {
    validate_file "$COMPOSE_FILE" || exit 1
    validate_file "$SECRETS_FILE" || exit 1
    log "📦 Project: $COMPOSE_PROJECT_NAME"
    log "🔧 Compose file: $COMPOSE_FILE"
    log "🔑 Secrets env file: $SECRETS_FILE"
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
SMOKE_DIR="${BASE_DIR}/smoke-tests"
TEST_FILE="test.txt"
TEST_CONTENT="QuetzalX is a person that works at CIRED."
TEST_QUERY="Who is QuetzalX?"

# --- Logging Utilities ---
# Usage:
#   log "info message"
#   log -e "error message"
#   log -w "warning message"
#   log -d "debug message"
#   log -s "success message" (green)
log() {
    local level="INFO"
    local color="\033[0m"  # Default

    case "$1" in
        -e) level="ERROR"; color="\033[0;31m"; shift ;;  # Red
        -w) level="WARN"; color="\033[0;33m"; shift ;;   # Yellow
        -d) level="DEBUG"; color="\033[0;36m"; shift ;;  # Cyan
        -s) level="SUCCESS"; color="\033[0;32m"; shift ;; # Green
    esac

    echo -e "${color}[$(date +'%Y-%m-%d %H:%M:%S')] [$level] $*\033[0m" >&2
}

# Validate required environment variables
validate_env() {
    local missing=()
    for var in "$@"; do
        if [[ -z "${!var:-}" ]]; then
            missing+=("$var")
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        log -e "Missing required environment variables: ${missing[*]}"
        return 1
    fi
    return 0
}
