from typing import Optional
from pydantic import BaseModel, Field


class Citation(BaseModel):
    source: str
    section: str
    url: Optional[str] = None
    excerpt: str


class RAGResponse(BaseModel):
    answer: str = Field(description="Direct answer to the question")
    citations: list[Citation] = Field(description="Sources used to construct the answer")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0-1")
    sources_used: list[str] = Field(description="Document names retrieved")
    token_cost_usd: float = Field(description="Estimated cost of this query in USD")
