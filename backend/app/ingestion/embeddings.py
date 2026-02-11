from __future__ import annotations

from typing import List
import hashlib
import logging
from functools import lru_cache

from app.config import settings

logger = logging.getLogger(__name__)

# Global model variable
_model = None

def get_model():
    """Lazy load the sentence transformer model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {settings.embeddings_model}")
            _model = SentenceTransformer(settings.embeddings_model)
        except ImportError:
            logger.error("sentence-transformers not installed. Please install it with: pip install sentence-transformers")
            raise
    return _model

def _hash_to_vector(text: str, dim: int = 8) -> List[float]:
    """Legacy hash-based embeddings for testing."""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    # Repeat the digest to fill dimensions if needed
    extended_digest = digest * (dim // len(digest) + 1)
    values = [b for b in extended_digest[:dim]]
    return [v / 255.0 for v in values]

def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts.
    Supports 'sentence-transformers' (semantic) and 'hash' (deterministic/random).
    """
    if settings.embeddings_provider == "sentence-transformers":
        model = get_model()
        embeddings = model.encode(texts)
        # Convert numpy arrays to lists
        return [e.tolist() for e in embeddings]
    
    # Fallback/Legacy hash embeddings
    dim = max(1, int(settings.embeddings_dim))
    return [_hash_to_vector(text, dim=dim) for text in texts]
