from __future__ import annotations

from groq import Groq

from app.config import settings


def llm_enabled() -> bool:
    return bool(settings.groq_api_key)


def get_client() -> Groq:
    if not settings.groq_api_key:
        raise ValueError("Groq API key is not configured")
    return Groq(api_key=settings.groq_api_key)
