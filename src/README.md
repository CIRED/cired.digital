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

Javascript uses the classic, not the ES-modules variant or Typescript.

Includes a Python script to dynamically generate the wordcloud showing the collection themes.
For commercial providers, we only include a **cost effective** (read: cheap) model.

Models pricing and strings:

- (Anthropic)[https://docs.anthropic.com/en/docs/about-claude/models/overview]
- (Deepseek)[https://api-docs.deepseek.com/quick_start/pricing]
- (Mistral)[https://mistral.ai/pricing#api-pricing]
- (OpenAI)[https://platform.openai.com/docs/pricing] and [https://openai.com/api/pricing/]


## analytics

A FastAPI/Unicorn server that logs sessions, questions, answers and feedbacks.
Visualization and reporting remain to be developped.
