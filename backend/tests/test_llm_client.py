import pytest
from app.llm.client import get_llm_client, ClaudeClient, OpenAIClient, OllamaClient
from app.llm.client import _claude_cost, _openai_cost


def test_get_claude_client():
    client = get_llm_client("claude")
    assert isinstance(client, ClaudeClient)


def test_get_openai_client():
    client = get_llm_client("openai")
    assert isinstance(client, OpenAIClient)


def test_get_ollama_client():
    client = get_llm_client("ollama")
    assert isinstance(client, OllamaClient)


def test_unknown_provider_raises():
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        get_llm_client("groq")


def test_claude_haiku_cost_cheaper_than_sonnet():
    haiku_cost = _claude_cost("claude-haiku-4-5-20251001", 1000, 200)
    sonnet_cost = _claude_cost("claude-sonnet-4-6", 1000, 200)
    assert haiku_cost < sonnet_cost


def test_claude_cost_zero_tokens():
    assert _claude_cost("claude-haiku-4-5-20251001", 0, 0) == 0.0


def test_openai_cost_positive():
    cost = _openai_cost("gpt-4o-mini", 500, 100)
    assert cost > 0
