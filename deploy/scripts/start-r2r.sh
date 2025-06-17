#!/bin/bash

# Check if HATCHET_CLIENT_TOKEN is set, if not read it from the API key file
if [ -z "${HATCHET_CLIENT_TOKEN}" ]; then
  export HATCHET_CLIENT_TOKEN=$(cat /hatchet_api_key/api_key.txt)
fi

# HDM-2025-06-17
# Interpolate env vars into TOML file using sed
# Only runs if R2R_CONFIG_PATH is set and file exists

if [ -n "${R2R_CONFIG_PATH:-}" ] && [ -f "$R2R_CONFIG_PATH" ]; then
  RENDERED="${R2R_CONFIG_PATH}+rendered.toml"
  echo "Interpolating $R2R_CONFIG_PATH → $RENDERED"

  cp "$R2R_CONFIG_PATH" "$RENDERED"

  for var in $(env | cut -d= -f1); do
    val=$(printenv "$var" | sed -e 's/[\/&]/\\&/g')  # escape / and &
    sed -i "s|\${$var}|$val|g" "$RENDERED"
  done

  export R2R_CONFIG_PATH="$RENDERED"
else
  echo "R2R_CONFIG_PATH not set or file does not exist — skipping interpolation"
fi

# Start the application
exec uvicorn core.main.app_entry:app --host ${R2R_HOST} --port ${R2R_PORT}
