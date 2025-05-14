#!/usr/bin/env bash
# Common configuration for R2R orchestration scripts

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Logging function used by all scripts
log() { echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] $*"; }

# Project settings
PROJECT_NAME="myrag"
SUBDIR="docker"
COMPOSE_FILE="${SCRIPT_DIR}/docker/compose.full.yaml"
OVERRIDE_FILE="${SCRIPT_DIR}/compose.override.yaml"
KEYS_FILE="${SCRIPT_DIR}/../../../../credentials/API_KEYS"
VENV_DIR="${SCRIPT_DIR}/venv"

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
