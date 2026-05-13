from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.config import settings


def chunk_document(content: str, source: str, section: str = "", url: str = "") -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
    )
    texts = splitter.split_text(content)
    return [
        {"source": source, "section": section, "url": url, "content": t}
        for t in texts
        if t.strip()
    ]
