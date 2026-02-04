from __future__ import annotations

from typing import TypedDict, List, Tuple

from langgraph.graph import StateGraph, END

from app.agents.retriever import retrieve_chunks
from app.agents.analyst import analyze_claim
from app.agents.critic import validate_citations
from app.schemas.models import (
    AnalysisRequest,
    AnalysisResponse,
    DocumentChunk,
    Citation,
)
from app.vectorstores.base import VectorStore


class WorkflowState(TypedDict):
    request: AnalysisRequest
    retrieved: List[Tuple[float, DocumentChunk]]
    decision: str
    rationale: str
    citations: List[Citation]


def _retrieve(state: WorkflowState, store: VectorStore) -> WorkflowState:
    retrieved = retrieve_chunks(store, state["request"])
    return {**state, "retrieved": retrieved}


def _analyze(state: WorkflowState) -> WorkflowState:
    decision, rationale, citations = analyze_claim(state["request"], state["retrieved"])
    return {
        **state,
        "decision": decision,
        "rationale": rationale,
        "citations": citations,
    }


def _critic(state: WorkflowState) -> WorkflowState:
    verified = validate_citations(state["citations"], state["retrieved"])
    return {**state, "citations": verified}


def run_langgraph(store: VectorStore, request: AnalysisRequest) -> AnalysisResponse:
    graph = StateGraph(WorkflowState)

    graph.add_node("retrieve", lambda state: _retrieve(state, store))
    graph.add_node("analyze", _analyze)
    graph.add_node("critic", _critic)

    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "analyze")
    graph.add_edge("analyze", "critic")
    graph.add_edge("critic", END)

    compiled = graph.compile()

    initial_state: WorkflowState = {
        "request": request,
        "retrieved": [],
        "decision": "needs-review",
        "rationale": "",
        "citations": [],
    }

    final_state = compiled.invoke(initial_state)

    return AnalysisResponse(
        decision=final_state["decision"],
        rationale=final_state["rationale"],
        citations=final_state["citations"],
    )
