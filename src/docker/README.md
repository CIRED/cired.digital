# README.md for the RAG engine

HDM, 2025-05-26

The RAG engine is R2R, the stack including Postgress and Hatchett is managed with `docker compose`.

CIRED.digital/
└ cired.digital/
  ├ credentials/        # env files with secrets like API keys and admin logins
  ├ data/               # Raw and processed research documents
  ├ docs/               # Technical documentation and guidelines
  ├ reports/            # Analytical outputs
  ├ tests/              # Automated tests, mirroring the src/ directory structure
  └ src/                # Application source code
    ├ analytics/         # Performance and user metrics
    ├ data_preparation/  # Data retrieval and preparation
    ├ frontend/          # Frontend chatbot user interface (Single page app)
    └ docker/            # Scripts for R2R, analytics and frontend containers **YOU ARE HERE**
      ├ compose.yaml          # docker compose configuration.
      ├ ops/                  # Bash scripts to manage the stack state.
      ├ smoke-tests/          # Python scripts to verify that the R2R stack works.
      ├ user_configs/         # Custom configuration files accessible to the application the `r2r` container. Not used yet.
      ├ user_tools/           # Custom tool files accessible to the application in the `r2r` container. Not used yet.
      ├ scripts/              # Scripts made available to r2r container. Copied from `config.upstream`, do not modify.
      └ config.upstream/      # Temporary directory not versionned in our repo.

*Notes:*

. Scripts in `smoke-tests/` require `uv` since it uses `uvx` to pull the `r2r` SDK.

. This `docker/` directory mirrors the `docker/` directory from R2R repository, with edits to the compose file our own scripts and configuration files. If upstream changes, we have to manually inspect and sync. To that end, the dir `config.upstream` can be created by `ops/install.sh` and deleted by `ops/clean.sh`.
