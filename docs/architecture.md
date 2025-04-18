# cired.digital architecture note

We plan to run a full RAG stack in docker as a separate service, and and deploy ours on the same machine as a use-case-specific layer.

There will be:

- an  upstream administration service to sync with HAL and push documents into the RAG stack
- a user-facing interface to  ask questions, get justified answer with sources citation and chunk quotes.
- an analysis backend to see statistics and reports

There will be thin HTTP/gRPC wrappers, e.g. ```r2r_client.py``` to communicate with the RAG stacks. It will be abstracted to a common interface so that different stacks can be used, without excess.

We will use env‑vars (e.g. R2R_BASE_URL, R2R_API_KEY) to configure the client at runtime.
