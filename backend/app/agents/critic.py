from __future__ import annotations

from typing import List, Tuple
import json

from pydantic import ValidationError

from app.schemas.models import Citation, DocumentChunk, LLMCriticOutput
from app.llm import get_client, llm_enabled
from app.config import settings


def validate_citations(
    citations: List[Citation],
    retrieved: List[Tuple[float, DocumentChunk]] | None = None,
) -> List[Citation]:
    """
    Ensure every citation has page and filename metadata and is supported
    by retrieved context when LLM is available.
    """
    filtered = [c for c in citations if c.page_number and c.source_filename]
    if not filtered or not llm_enabled() or not retrieved:
        return filtered

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
        "You are a strict auditor. Keep only citations that are directly supported "
        "by the provided policy text. Return JSON only."
    )

    citations_payload = [
        {
            "index": index,
            "quote": citation.quote,
            "page_number": citation.page_number,
            "source_filename": citation.source_filename,
        }
        for index, citation in enumerate(filtered)
    ]

    policy_text = "\n\n".join(context_blocks)
    user_prompt = (
        "Policy excerpts:\n"
        f"{policy_text}\n\n"
        "Citations:\n"
        f"{json.dumps(citations_payload)}\n\n"
        "Return JSON with field keep_indices as an array of citation indices to keep."
    )

    client = get_client()
    response = client.chat.completions.create(
        model=settings.groq_chat_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
    )

    content = response.choices[0].message.content or "{}"
    try:
        parsed = LLMCriticOutput.model_validate_json(content)
        keep_indices = set(int(i) for i in parsed.keep_indices)
    except (json.JSONDecodeError, TypeError, ValueError, ValidationError):
        return filtered

    return [c for index, c in enumerate(filtered) if index in keep_indices]
