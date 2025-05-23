# CIRED Chatbot Architecture Overview

This README provides a code architecture overview of the chatbot system being developed for CIRED. A more detailed description is available in the document `docs/blueprints.md`.

## Main Objectives

The chatbot enables users to pose natural-language queries and obtain accurate, citation-supported answers from CIRED’s research corpus. Multiple Retrieval-Augmented Generation (RAG) engines, such as R2R, Morphik, and PaperQA, will be integrated and evaluated side-by-side. The architecture emphasizes openness and reproducibility by sharing all code publicly. User privacy and compliance with GDPR standards will be rigorously maintained. Data-driven performance metrics will guide continuous improvement of the system.

## Where you are in the project

```text
CIRED.digital/
└── cired.digital/
    ├── data/               # Raw and processed research documents
    ├── docs/               # Technical documentation and guidelines
    ├── reports/            # Analytical outputs
    ├── src/                # Application source code **YOU ARE HERE**
    │   ├── analytics/         # Performance and user metrics
    │   ├── data_preparation/  # Data retrieval and preparation
    │   ├── engine/            # Scripts to manage the backend (R2R)
    │   └── frontend/          # Frontend chatbot user interface (Single page app)
    └── tests/              # Automated tests, mirroring the src/ directory structure
        ├── analytics/
        ├── data_preparation/
        ├── engine/
        └── frontend/
```
> Note: The cired.digital/ repository is a subdirectory of the top-level CIRED.digital/ project directory, not versionned. The tests/ directory inside cired.digital/ mirrors the structure of src/ to facilitate targeted and modular testing.

## Source Code Organization (`src/`)

The `src/` directory is organized into specific subdirectories: `ingestion/`, `storage/`, `rag_engines/`, `api/`, `frontend/`, `analytics/`, `libs/`, and `orchestration/`.

### Data Preparation (`data_preparation/`)

The ingestion pipeline retrieves research papers from the HAL database, processes them, and segments the content for indexing and storage.

### RAG Engines (`rag_engines/`)

The system integrates multiple RAG engines using a standardized interface, allowing efficient performance comparisons.

### Backend API Service (`api/`)

The API manages incoming user queries, interacts with RAG engines for response retrieval, and coordinates system communication.

### Frontend Interface (`frontend/`)

A Next.js and React-based interactive chat interface enables real-time querying, user feedback, and side-by-side comparison of different engines.

### Analytics (`analytics/`)

Costs, performance and user satisfaction are tracked via clearly defined metrics, guiding future enhancements.

### Workflow Automation (`orchestration/`)

Routine processes, including data updates, testing, and reporting, are automated to streamline operations.

## Testing Strategy

Automated tests verify functionality across ingestion, storage, RAG integration, frontend interactions, and API responses, ensuring robustness and reliability.

## Operational and Ethical Guidelines

The project strictly adheres to GDPR, promotes transparency, and maintains comprehensive documentation. Operational costs are closely monitored.

## Sensitive Information Handling

Credentials and sensitive data are stored securely, separate from the project repository, ensuring confidentiality and security.


