#!/usr/bin/env bash
#
# Validate a running r2r instance
# 1. Check health endpoint
# 2. Check API keys
# 3. Run the smoke tests
# 3.1 Ingest and query a simple test file
# 3.2 Idem, calling different LLMs for generation
# 3.3 TODO: Ingest and query scientific papers as PDFs

# Log helper
log() {
  echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

# Query the R2R health endpoint and return success if it responds with the expected JSON
query_health_endpoint() {
  local url="http://localhost:7272/v3/health"
  local expected='{"results":{"message":"ok"}}'

  curl -s "$url"
}

# Check R2R health, with retry logic
check_r2r_health() {
  log "🔍 Checking R2R health at http://localhost:7272/v3/health..."

  local response
  response=$(query_health_endpoint)

  if [[ "$response" == '{"results":{"message":"ok"}}' ]]; then
    log "✅ R2R is healthy."
    return 0
  fi

  log "⚠️ R2R did not respond as expected. Retrying in 10 seconds..."
  sleep 10

  response=$(query_health_endpoint)
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
  local container_name="myrag-r2r-1"
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

SCRIPT_DIR="$(dirname "$0")"
SMOKE_DIR="$SCRIPT_DIR/smoke-tests"
VENV_DIR="$SCRIPT_DIR/venv"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    uv venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    uv pip install -r "$SMOKE_DIR/requirements.txt"
else
    source "$VENV_DIR/bin/activate"
fi

# Run tests
python "$SMOKE_DIR/hello_r2r.py"
python "$SMOKE_DIR/LLM_swap.py"

# Optionally deactivate and clean up
deactivate
# rm -rf "$VENV_DIR"  # Uncomment to delete venv after every run

echo "R2R smoke tests passed."
