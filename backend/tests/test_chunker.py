import pytest
from app.rag.chunker import chunk_document


def test_chunk_returns_list_of_dicts():
    text = "Word " * 600  # ~600 tokens, should split into multiple chunks
    chunks = chunk_document(text, source="TestSource", url="https://example.com")
    assert isinstance(chunks, list)
    assert len(chunks) > 1
    for c in chunks:
        assert "source" in c
        assert "content" in c
        assert "url" in c


def test_chunk_metadata_propagated():
    chunks = chunk_document("Hello world " * 10, source="Anthropic", url="https://docs.anthropic.com")
    assert all(c["source"] == "Anthropic" for c in chunks)
    assert all(c["url"] == "https://docs.anthropic.com" for c in chunks)


def test_empty_content_skipped():
    chunks = chunk_document("   \n\n   ", source="X", url="")
    assert chunks == []


def test_chunk_size_respected():
    # Each chunk content should not wildly exceed CHUNK_SIZE (512 tokens ≈ ~2000 chars)
    text = "sentence. " * 1000
    chunks = chunk_document(text, source="X", url="")
    for c in chunks:
        assert len(c["content"]) < 4000, f"Chunk too large: {len(c['content'])} chars"


def test_markdown_headers_used_as_split_points():
    text = "## Section One\n" + "word " * 200 + "\n## Section Two\n" + "word " * 200
    chunks = chunk_document(text, source="X", url="")
    # Should split on ## headers, so at least 2 chunks
    assert len(chunks) >= 2
