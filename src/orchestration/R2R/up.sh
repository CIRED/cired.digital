#!/usr/bin/env bash
#
# Starts R2R
#
# Instead of adding the keys in clear into docker/env/r2r-full.env,
# we use a local compose override file to pass the secrets
# from the file credentials/API_KEYS which contains
#  DEEPSEEK_API_KEY=sk_...
#  OPENAI_API_KEY=sk_...
#  MISTRAL_API_KEY=...

set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR"
source "$SCRIPT_DIR/common_config.sh"
trap 'log "❌ An unexpected error occurred."' ERR

# Validate we have docker
if ! command -v docker &> /dev/null; then
  log "❌ Error: Docker is not installed or not in PATH."
  log "    To install Docker from Docker's official repository:"
  log "    # Add Docker's official GPG key"
  log "    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg"
  log "    # Add Docker repository"
  log "    echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu focal stable' | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null"
  log "    # Install Docker Engine"
  log "    sudo apt update && sudo apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin"
  log "    # Or use the convenience script: curl -fsSL https://get.docker.com | sh"
  log "    For other systems: https://docs.docker.com/get-docker/"
  exit 1
fi

if ! docker info > /dev/null 2>&1; then
  log "Error: Docker is installed but not working correctly."
  log "    Possible causes:"
  log "    - Docker daemon is not running (try: sudo systemctl start docker)"
  log "    - Permission issue (try: sudo usermod -aG docker $USER, then log out/in)"
  log "    - Docker socket permissions"
  exit 1
fi

# Verify configuration files exist
if [[ ! -f "$COMPOSE_FILE" ]]; then
  log "Error: Compose file '$COMPOSE_FILE' not found."
  exit 1
fi

if [[ ! -f "$OVERRIDE_FILE" ]]; then
  log "Error: Override file '$OVERRIDE_FILE' not found."
  exit 1
fi

if [[ ! -f "$KEYS_FILE" ]]; then
  log "Error: Environment file '$KEYS_FILE' not found."
  exit 1
fi

# Environment variable checking function. Returns the number of API keys found (0 to 3).
check_env_vars() {
  local prefix="$1"
  log "🔍 $prefix Environment Variables:"

  local vars_set=0
  local total_vars=3

  if [[ -n "${OPENAI_API_KEY:-}" ]]; then
    log "  ✅ OPENAI_API_KEY: SET (${#OPENAI_API_KEY} characters)"
    ((vars_set++))
  else
    log "  ❌ OPENAI_API_KEY: NOT SET"
  fi

  if [[ -n "${MISTRAL_API_KEY:-}" ]]; then
    log "  ✅ MISTRAL_API_KEY: SET (${#MISTRAL_API_KEY} characters)"
    ((vars_set++))
  else
    log "  ❌ MISTRAL_API_KEY: NOT SET"
  fi

  if [[ -n "${DEEPSEEK_API_KEY:-}" ]]; then
    log "  ✅ DEEPSEEK_API_KEY: SET (${#DEEPSEEK_API_KEY} characters)"
    ((vars_set++))
  else
    log "  ❌ DEEPSEEK_API_KEY: NOT SET"
  fi

  log "  📊 Summary: $vars_set/$total_vars environment variables are set"
  echo "$vars_set"  # Return the count via echo
  return 0         # Always return success
}


log "📦 Project: $PROJECT_NAME"
log "🔧 Compose file: $COMPOSE_FILE"
log "🔧🔧 Override file: $OVERRIDE_FILE"
log "🔑 Env file: $KEYS_FILE"

# Check environment variables before sourcing
vars_before=$(check_env_vars "BEFORE sourcing")

# Bring up the service
if docker_compose_cmd ps 2>/dev/null | grep -q 'Up'; then
  log "⚠️ Services are already running."
  docker_compose_cmd ps
  exit 0
else
  # Warn if variables are already set
  if [[ $vars_before -gt 0 ]]; then
    log "⚠️ WARNING: Some environment variables are already set and will be overridden!"
  fi
  # Source the environment file and export all variables
  set -a  # automatically export all variables
  source "$KEYS_FILE"
  set +a  # turn off automatic export

  vars_after=$(check_env_vars "AFTER sourcing")
  if [[ $vars_after -lt 3 ]]; then
    log "⚠️ WARNING: Not all environment variables are set. Docker Compose may show warnings."
  fi

  log "🚀 Starting services..."
  docker_compose_cmd --profile postgres up -d
  log "✅ Docker Compose started successfully."
fi
