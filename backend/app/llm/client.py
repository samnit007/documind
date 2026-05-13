from abc import ABC, abstractmethod
from typing import Any, Optional
import anthropic
import openai
from app.config import settings


class LLMClient(ABC):
    @abstractmethod
    async def complete(self, system: str, user: str, model: Optional[str] = None) -> tuple[str, float]:
        """Returns (response_text, cost_usd)."""


class ClaudeClient(LLMClient):
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def complete(self, system: str, user: str, model: Optional[str] = None) -> tuple[str, float]:
        model = model or settings.fast_model
        response = await self.client.messages.create(
            model=model,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        cost = _claude_cost(model, response.usage.input_tokens, response.usage.output_tokens)
        return response.content[0].text, cost


class OpenAIClient(LLMClient):
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

    async def complete(self, system: str, user: str, model: Optional[str] = None) -> tuple[str, float]:
        model = model or "gpt-4o-mini"
        response = await self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        cost = _openai_cost(model, response.usage.prompt_tokens, response.usage.completion_tokens)
        return response.choices[0].message.content, cost


class OllamaClient(LLMClient):
    """Local Ollama — zero API cost. Set OLLAMA_BASE_URL if not localhost."""

    def __init__(self):
        import os
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

    async def complete(self, system: str, user: str, model: Optional[str] = None) -> tuple[str, float]:
        import httpx
        payload = {
            "model": model or self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{self.base_url}/api/chat", json=payload)
            resp.raise_for_status()
        return resp.json()["message"]["content"], 0.0


def get_llm_client(provider: Optional[str] = None) -> LLMClient:
    provider = provider or settings.default_llm
    if provider == "claude":
        return ClaudeClient()
    if provider == "openai":
        return OpenAIClient()
    if provider == "ollama":
        return OllamaClient()
    raise ValueError(f"Unknown LLM provider: {provider}")


def _claude_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    # Haiku: $0.80/$4.00 per M tokens  |  Sonnet: $3/$15 per M
    if "haiku" in model:
        return (input_tokens * 0.0000008) + (output_tokens * 0.000004)
    return (input_tokens * 0.000003) + (output_tokens * 0.000015)


def _openai_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    # gpt-4o-mini: $0.15/$0.60 per M
    return (input_tokens * 0.00000015) + (output_tokens * 0.0000006)
