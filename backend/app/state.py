from __future__ import annotations

from typing import Dict

from app.schemas.models import PolicySummary

from app.config import settings
from app.vectorstores.in_memory import InMemoryVectorStore
from app.vectorstores.chroma import ChromaVectorStore
from app.vectorstores.pinecone import PineconeVectorStore
from app.vectorstores.base import VectorStore


# Single global vector store for all policies
_GLOBAL_STORE: VectorStore | None = None
POLICY_REGISTRY: Dict[str, PolicySummary] = {}


def _build_store() -> VectorStore:
    match settings.vector_store:
        case "chroma":
            return ChromaVectorStore()
        case "pinecone":
            return PineconeVectorStore(namespace=None)
        case _:
            return InMemoryVectorStore()


def get_global_store() -> VectorStore:
    global _GLOBAL_STORE
    if _GLOBAL_STORE is None:
        _GLOBAL_STORE = _build_store()
    return _GLOBAL_STORE


def register_policy(summary: PolicySummary) -> None:
    POLICY_REGISTRY[summary.policy_id] = summary


def list_policies() -> list[PolicySummary]:
    return list(POLICY_REGISTRY.values())


def get_policy(policy_id: str) -> PolicySummary | None:
    return POLICY_REGISTRY.get(policy_id)
