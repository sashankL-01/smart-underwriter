from __future__ import annotations

from typing import Dict, List, Optional, Tuple
import uuid
import logging

from pinecone import Pinecone

from app.config import settings
from app.schemas.models import ChunkMetadata, DocumentChunk
from app.vectorstores.base import VectorStore

logger = logging.getLogger(__name__)


class PineconeVectorStore(VectorStore):
    def __init__(self, namespace: str | None = None) -> None:
        if not settings.pinecone_api_key or not settings.pinecone_index:
            raise ValueError("Pinecone is not configured")

        client = Pinecone(api_key=settings.pinecone_api_key)
        self._index = client.Index(settings.pinecone_index)
        self._namespace = namespace

    def add(self, embeddings: List[List[float]], chunks: List[DocumentChunk]) -> None:
        vectors = []
        for embedding, chunk in zip(embeddings, chunks):
            # Filter out None values from metadata (Pinecone doesn't accept nulls)
            metadata = {
                k: v for k, v in chunk.metadata.model_dump().items() if v is not None
            }
            metadata["text"] = chunk.text

            vectors.append(
                (
                    str(uuid.uuid4()),
                    embedding,
                    metadata,
                )
            )
        logger.info(
            "Upserting %d vectors to Pinecone (namespace=%s)",
            len(vectors),
            self._namespace,
        )
        if self._namespace:
            self._index.upsert(vectors=vectors, namespace=self._namespace)
        else:
            self._index.upsert(vectors=vectors)
        logger.info("Successfully upserted %d vectors to Pinecone", len(vectors))

    def query(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        metadata_filter: Optional[Dict[str, str]] = None,
    ) -> List[Tuple[float, DocumentChunk]]:
        response = self._index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=metadata_filter or {},
            namespace=self._namespace,
        )

        scored: List[Tuple[float, DocumentChunk]] = []
        for match in response.matches:
            metadata = match.metadata or {}
            chunk = DocumentChunk(
                text=metadata.get("text", ""),
                metadata=ChunkMetadata(
                    page_number=int(metadata.get("page_number", 0)),
                    source_filename=str(metadata.get("source_filename", "")),
                    policy_id=str(metadata.get("policy_id", "")),
                    section=metadata.get("section"),
                ),
            )
            scored.append((float(match.score), chunk))

        return scored
