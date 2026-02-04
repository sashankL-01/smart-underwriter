from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from app.schemas.models import DocumentChunk


class VectorStore:
    def add(self, embeddings: List[List[float]], chunks: List[DocumentChunk]) -> None:
        raise NotImplementedError

    def query(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        metadata_filter: Optional[Dict[str, str]] = None,
    ) -> List[Tuple[float, DocumentChunk]]:
        raise NotImplementedError
