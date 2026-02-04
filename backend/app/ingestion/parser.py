from __future__ import annotations

from typing import List
import fitz  # PyMuPDF

from app.schemas.models import ChunkMetadata, DocumentChunk


def _chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    if not text:
        return []
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start = max(end - overlap, end)
    return chunks


def parse_pdf(
    file_bytes: bytes,
    filename: str,
    policy_id: str,
    jurisdiction: str | None = None,
    claim_type: str | None = None,
) -> List[DocumentChunk]:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    chunks: List[DocumentChunk] = []

    for page_index in range(len(doc)):
        page = doc[page_index]
        text = page.get_text("text")
        for chunk in _chunk_text(text):
            metadata = ChunkMetadata(
                page_number=page_index + 1,
                source_filename=filename,
                policy_id=policy_id,
                jurisdiction=jurisdiction,
                claim_type=claim_type,
            )
            chunks.append(DocumentChunk(text=chunk, metadata=metadata))

    return chunks
