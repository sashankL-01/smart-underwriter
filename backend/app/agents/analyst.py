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
        # Include section metadata for context
        section_info = f"Section: {chunk.metadata.section}" if chunk.metadata.section else ""
        context_blocks.append(
            f"""
Source: {chunk.metadata.source_filename}
Page: {chunk.metadata.page_number}
{section_info}
Text: {chunk.text}
""".strip()
        )

    system_prompt = (
        "You are a Senior Insurance Underwriter and Claims Analyst. Your task is to analyze "
        "a claim against the provided policy documents to determine coverage.\n\n"
        "Follow this strict analysis process:\n"
        "1. **Check Exclusions First**: Does any exclusion clause apply? If yes -> Decision: 'excluded', Risk: 'high'.\n"
        "2. **Check Coverage Grants**: Is the claimed item explicitly listed as a benefit? If no -> Decision: 'needs-review', Risk: 'medium'.\n"
        "3. **Check Conditions/Limits**: Are there waiting periods, sub-limits, or co-pays? If yes -> Decision: 'likely-covered', Risk: 'medium' (due to restrictions).\n"
        "4. **Clear Coverage**: If covered with no applicable exclusions/limits -> Decision: 'likely-covered', Risk: 'low'.\n\n"
        "Output Requirements:\n"
        "- **Rationale**: Must be detailed, citing specific policy language. Explain WHY it is covered or excluded.\n"
        "- **Citations**: Extract exact quotes supporting your decision.\n"
        "- **Risk Level**: 'high' (denials/exclusions), 'medium' (limits/ambiguity), 'low' (clear coverage).\n"
        "Return valid JSON only."
    )

    policy_text = "\n\n".join(context_blocks)
    user_prompt = (
        f"Claim Description:\n{request.claim_text}\n\n"
        f"Policy Document Context:\n{policy_text}\n\n"
        "Analyze this claim based on the policy text above. "
        "Provide a JSON response with fields: 'decision', 'rationale', 'citations' (array of objects with quote, page_number, source_filename), and 'risk_level'."
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
    
    # robust json cleanup
    content = content.replace("```json", "").replace("```", "").strip()

    # Find first '{' and last '}' to handle trailing/leading text
    import re
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        content = match.group(0)
    
    try:
        parsed = LLMAnalysisOutput.model_validate_json(content)
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"JSON Parse Error: {e}")
        print(f"Raw Content: {content}")
        return (
            "needs-review",
            f"Model response could not be parsed. Error: {str(e)}",
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
