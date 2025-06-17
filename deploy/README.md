# README.md for the deployment directory

HDM, 2025-06-16

The stack uses:
- R2R and its dashboard, the core RAG application
- Postgres with pgvector extension
- Hatchet and dependencies for workflow
- unstructured for parsing and extracting documents
- nginx to serve the main user interface as a static web frontend
- FastAPI/uvicorn to serve the custom analytics backend

Not used:
- minio, the S3 compatible files storage service
- graph_clustering, started but should be unused when we disable graph analysis
- earlier releases included logging and analytics services which bugged on newer Ubuntu

External services:
- Commercial LLMs: at present we use OpenAI, Anthropic, DeepSeek, Mistral
- Open LLM: an experimental ollama on CNRS servers
- We do not use Serper, for now web search capability is not used
- We do not use Firecrawl, for now web scrape capability is not used

*Security:*

- Create a `.env` file next to `compose.yaml` to set the `ENV_DIR` variable pointing to `secrets`
- `sops` does not support `toml` format that R2R uses for storing configuration. Its rust rewrite `rops` does.
- The configuration file `user_configs/cidir2r.toml` contains "${R2R_ADMIN_PASSWORD}" instead of the clear text
- The secret is defined in the `env_file` along with all others
- We extend `scripts/start-r2r.sh` to do the interpolation (inject the secrets) at up time.

*What needs manual inspect and sync on upstream R2R changes:*

- Create `config.upstream/` using `ops/install.sh` and delete it with `ops/clean.sh` afterwards.
- Templates for `secrets/env/` directory are the `config.upstream/docker/env/` directory.
- Template for `compose.yaml` file is the `config.upstream/docker/compose.full.yaml`.
- Templates for `user_configs/` are at `https://github.com/SciPhi-AI/R2R/tree/main/py/core/configs`

*Disabling knowledge graphs*
We disable graph building AND graph search globally in the r2r TOML config file:
```
[ingestion]
automatic_extraction = false

[database]
  [database.graph_search_settings]
  enabled = false
```
HDM, 2025-06-17:
Forgetting to disable graph search globally like this can lead to empty retrieval issues,
even when we query the `v3/rag/` endpoint with the search_settings.graph_settings.enabled = false.
