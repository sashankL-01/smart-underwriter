from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str | None = None
    groq_chat_model: str = "llama-3.1-8b-instant"
    embeddings_provider: str = "sentence-transformers"  # hash | sentence-transformers
    embeddings_dim: int = 384
    embeddings_model: str = "all-MiniLM-L6-v2"

    chunk_size: int = 1000
    chunk_overlap: int = 200

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
