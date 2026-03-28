from __future__ import annotations

from typing import List, Tuple

from app.ingestion.embeddings import embed_texts
from app.schemas.models import AnalysisRequest, DocumentChunk
from app.vectorstores.base import VectorStore
from app.agents.self_query import build_metadata_filter


def retrieve_chunks(
    store: VectorStore,
    request: AnalysisRequest,
    top_k: int = 5,
) -> List[Tuple[float, DocumentChunk]]:
    query_embedding = embed_texts([request.claim_text])[0]

    metadata_filter = build_metadata_filter(request)

    return store.query(query_embedding, top_k=top_k, metadata_filter=metadata_filter)
