# DocuMind

> A retrieval-augmented Q&A system over Anthropic, LangChain, and Pydantic AI documentation. Ask a question, get a cited answer with confidence scoring and a transparent eval harness measuring retrieval and answer quality.

<!-- TODO: add CI badge, demo URL, screenshot -->

## Problem

AI tooling docs are fragmented across multiple sites. Developers waste time cross-referencing documentation while building. DocuMind indexes the combined corpus and answers questions with cited, validated responses.

## Architecture

<!-- TODO: add architecture diagram (Excalidraw export) -->

```
User question
    ↓
Embed query (OpenAI text-embedding-3-small)
    ↓
Vector search (pgvector / Supabase) — top-5 chunks
    ↓
LLM synthesis (Claude Haiku default / Sonnet toggle)
    ↓
Pydantic validation → retry on parse failure
    ↓
Cited answer + confidence + token cost
```

## Stack

| Layer | Tech |
|---|---|
| Frontend | Vue 3 + Vuetify |
| Backend | FastAPI (Python 3.12) |
| Vector store | pgvector via Supabase |
| Embeddings | OpenAI text-embedding-3-small |
| LLM | Claude Haiku 3.5 (default) / Sonnet 4 (toggle) |
| LLM abstraction | Swappable via `DEFAULT_LLM` env var (claude/openai/ollama) |
| Deploy | Vercel (frontend) + Railway (backend) |

## Run locally

```bash
# 1. Clone and set up backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your keys

# 2. Ingest docs (one-time, ~5 min)
python scripts/ingest.py

# 3. Start API
uvicorn app.main:app --reload

# 4. Frontend (separate terminal)
cd ../frontend
npm install && npm run dev
```

## Evals

<!-- TODO: add eval results table -->

| Metric | Score |
|---|---|
| Retrieval recall@5 | TBD |
| Answer faithfulness | TBD |
| Answer relevance | TBD |

## Tradeoffs & what I'd improve

- **Chunking:** fixed-size chunks lose semantic boundaries — would move to semantic chunking
- **Retrieval:** cosine similarity only — hybrid BM25 + vector would improve recall on exact terms
- **Cost:** Haiku default keeps queries under $0.001 — Sonnet toggle for complex reasoning
- **Scale:** single pgvector instance — would shard by source corpus at larger scale
