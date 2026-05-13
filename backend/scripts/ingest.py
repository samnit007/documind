"""
Scrape and ingest documentation into pgvector.

Usage:
    python scripts/ingest.py

Strategy per source:
  - Anthropic: fetch .md files from platform.claude.com (clean markdown, no JS)
  - LangChain/LangGraph: fetch .md files from docs.langchain.com (clean markdown)
  - Pydantic AI: HTML scrape ai.pydantic.dev (JS-free SSR site, works fine)
"""

import asyncio
import re
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import httpx
from bs4 import BeautifulSoup
from app.rag.chunker import chunk_document
from app.rag.embedder import embed_texts
from app.db.vector_store import init_db, upsert_chunks, clear_source

SOURCES = [
    {
        "name": "Anthropic",
        "mode": "md",
        "urls": [
            "https://platform.claude.com/docs/en/intro.md",
            "https://platform.claude.com/docs/en/about-claude/models/overview.md",
            "https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview.md",
            "https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/chain-of-thought.md",
            "https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview.md",
            "https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use.md",
            "https://platform.claude.com/docs/en/build-with-claude/embeddings.md",
            "https://platform.claude.com/docs/en/build-with-claude/context-windows.md",
            "https://platform.claude.com/docs/en/build-with-claude/batch-processing.md",
        ],
    },
    {
        "name": "LangChain",
        "mode": "md",
        "urls": [
            "https://docs.langchain.com/oss/python/langchain/overview.md",
            "https://docs.langchain.com/oss/python/langchain/rag.md",
            "https://docs.langchain.com/oss/python/langchain/retrieval.md",
            "https://docs.langchain.com/oss/python/langchain/agents.md",
            "https://docs.langchain.com/oss/python/langchain/tools.md",
            "https://docs.langchain.com/oss/python/langchain/chat-models.md",
            "https://docs.langchain.com/oss/python/langchain/embedding-models.md",
            "https://docs.langchain.com/oss/python/langgraph/overview.md",
            "https://docs.langchain.com/oss/python/langgraph/workflows-agents.md",
            "https://docs.langchain.com/oss/python/langgraph/persistence.md",
            "https://docs.langchain.com/oss/python/langgraph/streaming.md",
            "https://docs.langchain.com/oss/python/langgraph/agentic-rag.md",
        ],
    },
    {
        "name": "Pydantic AI",
        "mode": "html",
        "urls": [
            "https://ai.pydantic.dev/",
            "https://ai.pydantic.dev/agents/",
            "https://ai.pydantic.dev/models/",
            "https://ai.pydantic.dev/tools/",
            "https://ai.pydantic.dev/dependencies/",
            "https://ai.pydantic.dev/output/",
            "https://ai.pydantic.dev/multi-agent-applications/",
            "https://ai.pydantic.dev/testing-evals/",
        ],
    },
]

BATCH_SIZE = 32
MDX_TAG_RE = re.compile(r"<[A-Z][A-Za-z]*[^>]*>|</[A-Z][A-Za-z]*>|\{[^}]*\}")


async def fetch_md(url: str) -> str:
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "DocuMind-Ingestion/1.0"})
        resp.raise_for_status()
    text = resp.text
    # Strip MDX component tags (e.g. <Tip>, <CodeGroup>, {/* comment */})
    text = MDX_TAG_RE.sub("", text)
    # Strip the doc-index header that docs.langchain.com prepends
    text = re.sub(r"^>.*\n", "", text, flags=re.MULTILINE)
    return text.strip()


async def fetch_html(url: str) -> str:
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "DocuMind-Ingestion/1.0"})
        resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup.select("nav, header, footer, script, style, .sidebar"):
        tag.decompose()
    main = soup.find("main") or soup.find("article") or soup.body
    return main.get_text(separator="\n", strip=True) if main else ""


async def ingest_source(source: dict):
    print(f"\n→ Ingesting {source['name']} ({len(source['urls'])} pages) [{source['mode']}]")
    print(f"  Clearing existing {source['name']} chunks...")
    clear_source(source["name"])

    all_chunks = []
    fetch = fetch_md if source["mode"] == "md" else fetch_html

    for url in source["urls"]:
        try:
            text = await fetch(url)
            if not text or len(text) < 100:
                print(f"  ⚠ Empty/short: {url}")
                continue
            chunks = chunk_document(text, source=source["name"], url=url)
            all_chunks.extend(chunks)
            print(f"  ✓ {url} → {len(chunks)} chunks")
        except Exception as e:
            print(f"  ✗ {url}: {e}")

    if not all_chunks:
        return

    print(f"  Embedding {len(all_chunks)} chunks...")
    for i in range(0, len(all_chunks), BATCH_SIZE):
        batch = all_chunks[i:i + BATCH_SIZE]
        embeddings = await embed_texts([c["content"] for c in batch])
        for chunk, emb in zip(batch, embeddings):
            chunk["embedding"] = emb
        upsert_chunks(batch)
        print(f"  Stored batch {i // BATCH_SIZE + 1}/{-(-len(all_chunks) // BATCH_SIZE)}")

    print(f"  ✓ {source['name']} done — {len(all_chunks)} chunks stored")


async def main():
    print("Initialising database...")
    init_db()

    for source in SOURCES:
        await ingest_source(source)

    print("\n✓ Ingestion complete.")


if __name__ == "__main__":
    asyncio.run(main())
