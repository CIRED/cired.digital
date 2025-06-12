#!/usr/bin/env bash

################################################################################
# DOCKER COMPOSE FORCEFUL SHUTDOWN SCRIPT
################################################################################
#
# DESCRIPTION:
#   Performs a progressively aggressive shutdown of Docker Compose services
#   This script is designed for situations where standard `docker compose down`
#   fails or hangs, requiring more forceful intervention.
#
# USAGE:
#   ./down.sh                    # Try without root first
#   sudo ./down.sh               # If escalation to stages 4-5 is needed
#
# REQUIREMENTS:
#   - User must be in docker group OR have sudo access for escalation
#   - Requires common_config.sh in the same directory
#   - Docker and Docker Compose must be installed
#
# EXECUTION STAGES:
#   1. Graceful shutdown: `docker compose down` (15s timeout)
#   2. Force kill: `docker kill` on surviving containers (10s timeout)
#   3. Force remove: `docker rm -f` on stubborn containers (10s timeout)
#   4. Daemon restart: Restart Docker daemon via systemctl (30s timeout)
#   5. Process kill: Host-level `kill -9` on container processes
#
#   1-3: Can run as regular user (if in docker group)
#   4-5: Require root privileges (systemctl, kill -9)
#
# EXIT CODES:
#   0  - Success (containers stopped gracefully or forcefully)
#   1  - Permission error for escalation stages
#   2  - Docker access denied (user not in docker group)
#   99 - Ultimate escalation completed (manual intervention may be needed)
#   Other - Unexpected error occurred
#
# TIMEOUTS:
#   DOWN_TIMEOUT=15   - docker compose down timeout
#   GATHER_TIMEOUT=5  - container listing timeout
#   KILL_TIMEOUT=10   - docker kill timeout
#   FORCE_TIMEOUT=10  - docker rm -f timeout
#
# ZOMBIE CONTAINER AND NETWORK CLEANUP:
#   The script identifies and removes "zombie" containers and networks that are
#   in 'created' or 'exited' state but have broken network references. This
#   cleanup runs before exiting at stages 1, 2 or 3.
#
# WARNING:
#   This script uses progressively destructive methods including:
#   - Force killing containers
#   - Restarting the Docker daemon
#   - Host-level process termination with SIGKILL
#   Use with caution in production environments.
#
# DEPENDENCIES:
#   - common_config.sh (must define PROJECT_NAME, COMPOSE_FILE)
#   - systemctl (for Docker daemon restart)
#   - Standard Unix tools: ps, grep, awk, kill
#
# AUTHORS:
#   Minh Ha-Duong, CNRS
#
# VERSION:
#   1.0
#
################################################################################


set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR"
source "$SCRIPT_DIR/common_config.sh"
trap 'log "❌ An unexpected error occurred."' ERR


# Check if we can access Docker without sudo
check_docker_access() {
    if ! docker ps >/dev/null 2>&1; then
        log "❌ Cannot access Docker daemon. Please:"
        log "   - Add your user to the docker group: sudo usermod -aG docker $USER"
        log "   - Then log out and back in, or run: newgrp docker"
        log "   - Or run this script with sudo"
        exit 2
    fi
}

# Check if we need root for escalation stages
check_root_for_escalation() {
    if [ "$EUID" -ne 0 ]; then
        log "⚠️  Escalation to stages 4-5 requires root privileges."
        log "   Please run: sudo $0"
        exit 1
    fi
}

# Timeouts (in seconds)
DOWN_TIMEOUT=15       # how long to wait for `compose down`
GATHER_TIMEOUT=5     # how long to wait for listing containers
KILL_TIMEOUT=10       # how long to wait for `docker kill`
FORCE_TIMEOUT=10

cleanup_zombie() {
    local step_name="$1"
    log "$step_name) Removing 'created' or 'exited' containers with broken references…"

    local removed_count=0
    local containers
    containers=$(docker ps -aq -f status=created -f status=exited 2>/dev/null || true)

    if [ -n "$containers" ]; then
        for cid in $containers; do
            local cname
            cname=$(docker inspect --format='{{.Name}}' "$cid" 2>/dev/null | cut -c2- || echo "unknown")
            log "   🧹 Removing container: $cname ($cid)"

            if docker rm "$cid" >/dev/null 2>&1; then
                removed_count=$((removed_count + 1))
            fi
        done
    fi

    log "   ✅ Removed $removed_count container(s)."

    log "   🌐 Cleaning up unused networks…"
    docker network prune -f >/dev/null 2>&1 || true

    log "   ✅ Zombie cleanup done."
}


# Initial Docker access check
check_docker_access

########################################
# STAGE 1: docker compose down
########################################

log "1) Attempting graceful shutdown: docker compose down (timeout ${DOWN_TIMEOUT}s)…"
# Note: timeout disallows using function. So inlining the docker_compose_cmd() from common_config.sh
if timeout "${DOWN_TIMEOUT}s" docker compose --project-name "$PROJECT_NAME" -f "$COMPOSE_FILE" down; then
  log "✅ Compose down completed within ${DOWN_TIMEOUT}s."
else
  log "⚠️  Compose down did NOT complete in ${DOWN_TIMEOUT}s."
fi

log "Gathering still-running containers (timeout ${GATHER_TIMEOUT}s)…"
CONTAINERS_RAW=$(timeout "${GATHER_TIMEOUT}s" \
    docker ps \
      --filter "label=com.docker.compose.project=${PROJECT_NAME}" \
      --filter status=running \
      --format '{{.ID}}' 2>/dev/null || true)

# Split into an array
read -r -a CONTAINERS <<<"$CONTAINERS_RAW"

if [ ${#CONTAINERS[@]} -eq 0 ]; then
  log "ℹ️  No containers left to kill."
  cleanup_zombie "finally"
  exit 0
else
  log "Found ${#CONTAINERS[@]} surviving container(s): ${CONTAINERS[*]}"
fi


########################################
# STAGE 2: docker kill
########################################

log "2) Forcing stop with docker kill (timeout ${KILL_TIMEOUT}s)…"
if timeout "${KILL_TIMEOUT}s" docker kill "${CONTAINERS[@]}"; then
  log "✅ docker kill succeeded within ${KILL_TIMEOUT}s."
  cleanup_zombie "finally"
  exit 0
else
  log "❌ docker kill did NOT complete in ${KILL_TIMEOUT}s."
fi

########################################
# STAGE 3: docker rm -f (remove and kill)
########################################

log "3) Attempting force-remove of containers (timeout ${FORCE_TIMEOUT}s)"
if timeout "${FORCE_TIMEOUT}s" docker rm -f "${CONTAINERS[@]}" 2>/dev/null; then
  log "✅ docker rm -f succeeded."
  cleanup_zombie "finally"
  exit 0
else
  log "❌ docker rm -f failed."
fi


########################################
# STAGE 4: Restart Docker daemon (requires root)
########################################

check_root_for_escalation

if command -v systemctl &>/dev/null; then
  log "4) Restarting Docker daemon via systemctl…"
  if timeout 30s systemctl restart docker; then
    log "✅ Docker daemon restarted."
    exit 0
  else
    log "❌ Docker daemon restart timed out."
  fi
else
  log "❌ systemctl command not available."
fi

########################################
# FINAL ESCALATION: host-level kill
########################################
log "5) Escalating: killing container processes on host…"
for cid in "${CONTAINERS[@]}"; do
  pids=$(ps -eo pid,cmd | grep "[d]ockerd.*$cid" | awk '{print $1}')
  for pid in $pids; do
    log "→ killing PID $pid"
    kill -9 "$pid" || true
  done
done

log "❗ Ultimate escalation complete. Manual intervention may still be required."
exit 99
