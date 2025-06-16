# Cirdi: A CIRED digital documentalist

The application is organized in three parts: `intake/`, `frontend/`, and `analytics/`.

## intake/

A command-line ingestion pipeline including:
- `query.py` gets the catalog of open access CIRED publications from HAL
- `download.py` gets the documents (most PDf, some media)
- `prepare_catalog.py` removes oversized files and partially deduplicate
- `push.py` uploads to complete the R2R instance with documents from the catalog.
- `cull.py` removes from the instance any document not found in the catalog
- `verify.py` shows statistics on documents in the R2R

## frontend/

A vanilla HTML/JS standalone web page application. The action loop is:
- User asks a question.
- System shows the RAG answer with sources.
- User provides feedback.

Includes a script to dynamically generate the wordcloud showing the collection themes.

## analytics

A FastAPI/Unicorn server that logs sessions, questions, answers and feedbacks.
Visualization and reporting remain to be developped.
