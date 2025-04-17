# code subdirectory organization

This project's goal is to implement a chatbot with CIRED publications.

## data/
Raw and processed data.
Organization will be updated as we develop the processing.
Not versionned in the git.

**CIRED_numerisation_RAW** contains a read-only copy of pre-1998 publications, scanned OCRed. Remains to be processed.

**pdfs** contents downloaded from HAL.

## docs/
Human‑readable docs, diagrams, README extensions.
Preferably markdown.

## reports/
Generated output.

## src/cired_chatbot/
Our module. Python >= 3.11. Passes ```ruff checks``` with no errors or warnings.

We plan to run a full RAG stack in docker as a separate service, and and deploy ours on the same machine as a use-case-specific layer.

There will be thin HTTP/gRPC wrappers, e.g. ```r2r_client.py``` to communicate with the RAG stack: push documents, ask questions, get justified answer with sources citation and chunk quotes.

We will use env‑vars (e.g. R2R_BASE_URL, R2R_API_KEY) to configure the client at runtime.

**cli** Command line interface tools. Scripts.

## tests/
unit & integration tests
