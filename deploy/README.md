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

*Security is work-in-progress:*

- Create a `.env` file next to `compose.yaml` to set the `ENV_DIR` variable pointing to `secrets`
- `sops` does not support `toml` format that R2R uses for storing configuration. Its rust rewrite `rops` does.
- TODO: also securely manage secrets from `user_configs/`

*What needs manual inspect and sync on upstream R2R changes:*

- Create `config.upstream/` using `ops/install.sh` and delete it with `ops/clean.sh` afterwards.
- Templates for `secrets/env/` directory are the `config.upstream/docker/env/` directory.
- Template for `compose.yaml` file is the `config.upstream/docker/compose.full.yaml`.
- Templates for `user_configs/` are at `https://github.com/SciPhi-AI/R2R/tree/main/py/core/configs`
