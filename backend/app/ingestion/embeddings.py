from __future__ import annotations

from typing import List
import hashlib

from app.config import settings


def _hash_to_vector(text: str, dim: int = 8) -> List[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values = [b for b in digest[:dim]]
    return [v / 255.0 for v in values]


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Embedding implementation.
    Uses deterministic hash vectors by default.
    """
    dim = max(1, int(settings.embeddings_dim))
    return [_hash_to_vector(text, dim=dim) for text in texts]
