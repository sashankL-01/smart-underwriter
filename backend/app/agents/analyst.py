from __future__ import annotations

from typing import List, Tuple
import json

from pydantic import ValidationError

from app.schemas.models import (
    AnalysisRequest,
    Citation,
    DocumentChunk,
    LLMAnalysisOutput,
)
from app.llm import get_client, llm_enabled
from app.config import settings


def analyze_claim(
    request: AnalysisRequest,
    retrieved: List[Tuple[float, DocumentChunk]],
) -> tuple[str, str, List[Citation], str]:
    if not retrieved:
        return (
            "needs-review",
            "No relevant clauses were retrieved. Manual review required.",
            [],
            "high",
        )

    if not llm_enabled():
        citations: List[Citation] = []
        for _, chunk in retrieved:
            citations.append(
                Citation(
                    quote=chunk.text[:240],
                    page_number=chunk.metadata.page_number,
                    source_filename=chunk.metadata.source_filename,
                    policy_id=chunk.metadata.policy_id,
                    text=chunk.text,
                )
            )

        rationale = (
            "Retrieved relevant policy clauses and matched them against the claim. "
            "Review the cited sections to confirm coverage and exclusions."
        )

        return "likely-covered", rationale, citations, "medium"

    context_blocks = []
    for _, chunk in retrieved:
        context_blocks.append(
            """
Source: {source}
Page: {page}
Text: {text}
""".strip().format(
                source=chunk.metadata.source_filename,
                page=chunk.metadata.page_number,
                text=chunk.text,
            )
        )

    system_prompt = (
        "You are an insurance policy analyst. Use only the provided policy text to "
        "evaluate the claim. Provide citations with page numbers and filenames. "
        "Assess risk level: low (clear coverage), medium (ambiguous), high (likely excluded or missing coverage). "
        "Return JSON only."
    )

    policy_text = "\n\n".join(context_blocks)
    user_prompt = (
        "Claim:\n"
        f"{request.claim_text}\n\n"
        "Policy excerpts:\n"
        f"{policy_text}\n\n"
        "Decide if the claim is likely-covered, excluded, or needs-review. "
        "Return JSON with fields: decision, rationale, citations, risk_level. "
        "citations is an array of {quote, page_number, source_filename}. "
        "risk_level must be: low, medium, or high."
    )

    client = get_client()
    response = client.chat.completions.create(
        model=settings.groq_chat_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    content = response.choices[0].message.content or "{}"
    try:
        parsed = LLMAnalysisOutput.model_validate_json(content)
    except (json.JSONDecodeError, ValidationError):
        return (
            "needs-review",
            "Model response could not be parsed. Manual review required.",
            [],
            "high",
        )

    citations = [
        Citation(
            quote=citation.quote[:400],
            page_number=citation.page_number,
            source_filename=citation.source_filename,
            policy_id=(
                retrieved[i][1].metadata.policy_id if i < len(retrieved) else "unknown"
            ),
            text=retrieved[i][1].text if i < len(retrieved) else citation.quote,
        )
        for i, citation in enumerate(parsed.citations)
    ]

    return parsed.decision, parsed.rationale, citations, parsed.risk_level
