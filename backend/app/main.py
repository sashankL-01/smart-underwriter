from __future__ import annotations

import logging

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.ingestion.parser import parse_pdf
from app.ingestion.embeddings import embed_texts
from app.schemas.models import (
    AnalysisRequest,
    AnalysisResponse,
    IngestResponse,
    PolicySummary,
)
from app.agents.orchestrator import run_workflow
from app.state import get_global_store, register_policy, list_policies, get_policy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Smart Underwriter")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/ingest", response_model=IngestResponse)
async def ingest_policy(
    policy_id: str,
    file: UploadFile = File(...),
    jurisdiction: str | None = None,
    claim_type: str | None = None,
) -> IngestResponse:
    logger.info(
        "Ingest request policy_id=%s filename=%s jurisdiction=%s claim_type=%s",
        policy_id,
        file.filename,
        jurisdiction,
        claim_type,
    )
    file_bytes = await file.read()
    chunks = parse_pdf(file_bytes, file.filename, policy_id, jurisdiction, claim_type)
    logger.debug("Parsed %d chunks from PDF", len(chunks))
    embeddings = embed_texts([chunk.text for chunk in chunks])
    logger.debug("Generated %d embeddings", len(embeddings))

    store = get_global_store()
    store.add(embeddings, chunks)
    logger.info("Stored %d chunks for policy_id=%s", len(chunks), policy_id)

    register_policy(
        PolicySummary(
            policy_id=policy_id,
            source_filename=file.filename,
            jurisdiction=jurisdiction,
            claim_type=claim_type,
            chunks_indexed=len(chunks),
        )
    )

    return IngestResponse(policy_id=policy_id, chunks_indexed=len(chunks))


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_claim(request: AnalysisRequest) -> AnalysisResponse:
    logger.info(
        "Analyze request policy_id=%s jurisdiction=%s claim_type=%s",
        request.policy_id,
        request.jurisdiction,
        request.claim_type,
    )
    store = get_global_store()
    response = run_workflow(store, request)
    logger.info(
        "Analyze response decision=%s citations=%d",
        response.decision,
        len(response.citations),
    )
    return response


@app.get("/policies", response_model=list[PolicySummary])
async def policies() -> list[PolicySummary]:
    return list_policies()


@app.get("/policies/{policy_id}", response_model=PolicySummary)
async def policy_detail(policy_id: str) -> PolicySummary:
    summary = get_policy(policy_id)
    if not summary:
        return PolicySummary(policy_id=policy_id, chunks_indexed=0)
    return summary
