# README.md for the RAG engine

HDM, 2025-05-26

The RAG engine is R2R, the stack including Postgress and Hatchett is managed with `docker compose`.

compose.yaml            a copy of config.upstream/compose.full.yaml
compose.override.yaml   our own configuration options

config.upstream/        Not versionned in our repo, pulled by scripts/install.sh. This is the docker/ directory from R2R repository. The engine/ directory is basically a copy this, augmented with our own scripts and configuration files. If upstream changes, we will have to manually review and sync.

scripts/                Bash scripts to manage the stack state. The scripts `create-hatchet-db.sh`, `start-r2r.sh` and `setup-token.sh` are copied from `config.upstream` with the permission that R2R is open source. Better not modify them, in case upstream changes.

smoke-tests/            Python scripts to verify that the R2R stack works. Requires `uv` since it uses `uvx` to pull the `r2r` SDK.

env/                    Contains the environment files for the various containers of the stack.

user_configs/           Custom configuration files accessible to the application the `r2r` container. Not used yet.
user_tools/             Custom tool files accessible to the application in the `r2r` container. Not used yet.
