#!/usr/bin/env bash
set -euo pipefail

# Require root, we may have to restart dockerd and kill processes
if [ "$EUID" -ne 0 ]; then
  echo "⚠️  Please run this script as root: sudo $0"
  exit 1
fi

PROJECT_NAME="myrag"
COMPOSE_FILE="./docker/compose.full.yaml"

# Timeouts (in seconds)
DOWN_TIMEOUT=15       # how long to wait for `compose down`
GATHER_TIMEOUT=5     # how long to wait for listing containers
KILL_TIMEOUT=10       # how long to wait for `docker kill`
FORCE_TIMEOUT=10

echo "1) Attempting graceful shutdown: docker compose down (timeout ${DOWN_TIMEOUT}s)…"
if timeout "${DOWN_TIMEOUT}s" \
     docker compose \
       -f "$COMPOSE_FILE" \
       --project-name "$PROJECT_NAME" \
       --profile postgres \
       down; then

  echo "✅ Compose down completed within ${DOWN_TIMEOUT}s."
  exit 0
else
  echo "⚠️  Compose down did NOT complete in ${DOWN_TIMEOUT}s."
fi

echo
echo "2) Gathering still-running containers (timeout ${GATHER_TIMEOUT}s)…"
# First try with docker compose ps
CONTAINERS_RAW=""
if timeout "${GATHER_TIMEOUT}s" docker compose \
     -f "$COMPOSE_FILE" \
     --project-name "$PROJECT_NAME" \
     --profile postgres \
     ps -q > /tmp/containers.raw 2>/dev/null; then
  CONTAINERS_RAW=$(< /tmp/containers.raw)
else
  echo "⚠️  compose ps timed out or failed—falling back to 'docker ps' filter…"
  CONTAINERS_RAW=$(timeout "${GATHER_TIMEOUT}s" \
      docker ps \
        --filter "label=com.docker.compose.project=${PROJECT_NAME}" \
        --filter status=running \
        --format '{{.ID}}' 2>/dev/null || true)
fi

# Split into an array
read -r -a CONTAINERS <<<"$CONTAINERS_RAW"

if [ ${#CONTAINERS[@]} -eq 0 ]; then
  echo "ℹ️  No containers left to kill."
  exit 1
fi

echo "Found ${#CONTAINERS[@]} container(s): ${CONTAINERS[*]}"
echo "3) Forcing stop with docker kill (timeout ${KILL_TIMEOUT}s)…"

# Wrap docker kill in its own timeout
if timeout "${KILL_TIMEOUT}s" docker kill "${CONTAINERS[@]}"; then
  echo "✅ docker kill succeeded within ${KILL_TIMEOUT}s."
  exit 0
else
  echo "❌ docker kill did NOT complete in ${KILL_TIMEOUT}s."
fi

########################################
# LAYER 4: docker rm -f (remove and kill)
########################################
echo "4) Attempting force-remove of containers (timeoout ${FORCE_TIMEOUT}s)"
if timeout "${FORCE_TIMEOUT}s" docker rm -f "${CONTAINERS[@]}" 2>/dev/null; then
  echo "✅ docker rm -f succeeded."
  exit 0
else
  echo "❌ docker rm -f failed."
fi

########################################
# LAYER 5: Restart Docker daemon
########################################
if command -v systemctl &>/dev/null; then
  echo "5) Restarting Docker daemon via systemctl…"
  if timeout 30s systemctl restart docker; then
    echo "✅ Docker daemon restarted."
    exit 0
  else
    echo "❌ Docker daemon restart timed out."
  fi
fi

########################################
# FINAL ESCALATION: host-level kill
########################################
echo "6) Escalating: killing container processes on host…"
for cid in "${CONTAINERS[@]}"; do
  # find shim/runc PIDs
  pids=$(ps -eo pid,cmd | grep "[d]ockerd.*$cid" | awk '{print $1}')
  for pid in $pids; do
    echo "→ killing PID $pid"
    kill -9 "$pid" || true
  done
done

echo "❗ Ultimate escalation complete. Manual intervention may still be required."
exit 99
