#!/usr/bin/env bash
#
# Validate a running r2r instance
# 1. Check health endpoint
# 2. Check API keys
# 3. Run the smoke tests
# 3.1 Ingest and query a simple test file
# 3.2 Idem, calling different LLMs for generation
# 3.3 TODO: Ingest and query scientific papers as PDFs

set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR"
source "$SCRIPT_DIR/common_config.sh"
trap 'log "❌ An unexpected error occurred."' ERR


# Check R2R health, with retry logic
check_r2r_health() {
    log "🔍 Checking R2R health at $HEALTH_ENDPOINT..."

  local response
  response=$(curl -s --connect-timeout 5 "$HEALTH_ENDPOINT")

  if [[ "$response" == '{"results":{"message":"ok"}}' ]]; then
    log "✅ R2R is healthy."
    return 0
  fi

  log "⚠️ R2R did not respond as expected. Retrying in 10 seconds..."
  sleep 10

  response=$(curl -s --connect-timeout 5 "$HEALTH_ENDPOINT")
  if [[ "$response" == '{"results":{"message":"ok"}}' ]]; then
    log "✅ R2R is healthy (after retry)."
    return 0
  else
    log "❌ R2R is not responding as expected after retry."
    log "   Received: $response"
    return 1
  fi
}

# Check for API keys in the R2R container
check_api_keys() {
  local container_name="${PROJECT_NAME}-r2r-1"
  log "🔍 Checking for API keys in container '$container_name'..."

  if docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
    if docker exec "$container_name" env | grep -q "API_KEY"; then
      log "✅ API keys found in container."
    else
      log "❌ No API keys found in container."
    fi
  else
    log "⚠️ Container '$container_name' is not running."
  fi
}

# Run both checks
check_r2r_health
check_api_keys

# Run smoke tests

# Verify the virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    log "❌ Python virtual environment not found. Please run install.sh first."
    exit 1
fi

source "$VENV_DIR/bin/activate"

log "🚀 Running smoke tests..."
python3 "$SMOKE_DIR/hello_r2r.py"
python3 "$SMOKE_DIR/LLM_swap.py"

deactivate

log "R2R smoke tests passed."
