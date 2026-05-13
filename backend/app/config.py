from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    openai_api_key: str
    database_url: str

    # LLM config
    default_llm: str = "claude"           # claude | openai | ollama
    fast_model: str = "claude-haiku-4-5-20251001"
    smart_model: str = "claude-sonnet-4-6"
    embedding_model: str = "text-embedding-3-small"

    # RAG config
    chunk_size: int = 512
    chunk_overlap: int = 64
    retrieval_k: int = 5

    class Config:
        env_file = ".env"


settings = Settings()
