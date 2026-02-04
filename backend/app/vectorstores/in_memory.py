from __future__ import annotations

from typing import Dict, List, Optional, Tuple
import math

from app.schemas.models import DocumentChunk
from app.vectorstores.base import VectorStore


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _match_metadata(
    chunk: DocumentChunk, metadata_filter: Optional[Dict[str, str]]
) -> bool:
    if not metadata_filter:
        return True
    for key, value in metadata_filter.items():
        if getattr(chunk.metadata, key, None) != value:
            return False
    return True


class InMemoryVectorStore(VectorStore):
    def __init__(self) -> None:
        self._rows: List[Tuple[List[float], DocumentChunk]] = []

    def add(self, embeddings: List[List[float]], chunks: List[DocumentChunk]) -> None:
        for embedding, chunk in zip(embeddings, chunks):
            self._rows.append((embedding, chunk))

    def query(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        metadata_filter: Optional[Dict[str, str]] = None,
    ) -> List[Tuple[float, DocumentChunk]]:
        scored: List[Tuple[float, DocumentChunk]] = []
        for embedding, chunk in self._rows:
            if not _match_metadata(chunk, metadata_filter):
                continue
            score = _cosine_similarity(query_embedding, embedding)
            scored.append((score, chunk))
        scored.sort(key=lambda item: item[0], reverse=True)
        return scored[:top_k]
