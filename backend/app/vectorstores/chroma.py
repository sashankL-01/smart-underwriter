from __future__ import annotations

from typing import Dict, List, Optional, Tuple
import uuid

import chromadb

from app.config import settings
from app.schemas.models import ChunkMetadata, DocumentChunk
from app.vectorstores.base import VectorStore


class ChromaVectorStore(VectorStore):
    def __init__(self) -> None:
        client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        self._collection = client.get_or_create_collection(settings.chroma_collection)

    def add(self, embeddings: List[List[float]], chunks: List[DocumentChunk]) -> None:
        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [chunk.metadata.model_dump() for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def query(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        metadata_filter: Optional[Dict[str, str]] = None,
    ) -> List[Tuple[float, DocumentChunk]]:
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=metadata_filter or {},
            include=["documents", "metadatas", "distances"],
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        scored: List[Tuple[float, DocumentChunk]] = []
        for text, metadata, distance in zip(documents, metadatas, distances):
            chunk = DocumentChunk(
                text=text,
                metadata=ChunkMetadata(**metadata),
            )
            score = 1.0 - float(distance)
            scored.append((score, chunk))

        return scored
