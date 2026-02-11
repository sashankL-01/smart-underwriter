from __future__ import annotations

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    page_number: int
    source_filename: str
    policy_id: str
    section: Optional[str] = None
    content_type: Optional[str] = None
    keywords: Optional[List[str]] = None
    jurisdiction: Optional[str] = None
    claim_type: Optional[str] = None


class DocumentChunk(BaseModel):
    text: str
    metadata: ChunkMetadata


class Citation(BaseModel):
    quote: str
    page_number: int
    source_filename: str
    policy_id: str = ""
    text: str = ""


class AnalysisRequest(BaseModel):
    policy_id: str = Field(..., description="Policy identifier used during ingestion")
    claim_text: str
    jurisdiction: Optional[str] = None
    claim_type: Optional[str] = None


class AnalysisResponse(BaseModel):
    decision: str
    rationale: str
    citations: List[Citation]
    risk_level: str = "medium"  # low | medium | high


class LLMAnalysisOutput(BaseModel):
    decision: Literal["likely-covered", "excluded", "needs-review"]
    rationale: str
    citations: List[Citation]
    risk_level: Literal["low", "medium", "high"] = "medium"


class LLMCriticOutput(BaseModel):
    keep_indices: List[int]


class IngestResponse(BaseModel):
    policy_id: str
    chunks_indexed: int


class PolicySummary(BaseModel):
    policy_id: str
    source_filename: str | None = None
    jurisdiction: Optional[str] = None
    claim_type: Optional[str] = None
    chunks_indexed: int = 0
