from __future__ import annotations

from app.schemas.models import AnalysisRequest


def route_request(request: AnalysisRequest) -> str:
    """
    Decide which workflow to use.
    For now, all requests go to policy analysis.
    """
    return "policy_analysis"
