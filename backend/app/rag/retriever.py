from typing import Optional
from app.rag.embedder import embed_query
from app.db.vector_store import similarity_search, DocumentChunk
from app.config import settings


async def retrieve(query: str, k: Optional[int] = None) -> list[DocumentChunk]:
    k = k or settings.retrieval_k
    query_embedding = await embed_query(query)
    return similarity_search(query_embedding, k=k)
