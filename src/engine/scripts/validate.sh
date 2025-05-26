#!/usr/bin/env bash
#
# Validate a running r2r instance
# 1. Check health endpoint
# 2. Check API keys
# 3. Run the smoke tests using uvx
# 3.1 Ingest and query a simple test file
# 3.2 Idem, calling different LLMs for generation
# 3.3 TODO: Ingest and query scientific papers as PDFs

set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR"
source "$SCRIPT_DIR/common_config.sh"

# Custom error handler
handle_error() {
    local exit_code=$?
    local line_number=$1
    log "❌ Error occurred on line $line_number (exit code: $exit_code)"
    log "   Last command failed. Check the output above for details."
    exit $exit_code
}

trap 'handle_error $LINENO' ERR

# Check R2R health, with retry logic
check_r2r_health() {
    log "🔍 Checking R2R health at $HEALTH_ENDPOINT..."

    # First, check if we can connect at all
    if ! curl -s --connect-timeout 5 --max-time 10 "$HEALTH_ENDPOINT" >/dev/null 2>&1; then
        log "❌ Cannot connect to R2R at $HEALTH_ENDPOINT"
        log "   Please ensure R2R is running with: docker compose up -d"
        log "   Or check if it's running on a different port."
        return 1
    fi

    local response
    response=$(curl -s --connect-timeout 5 --max-time 10 "$HEALTH_ENDPOINT" 2>/dev/null || echo "CURL_FAILED")

    if [[ "$response" == "CURL_FAILED" ]]; then
        log "❌ Failed to get response from R2R health endpoint"
        return 1
    fi

    log "   Response: $response"

    if [[ "$response" == '{"results":{"message":"ok"}}' ]]; then
        log "✅ R2R is healthy."
        return 0
    fi

    log "⚠️ R2R did not respond as expected. Retrying in 10 seconds..."
    sleep 10

    response=$(curl -s --connect-timeout 5 --max-time 10 "$HEALTH_ENDPOINT" 2>/dev/null || echo "CURL_FAILED")
    
    if [[ "$response" == "CURL_FAILED" ]]; then
        log "❌ Failed to get response from R2R health endpoint (retry)"
        return 1
    fi

    log "   Retry response: $response"

    if [[ "$response" == '{"results":{"message":"ok"}}' ]]; then
        log "✅ R2R is healthy (after retry)."
        return 0
    else
        log "❌ R2R is not responding as expected after retry."
        log "   Expected: {\"results\":{\"message\":\"ok\"}}"
        log "   Received: $response"
        return 1
    fi
}

# Check for API keys in the R2R container
check_api_keys() {
    local container_name="${PROJECT_NAME}-r2r-1"
    log "🔍 Checking for API keys in container '$container_name'..."

    if docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        if docker exec "$container_name" env | grep -q "API_KEY" 2>/dev/null; then
            log "✅ API keys found in container."
        else
            log "❌ No API keys found in container."
        fi
    else
        log "⚠️ Container '$container_name' is not running."
        log "   Available containers:"
        docker ps --format '{{.Names}}' | sed 's/^/     /'
    fi
}

# Check if uvx is available
check_uvx() {
    if ! command -v uvx >/dev/null 2>&1; then
        log "❌ uvx is not installed or not in PATH."
        log "   Please install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
        log "   Or use pipx: pipx install uv"
        exit 1
    fi
    log "✅ uvx is available."
}

# Pre-flight checks
log "🚀 Starting R2R validation..."

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    log "❌ Docker is not running or not accessible."
    exit 1
fi

# Check if uvx is available
check_uvx

# Run health and API key checks
if ! check_r2r_health; then
    log "❌ R2R health check failed. Cannot proceed with smoke tests."
    exit 1
fi

check_api_keys

# Run smoke tests using uvx
log "🧪 Running smoke tests with uvx..."

# Check if smoke test files exist
if [ ! -f "$SMOKE_DIR/hello_r2r.py" ]; then
    log "❌ Smoke test file not found: $SMOKE_DIR/hello_r2r.py"
    exit 1
fi

if [ ! -f "$SMOKE_DIR/LLM_swap.py" ]; then
    log "❌ Smoke test file not found: $SMOKE_DIR/LLM_swap.py"
    exit 1
fi

# Run the smoke tests with uvx (automatically handles r2r dependency)
log "🚀 Running hello_r2r.py with uvx..."
uvx --from r2r python3 "$SMOKE_DIR/hello_r2r.py"

log "🚀 Running LLM_swap.py with uvx..."
uvx --from r2r python3 "$SMOKE_DIR/LLM_swap.py"

log "✅ All R2R validation checks passed successfully!"
