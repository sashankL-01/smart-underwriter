from __future__ import annotations

import logging

from app.agents.router import route_request
from app.agents.retriever import retrieve_chunks
from app.agents.analyst import analyze_claim
from app.agents.critic import validate_citations
from app.agents.langgraph_flow import run_langgraph
from app.config import settings
from app.schemas.models import AnalysisRequest, AnalysisResponse
from app.vectorstores.base import VectorStore

logger = logging.getLogger(__name__)


def run_workflow(store: VectorStore, request: AnalysisRequest) -> AnalysisResponse:
    workflow = route_request(request)
    logger.debug("Routed workflow=%s policy_id=%s", workflow, request.policy_id)

    if workflow != "policy_analysis":
        logger.warning("Unsupported workflow route=%s", workflow)
        return AnalysisResponse(
            decision="needs-review",
            rationale="Unsupported workflow route.",
            citations=[],
        )

    if settings.use_langgraph:
        logger.info("Running LangGraph workflow")
        return run_langgraph(store, request)

    logger.info("Running standard workflow")
    retrieved = retrieve_chunks(store, request)
    logger.debug("Retrieved %d chunks", len(retrieved))
    decision, rationale, citations, risk_level = analyze_claim(request, retrieved)
    logger.debug(
        "Analysis decision=%s citations=%d risk=%s",
        decision,
        len(citations),
        risk_level,
    )
    verified = validate_citations(citations, retrieved)
    logger.debug("Verified citations=%d", len(verified))

    return AnalysisResponse(
        decision=decision,
        rationale=rationale,
        citations=verified,
        risk_level=risk_level,
    )
