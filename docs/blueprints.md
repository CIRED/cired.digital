# Architecture Overview

This document outlines a fit-for-purpose architecture for the CIRED digital chatbot project, reflecting its research goals: conversational access to HAL publications, open‑source replicability, multi-engine RAG comparisons, and robust analytics.

An introductory overview is available in `src/README.md`, this is the detailed version. This is a conceptual blueprint. Most of these files do not exist yet, and never will because:

> "The best-laid schemes o’ mice an’ men / Gang aft agley,"
(To a mouse, Robert Burns, 1785)

## 1. Research Aims & Key Requirements

Before diving into directories, recall our core objectives:

1. **Conversational Science Mediation**: Users ask natural-language questions over CIRED’s HAL collection, receiving answers with precise citations and context.
2. **Modular RAG Engine Comparison**: Side-by-side benchmarking of multiple RAG engines (R2R, Morphik, PaperQA, etc.) on the same corpus.
3. **Open Science & Reproducibility**: All code, configurations, and pipelines are open-source, parameterized, and documented for use on any HAL collection.
4. **Ethical & Privacy Compliance**: Anonymize user interactions, log citations transparently, and respect GDPR.
5. **Data-Driven Optimization**: Collect metrics (latency, accuracy, cost, user feedback) and enable rapid iteration via notebooks and automated workflows.

> Keep these goals in mind as you work—each component you build should contribute to at least one of these objectives.


## 2. Top level repository layout

```text
project-root/  ← cired.digital/
├── data/        ← raw PDFs, extracted text, chunks, vector indexes
├── docs/        ← architecture docs, OpenAPI spec, runbooks, ethics guidelines
├── reports/     ← evaluation dashboards
├── src/         ← source code modules (see Section 3)
└── tests/       ← unit, integration, end-to-end tests mirroring `src/`
```

> Think of these top-level folders as your guideposts. You’ll add code under `src/`, tests under `tests/`, and outputs under `data/` or `reports/`.


## 3. Source code organization

```text
src/
├── data_preparation/ ← fetch & chunk pipelines, versioning, indexing
├── rag_engines/      ← engine adapters & common interface
├── api/              ← Q&A service
├── frontend/         ← chat UI & A/B framework
├── analytics/        ← KPIs, benchmarks, notebooks
├── libs/             ← shared utilities (config, logging, utils)
└── orchestration/    ← workflow definitions & automation
```

Each folder under `src/` aligns with a research step.

### 3.1. Data preparation

  - `fetch_hal.py`: incremental syncing from HAL API (XML → text).
  - `pdf_processor.py`: OCR fallback for missing text.
  - `chunker.py`: section-aware, sliding-window semantic chunking.
  - CLI (`ingest.py`) with flags `--since`, `--batch-size`, `--engine`.
  - `versioned/`: DVC or Git-LFS tracking of raw & processed artifacts.
  - `catalog.py`: index metadata (title, authors, date) in JSON. HAL provides it, we may need to.

> **Tip:** Write small unit tests for each step in and practice running `ingest.py` commands with different flags to see how idempotency works.

### 3.2. RAG Engine Adapters

- **Interface**: Define a `BaseEngine` in `rag_engines/common.py`:
  ```python
  class BaseEngine:
      def index(self, chunks): ...
      def query(self, prompt): ...
      def teardown(self): ...
  ```
- **Clients**: Implement `r2r_client.py`, `morphik_client.py`, `paperqa_client.py`, etc., each extending `BaseEngine`.
- **Config**: `docs/engines.yaml` maps engine names to Docker images or service endpoints.

> **Tip:** When adding a new engine, start by copying an existing client and adjust only the config and API calls. Run its unit tests before integrating.

### 3.3. API Service

- **Framework**: FastAPI
- **Endpoints**:
  - `POST /qa`: accepts `question`, `engine`, `max_tokens`, returns answer + citations + metadata.
  - `GET /health` and `GET /metrics` for service status and Prometheus metrics.
- **Middleware**: Logging middleware captures timings, engine used, and user consent.
- **Docker**: `Dockerfile` builds the service container.

> **Tip:** Keep routers thin—put business logic in `services/` modules. Use FastAPI’s interactive docs (`/docs`) to test endpoints.

### 3.4. Frontend Chat & A/B Framework

- **Framework**: Next.js + React
- **Structure**:
  - `components/`: ChatWindow, CitationList, FeedbackButtons.
  - `pages/`: `/`, `/admin`, `/analytics`.
  - `lib/`: API wrappers using SWR for caching.
  - `styles/`: Tailwind CSS config.
- **Features**:
  - Real-time chat with streaming responses.
  - A/B toggle or duel mode to compare two engines side by side.
  - Consent banner and thumbs up/down feedback.

> **Tip:** Start by modifying an existing component (e.g., ChatWindow). Use React DevTools and inspect props to understand data flow.

### 3.5. Analytics & Metrics

- **metrics/definitions.py**: precision@k, latency, cost-per-query, citation-coverage functions.
- **scripts/run_benchmark.py**: CLI to run sample queries across engines and output JSON results.
- **notebooks/**: exploratory analysis of trade-offs and chunk-size tuning.

> **Junior Tip:** Write a small script using one metric function and run it on a dummy JSON result file. Visualize outputs in a minimal Jupyter cell.

### 3.6. Orchestration & Automation

- **Tool**: Prefect
- **Flows**:
  - `ingest_flow`: run ingestion pipeline.
  - `index_flow`: index chunks into each engine.
  - `benchmark_flow`: run queries and collect results.
  - `report_flow`: generate dashboards and PDF summaries.
- **Scheduling**: Daily or triggered on data updates.
- **Alerts**: Slack/email notifications on failures or regressions.

> **Junior Tip:** Explore an existing Prefect flow, run it locally (`prefect flow run`), and examine the logs in the Prefect UI.


## 4. Testing Strategy (`tests/`)

Mirror each `src/` component:

```
tests/
├── data_preparation/
├── rag_engines/
├── api/
├── frontend/
└── analytics/
```

- **pytest** for Python modules; mock external APIs (HAL, engines).
- **Jest** for React components; use MSW to mock `/api/qa`.
- **End-to-end**: ingest sample PDFs, spin up a test engine, query via API, and verify UI renders citations. Use Cypress or Playwright

> **Tip:** Start by writing unit tests for one small function in `libs/utils/`—get familiar with test fixtures and mocking.

## 5. Ethical & Operational Considerations

- **GDPR compliance**: anonymize and purge PII on schedule via Prefect tasks.
- **Open Science**: version control all configs (`docs/*.yaml`), licenses, and data schemas.
- **Scalability**: containerized services ready for Kubernetes deployment.
- **Cost monitoring**: tag queries with cost metadata; surface in `/metrics` and `reports/`.

> **Tip:** Read the GDPR purge flow in `orchestration/report_flow.py` to see how PII cleanup is automated.


## 6. Secrets

Files with API keys are not versionned under `cired.digital/` but stored in `credentials/` which is a sibling directory.
