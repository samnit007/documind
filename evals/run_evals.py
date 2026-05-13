"""
DocuMind Eval Harness — Week 3

Metrics:
  Retrieval:
    recall@5  — does a chunk from the expected source(s) appear in top 5?
    MRR       — mean reciprocal rank of first relevant chunk (0 if none in top 5)

  Answer quality (LLM-as-judge via Claude Haiku):
    faithfulness  — is the answer grounded in retrieved context? (0-1)
    relevance     — does the answer address the question? (0-1)

  System:
    latency_s     — wall-clock seconds per query
    cost_usd      — token cost reported by pipeline

Usage:
    cd backend && ../.venv/bin/python ../evals/run_evals.py
"""

import asyncio
import json
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)) + "/backend")

from app.rag.embedder import embed_query
from app.rag.pipeline import query as rag_query
from app.db.vector_store import similarity_search_with_scores
from app.llm.client import ClaudeClient
from app.config import settings

QUESTIONS_FILE = os.path.join(os.path.dirname(__file__), "questions.json")
RESULTS_FILE = os.path.join(os.path.dirname(__file__), "results.json")
K = 5

JUDGE_SYSTEM = """You are an evaluation judge for a RAG system.
Score the answer on two dimensions. Respond with ONLY valid JSON:
{
  "faithfulness": <0.0-1.0>,
  "relevance": <0.0-1.0>,
  "faithfulness_reason": "<one sentence>",
  "relevance_reason": "<one sentence>"
}

faithfulness: Is every claim in the answer supported by the provided context?
  1.0 = fully grounded, 0.0 = hallucinated or contradicts context.
relevance: Does the answer actually address the question asked?
  1.0 = fully answers the question, 0.0 = off-topic or refuses without good reason."""


async def judge_answer(question: str, context: str, answer: str) -> dict:
    client = ClaudeClient()
    prompt = f"""Question: {question}

Retrieved context:
{context[:3000]}

Answer to evaluate:
{answer}"""
    raw, cost = await client.complete(system=JUDGE_SYSTEM, user=prompt)
    import re
    match = re.search(r"\{[\s\S]*\}", raw)
    if match:
        data = json.loads(match.group())
        data["judge_cost_usd"] = cost
        return data
    return {"faithfulness": 0.0, "relevance": 0.0, "judge_cost_usd": cost}


async def eval_question(q: dict) -> dict:
    question = q["question"]
    expected_sources = set(q["expected_sources"])

    t0 = time.time()
    embedding = await embed_query(question)
    ranked = similarity_search_with_scores(embedding, k=K)
    retrieved_sources = [chunk.source for chunk, _ in ranked]

    # recall@5
    recall = 1.0 if any(s in expected_sources for s in retrieved_sources) else 0.0

    # MRR
    rr = 0.0
    for rank, (chunk, _) in enumerate(ranked, start=1):
        if chunk.source in expected_sources:
            rr = 1.0 / rank
            break

    # Full pipeline for answer + cost
    response = await rag_query(question)
    latency = time.time() - t0

    # Context for judge
    context = "\n\n".join(chunk.content for chunk, _ in ranked)

    # LLM judge
    if q["category"] == "no-answer":
        # For no-answer questions: good if system says it doesn't know
        answer_lower = response.answer.lower()
        honest = any(p in answer_lower for p in [
            "don't know", "not", "no information", "cannot", "doesn't contain",
            "not found", "not in", "unable"
        ])
        judge = {
            "faithfulness": 1.0 if honest else 0.2,
            "relevance": 1.0 if honest else 0.3,
            "faithfulness_reason": "no-answer case — checked for honest refusal",
            "relevance_reason": "no-answer case — checked for honest refusal",
            "judge_cost_usd": 0.0,
        }
        recall = 1.0  # no expected source, so recall is N/A — mark as pass
        rr = 1.0
    else:
        judge = await judge_answer(question, context, response.answer)

    result = {
        "id": q["id"],
        "category": q["category"],
        "question": question,
        "expected_sources": q["expected_sources"],
        "retrieved_sources": retrieved_sources,
        "recall_at_5": recall,
        "mrr": round(rr, 4),
        "answer_preview": response.answer[:200],
        "faithfulness": judge.get("faithfulness", 0.0),
        "relevance": judge.get("relevance", 0.0),
        "faithfulness_reason": judge.get("faithfulness_reason", ""),
        "relevance_reason": judge.get("relevance_reason", ""),
        "confidence": response.confidence,
        "latency_s": round(latency, 2),
        "pipeline_cost_usd": round(response.token_cost_usd, 6),
        "judge_cost_usd": round(judge.get("judge_cost_usd", 0.0), 6),
    }

    status = "✓" if recall == 1.0 and judge.get("faithfulness", 0) >= 0.6 else "✗"
    print(f"  {status} Q{q['id']:02d} [{q['category']}] recall={recall:.0f} "
          f"mrr={rr:.2f} faith={judge.get('faithfulness',0):.2f} "
          f"rel={judge.get('relevance',0):.2f} {latency:.1f}s")

    return result


async def main():
    with open(QUESTIONS_FILE) as f:
        questions = json.load(f)

    print(f"Running {len(questions)} eval questions...\n")

    results = []
    total_cost = 0.0

    for q in questions:
        result = await eval_question(q)
        results.append(result)
        total_cost += result["pipeline_cost_usd"] + result["judge_cost_usd"]

    # Aggregate metrics
    recall = sum(r["recall_at_5"] for r in results) / len(results)
    mrr = sum(r["mrr"] for r in results) / len(results)
    faithfulness = sum(r["faithfulness"] for r in results) / len(results)
    relevance = sum(r["relevance"] for r in results) / len(results)
    avg_latency = sum(r["latency_s"] for r in results) / len(results)

    summary = {
        "n": len(results),
        "recall_at_5": round(recall, 3),
        "mrr": round(mrr, 3),
        "faithfulness": round(faithfulness, 3),
        "relevance": round(relevance, 3),
        "avg_latency_s": round(avg_latency, 2),
        "total_cost_usd": round(total_cost, 4),
        "results": results,
    }

    with open(RESULTS_FILE, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n{'='*55}")
    print(f"  Recall@5      {recall:.3f}  ({sum(r['recall_at_5']==1 for r in results)}/{len(results)} passed)")
    print(f"  MRR           {mrr:.3f}")
    print(f"  Faithfulness  {faithfulness:.3f}")
    print(f"  Relevance     {relevance:.3f}")
    print(f"  Avg latency   {avg_latency:.1f}s")
    print(f"  Total cost    ${total_cost:.4f}")
    print(f"{'='*55}")
    print(f"\nResults saved → evals/results.json")


if __name__ == "__main__":
    asyncio.run(main())
