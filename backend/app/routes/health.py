from fastapi import APIRouter
from app.db.vector_store import chunk_count

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok", "chunks_indexed": chunk_count()}
