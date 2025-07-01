# README.md for the deployment directory

HDM, 2025-06-16

## Overview

The docker compose stack includes:
- R2R and its dashboard (core RAG application)
- Postgres with pgvector extension
- Hatchet for workflow management
- Nginx for serving the static web frontend
- FastAPI/Uvicorn for the custom monitoring/analytics backend
- Nginx Proxy Manager to route requests

Compared to R2R-full we disable minio, unstructured and graph-community.
All running on a single server.

## Deployment

- Use the `bootstrap.sh` script to set up the server.
- Use `deploy.sh --remote` to install and start the stack.

## Secrets Management

- Create a `.env` file next to `compose.yaml` to set the `ENV_DIR` variable pointing to `secrets/env`.
- Ensure the `secrets/env` directory is protected:
  ```bash
  chmod 700 secrets
  chmod 600 secrets/env/*
  ```
- Replace default passwords in environment files with strong ones:
  ```bash
  openssl rand -hex 32
  ```
- Verify no cleartext passwords remain:
  ```bash
  grep -R --line-number -E '(_PASS(W?ORD)?|_SECRET|://[^:]+:[^@]+@)' secrets
  ```
- Rotate secrets regularly (30–90 days).


## Hardening Recommendations

- The `bootstrap.sh` includes basic firewalling and other measures.
- Pin container image versions.
- Enforce TLS everywhere.
- Add `--no-new-privileges:true` and drop unnecessary Linux capabilities in Docker services.
- Rotate API keys and passwords regularly.
- Use volumes for logs and the database
- Periodic snapshots and backups
