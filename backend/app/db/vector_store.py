from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, String, Integer, Text
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


class Base(DeclarativeBase):
    pass


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True)
    source = Column(String(255), nullable=False)
    section = Column(String(512))
    url = Column(String(1024))
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536))  # text-embedding-3-small dimension


engine = create_engine(settings.database_url)


def init_db():
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(engine)


def clear_source(source: str):
    with Session(engine) as session:
        session.query(DocumentChunk).filter(DocumentChunk.source == source).delete()
        session.commit()


def upsert_chunks(chunks: list[dict]):
    with Session(engine) as session:
        for chunk in chunks:
            session.add(DocumentChunk(**chunk))
        session.commit()


def similarity_search(embedding: list[float], k: int = 5) -> list[DocumentChunk]:
    with Session(engine) as session:
        results = (
            session.query(DocumentChunk)
            .order_by(DocumentChunk.embedding.cosine_distance(embedding))
            .limit(k)
            .all()
        )
        return results


def chunk_count() -> int:
    with Session(engine) as session:
        return session.query(DocumentChunk).count()
