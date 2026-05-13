# DocuMind

> A retrieval-augmented Q&A system over the combined Anthropic, LangChain, LangGraph, and Pydantic AI documentation. Ask a question in plain English — get a cited answer with confidence scoring, per-query cost tracking, and a transparent eval harness.

**Live demo:** [documind-ashy.vercel.app](https://documind-ashy.vercel.app)

## Problem

AI tooling docs are fragmented across multiple sites. Developers waste time cross-referencing Anthropic, LangChain, and Pydantic AI documentation while building. DocuMind indexes the combined corpus (1,699 chunks across 29 pages) and answers questions with cited, validated responses — so you stay in flow.

## Architecture

```
User question
    │
    ▼
Embed query          OpenAI text-embedding-3-small
    │
    ▼
Vector search        pgvector on Supabase — top-5 chunks by cosine similarity
    │
    ▼
LLM synthesis        Claude Haiku (default) or GPT-4o mini (toggle)
    │
    ▼
Pydantic validation  Enforce {answer, citations[], confidence, sources_used, cost}
    │                Retry once on parse failure
    ▼
Cited answer + confidence score + token cost displayed in UI
```

## Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | Vue 3 + TypeScript + Tailwind | Full-stack ownership, no UI framework lock-in |
| Backend | FastAPI + Python | Standard AI engineering stack |
| Vector store | pgvector on Supabase | SQL-native vector search, production-viable |
| Embeddings | OpenAI `text-embedding-3-small` | Cheapest viable model ($0.02/M tokens) |
| LLM | Claude Haiku default, provider toggle | Cost-aware; swappable via `LLMClient` abstraction |
| Output validation | Pydantic v2 schema + retry | LLM output is untrusted; validate and recover |
| Deploy | Vercel (frontend) + Railway (backend) | Real infra, not localhost |

## Eval results

20 questions across single-source, multi-source, and no-answer categories. Retrieval metrics computed from pgvector similarity scores; answer quality scored by Claude Haiku as judge.

| Metric | Score | Notes |
|---|---|---|
| **Recall@5** | **1.000** | Correct source in top 5 for all 20 questions |
| **MRR** | **1.000** | Relevant chunk always ranked #1 |
| **Faithfulness** | **0.920** | Answers grounded in retrieved context |
| **Relevance** | **0.778** | 3 questions hit corpus gaps → honest refusal penalised by judge |
| Avg latency | 5.8s | Claude Haiku on Railway free tier |
| Total eval cost | $0.069 | 20 queries + 20 judge calls |

**Corpus gaps (Q12, Q15, Q18):** these questions hit topics not well-covered in ingested pages. The system correctly responds "context doesn't contain this information" — honest RAG behaviour, but the LLM judge penalises refusals. Fix: ingest more targeted pages.

Full results in [`evals/results.json`](evals/results.json).

## Run locally

```bash
# 1. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in ANTHROPIC_API_KEY, OPENAI_API_KEY, DATABASE_URL

# 2. Ingest docs (one-time, ~3 min, costs ~$0.02 in embeddings)
python scripts/ingest.py

# 3. Start API
uvicorn app.main:app --reload --port 8000

# 4. Frontend (separate terminal)
cd ../frontend
npm install && npm run dev
# → http://localhost:5173
```

## Corpus

| Source | Pages | Chunks |
|---|---|---|
| Anthropic (platform.claude.com .md files) | 9 | 519 |
| LangChain + LangGraph (docs.langchain.com .md files) | 12 | 683 |
| Pydantic AI (ai.pydantic.dev HTML) | 8 | 497 |
| **Total** | **29** | **1,699** |

Docs are fetched as plain-text `.md` files where available (Anthropic, LangChain) to avoid JS-rendering issues. Pydantic AI uses BeautifulSoup HTML scraping (SSR site, works reliably).

## Tradeoffs & what I'd improve

- **Chunking:** fixed-size 512-token chunks lose semantic boundaries — would move to semantic/late chunking for denser retrieval signal
- **Retrieval:** cosine similarity only — hybrid BM25 + vector (reciprocal rank fusion) would improve recall on exact API names and method signatures
- **Faithfulness dip on CoT/embeddings pages:** those pages are very long; chunking splits mid-explanation. Larger chunk size or parent-document retrieval would help
- **Corpus staleness:** docs change; would add a weekly re-ingest cron job in production
- **Streaming:** current UX shows a loading spinner; streaming tokens would improve perceived responsiveness
- **Auth:** no rate limiting — would add per-IP limits before any public scale
