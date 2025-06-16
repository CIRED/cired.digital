# CIRED Chatbot Architecture Overviewb

This README provides a code architecture overview of the chatbot system being developed for CIRED. A more detailed description is available in the document `docs/blueprints.md`.

## Main Objectives

The chatbot enables users to pose natural-language queries and obtain accurate, citation-supported answers from CIRED’s research corpus. Multiple Retrieval-Augmented Generation (RAG) engines, such as R2R, Morphik, and PaperQA, will be integrated and evaluated side-by-side. The architecture emphasizes openness and reproducibility by sharing all code publicly. User privacy and compliance with GDPR standards will be rigorously maintained. Data-driven performance metrics will guide continuous improvement of the system.

## Source Code Organization (`src/`)

The `src/` directory is organized into specific subdirectories: `intake/`, `engine/`, `frontend/`, and `analytics/`.

### Data Preparation (`intake/`)

The ingestion pipeline is:
- `query.py` gets the catalog of open access CIRED publications from HAL
- `download.py` gets the documents (most PDf, some media)
- `prepare_catalog.py` removes oversized files and partially deduplicate
- `push.py` uploads to complete the R2R instance with documents from the catalog.
- `cull.py` removes from the instance any document not found in the catalog
- `verify.py` shows statistics on documents in the R2R

### Frontend Interface (`frontend/`)

A standalone web page application in vanilla HTML/JS.
Ask a question, get the RAG answer with sources, give feedback.

### Analytics (`analytics/`)

Logs sessions, questions, answers and feedback.
Soon: Add user profile.

### Stack management (`docker/`)

The docker configuration files for the containers stack: database, orchestration, RAG engine, frontend, analytics.
The script to start/stop the application is `src/docker/ops/up.sh`

## Testing Strategy

Planned: Automated tests verify functionality across ingestion, storage, RAG integration, frontend interactions, and API responses, ensuring robustness and reliability.

## Operational and Ethical Guidelines

The project strictly adheres to GDPR, promotes transparency, and maintains comprehensive documentation. Operational costs are closely monitored.

## Sensitive Information Handling

Credentials and sensitive data are stored securely, separate from the project repository, ensuring confidentiality and security.
