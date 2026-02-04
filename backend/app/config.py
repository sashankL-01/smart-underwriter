from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str | None = None
    groq_chat_model: str = "llama-3.1-8b-instant"
    embeddings_provider: str = "hash"  # hash | sentence-transformers
    embeddings_dim: int = 8

    vector_store: str = "pinecone"
    chroma_persist_dir: str = "./chroma"
    chroma_collection: str = "smart-underwriter"

    pinecone_api_key: str | None = None
    pinecone_index: str | None = None
    pinecone_env: str | None = None

    use_langgraph: bool = False

    class Config:
        env_file = (".env", "../.env")
        extra = "ignore"


settings = Settings()
