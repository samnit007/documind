from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.rag.pipeline import query as rag_query
from app.schemas.response import RAGResponse

router = APIRouter()


class QueryRequest(BaseModel):
    question: str
    provider: Optional[str] = None  # claude | openai | ollama


@router.post("/query", response_model=RAGResponse)
async def query_endpoint(req: QueryRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    return await rag_query(req.question, provider=req.provider)
