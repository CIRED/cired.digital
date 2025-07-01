#!/usr/bin/env bash
#
# Validate a running r2r instance
# 1. Check container logs for errors and warnings
# 2. Check health endpoint
# 3. Check API keys
# 4. Run the smoke tests using uvx
# 4.1 Ingest and query a simple test file
# 4.2 Idem, calling different LLMs for generation
# 4.3 TODO: Ingest and query scientific papers as PDFs

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
    local max_tries=12       # Number of attempts
    local delay=5            # Delay between attempts (seconds)
    local try=0
    local response

    log "🔍 Checking R2R health at $HEALTH_ENDPOINT (up to $((max_tries*delay))s)..."

    until [[ $try -ge $max_tries ]]; do
        ((try++))
        response=$(curl -s --connect-timeout 5 --max-time 10 "$HEALTH_ENDPOINT" 2>/dev/null || echo "")
        if [[ "$response" == '{"results":{"message":"ok"}}' ]]; then
            log "✅ R2R is healthy (after $try attempt(s))."
            return 0
        fi
        log "⚠️ Attempt $try/$max_tries failed, response='$response'. Retrying in $delay s..."
        sleep $delay
    done

    log "❌ R2R did not respond as expected after $try attempts."
    return 1
}

# Check for API keys in the R2R container
check_api_keys() {
    local container_name="${COMPOSE_PROJECT_NAME}-r2r-1"
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

check_container_logs() {
    local container_name="$1"
    local full_container_name="${COMPOSE_PROJECT_NAME}-${container_name}-1"

    log "🔍 Checking logs for container '$full_container_name'..."

    # Check if container exists and is running
    if ! docker ps --format '{{.Names}}' | grep -q "^${full_container_name}$"; then
        log "❌ Container '$full_container_name' is not running."
        return 3
    fi

    local logs
    logs=$(docker logs "$full_container_name" 2>&1)

    # Check for ERROR messages
    if echo "$logs" | grep -i "ERROR" >/dev/null 2>&1; then
        log "❌ Found ERROR messages in $full_container_name logs:"
        echo "$logs" | grep -i "ERROR" | sed 's/^/   /'
        return 1
    fi

    # Check for WARNING messages
    if echo "$logs" | grep -i "WARNING" >/dev/null 2>&1; then
        log "⚠️ Found WARNING messages in $full_container_name logs:"
        echo "$logs" | grep -i "WARNING" | sed 's/^/   /'
        return 2
    fi

    log "✅ No ERROR or WARNING messages found in $full_container_name logs."
    return 0
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

log "🔍 Checking container logs for errors and warnings..."
if ! check_container_logs "r2r"; then
    exit_code=$?
    if [ $exit_code -eq 1 ]; then
        log "❌ Container logs contain ERROR messages. Exiting."
        exit 1
    elif [ $exit_code -eq 2 ]; then
        log "⚠️ Container logs contain WARNING messages. Continuing with validation."
    elif [ $exit_code -eq 3 ]; then
        log "❌ Container is not running. Exiting."
        exit 1
    fi
fi

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
