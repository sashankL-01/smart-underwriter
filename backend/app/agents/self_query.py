from __future__ import annotations

from typing import Dict

from app.schemas.models import AnalysisRequest


def build_metadata_filter(request: AnalysisRequest) -> Dict[str, str]:
    metadata_filter: Dict[str, str] = {}

    # Optional: filter by jurisdiction or claim_type if specified
    if request.jurisdiction:
        metadata_filter["jurisdiction"] = request.jurisdiction
    if request.claim_type:
        metadata_filter["claim_type"] = request.claim_type

    return metadata_filter
