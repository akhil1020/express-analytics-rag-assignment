# Technical Documentation Assistant

A self-correcting RAG service for technical documentation. It uses FastAPI for the API, ChromaDB for local vector search, Ollama for local embeddings and LLM calls, and LangGraph to make the retrieval decision path explicit.

## Architecture

```text
POST /ingest → text extraction → paragraph-aware chunks → embeddings → ChromaDB

POST /query → query analysis → vector retrieval → LLM document grading
                                                    ├─ relevant → grounded answer + citations
                                                    └─ none → rewrite and retry (maximum 2) → I don't know
```

The graph state carries the question, rewritten search query, retrieved chunks, accepted chunks, retry count, and answer. This keeps the grading decision and retry limit visible rather than hiding them in one large prompt.

## Setup

1. Install dependencies with `uv sync`.
2. Start Ollama and make sure `llama3.2:latest` plus `nomic-embed-text` are available. Run `ollama pull nomic-embed-text` once if necessary. Optionally set `OLLAMA_MODEL` or `OLLAMA_EMBEDDING_MODEL`.
3. Start the API with `uv run fastapi dev main.py`.

The default models are local `llama3.2:latest` and `nomic-embed-text`, so the system needs no API key or paid provider.

The repository includes three short technical-documentation files in `docs/`. Index them before asking questions:

```bash
uv run python seed_corpus.py
```

## API examples

```bash
curl -X POST http://127.0.0.1:8000/ingest/ -F "files=@docs/fastapi_notes.md"
curl -X POST http://127.0.0.1:8000/ingest/ -F "urls=https://example.com/docs.html"
curl -X POST http://127.0.0.1:8000/query -H "Content-Type: application/json" -d "{\"question\": \"How do I validate request data?\"}"
```

`GET /documents` lists the corpus. `POST /feedback` takes a question, answer, boolean `helpful`, and optional comment.

## Design decisions and trade-offs

- Files and URLs are accepted because the brief permits either input path. PDF support is included in addition to Markdown, text, and HTML.
- Chunks target 1,000 characters with a 200-character overlap. Splitting first on paragraph boundaries keeps code examples and explanatory text together more often than a character-only splitter.
- Every retrieved chunk is individually graded by the LLM. The extra calls cost more than a plain RAG chain, but they make the corrective routing meaningful on a small corpus.
- ChromaDB persists locally under `data/`; a small JSON registry makes `GET /documents` easy to understand without adding a database schema.
- With more time, I would add background ingestion for large files, structured query classification, evaluation cases, and the optional groundedness/web-search features.

## Assumptions

- Ollama is running locally and the configured chat and embedding models have been pulled.
- Uploaded PDFs contain selectable text; OCR for scanned pages is intentionally out of scope.
- The API is local for this take-home exercise. URL ingestion should sit behind network controls in production.
"# express-analytics-rag-assignment" 
