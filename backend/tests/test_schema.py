import pytest
from pydantic import ValidationError
from app.schemas.response import RAGResponse, Citation


def test_valid_response_parses():
    data = {
        "answer": "Claude is an AI assistant.",
        "citations": [
            {
                "source": "Anthropic",
                "section": "Intro",
                "url": "https://docs.anthropic.com",
                "excerpt": "Claude is built by Anthropic.",
            }
        ],
        "confidence": 0.9,
        "sources_used": ["Anthropic"],
        "token_cost_usd": 0.00123,
    }
    response = RAGResponse(**data)
    assert response.answer == "Claude is an AI assistant."
    assert len(response.citations) == 1
    assert response.confidence == 0.9


def test_confidence_rejects_out_of_range():
    with pytest.raises(ValidationError):
        RAGResponse(
            answer="x",
            citations=[],
            confidence=1.5,  # > 1.0, invalid
            sources_used=[],
            token_cost_usd=0.0,
        )


def test_citation_url_optional():
    c = Citation(source="Anthropic", section="Intro", url=None, excerpt="text")
    assert c.url is None


def test_missing_required_field_raises():
    with pytest.raises(ValidationError):
        RAGResponse(
            # answer missing
            citations=[],
            confidence=0.5,
            sources_used=[],
            token_cost_usd=0.0,
        )


def test_empty_citations_valid():
    r = RAGResponse(
        answer="No relevant docs found.",
        citations=[],
        confidence=0.0,
        sources_used=[],
        token_cost_usd=0.0,
    )
    assert r.citations == []
