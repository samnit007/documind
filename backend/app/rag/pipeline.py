import json
import re
from typing import Optional
from pydantic import ValidationError
from app.rag.retriever import retrieve
from app.llm.client import get_llm_client
from app.schemas.response import RAGResponse, Citation

SYSTEM_PROMPT = """You are a technical assistant with expertise in AI engineering tools.
Answer questions using ONLY the provided context. If the context doesn't contain enough
information, say so honestly — do not hallucinate.

Respond with valid JSON matching this exact schema:
{
  "answer": "your answer here",
  "citations": [{"source": "doc name", "section": "section title", "url": "url or null", "excerpt": "short quote"}],
  "confidence": 0.0-1.0,
  "sources_used": ["doc1", "doc2"],
  "token_cost_usd": 0.0
}"""


async def query(question: str, provider: Optional[str] = None) -> RAGResponse:
    chunks = await retrieve(question)
    if not chunks:
        return RAGResponse(
            answer="No relevant documentation found for this question.",
            citations=[],
            confidence=0.0,
            sources_used=[],
            token_cost_usd=0.0,
        )

    context = "\n\n---\n\n".join(
        f"Source: {c.source}\nSection: {c.section}\nURL: {c.url}\n\n{c.content}"
        for c in chunks
    )

    user_prompt = f"Context:\n{context}\n\nQuestion: {question}"

    llm = get_llm_client(provider)
    raw, cost = await llm.complete(system=SYSTEM_PROMPT, user=user_prompt)

    # Parse + validate — retry once on failure
    try:
        data = json.loads(_strip_markdown(raw))
        data["token_cost_usd"] = cost
        return RAGResponse(**data)
    except (json.JSONDecodeError, ValidationError):
        raw2, cost2 = await llm.complete(
            system=SYSTEM_PROMPT,
            user=f"Your previous response was not valid JSON. Return ONLY the JSON object.\n\nQuestion: {question}\n\nContext:\n{context}",
        )
        data = json.loads(_strip_markdown(raw2))
        data["token_cost_usd"] = cost + cost2
        return RAGResponse(**data)


def _strip_markdown(text: str) -> str:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        return match.group(1).strip()
    return text
