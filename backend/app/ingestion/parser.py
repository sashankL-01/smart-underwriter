from __future__ import annotations

from typing import List, Optional, Tuple, Generator
import os
import re
import fitz  # PyMuPDF

from app.schemas.models import ChunkMetadata, DocumentChunk
from app.config import settings


def _recursive_split(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    Split text recursively by separators to respect semantic boundaries.
    Separators: double newline (paragraph), single newline, sentence end, space.
    """
    if len(text) <= chunk_size:
        return [text]
        
    separators = ["\n\n", "\n", ". ", " ", ""]
    
    for sep in separators:
        splits = text.split(sep)
        if len(splits) > 1:
            chunks = []
            current_chunk = []
            current_len = 0
            
            for split in splits:
                split_len = len(split) + len(sep)
                if current_len + split_len > chunk_size and current_chunk:
                    chunks.append(sep.join(current_chunk))
                    current_chunk = []
                    current_len = 0
                
                current_chunk.append(split)
                current_len += split_len
            
            if current_chunk:
                chunks.append(sep.join(current_chunk))
            
            # If splitting by this separator worked (produced valid chunks), recurse on large chunks
            final_chunks = []
            for chunk in chunks:
                if len(chunk) > chunk_size:
                    final_chunks.extend(_recursive_split(chunk, chunk_size, overlap))
                else:
                    final_chunks.append(chunk)
            return final_chunks
            
    # If no separator works, hard split
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size-overlap)]

def _detect_section(text: str, font_size: float, current_section: str) -> str:
    """Detect if a text block is likely a section header based on properties."""
    # Simple heuristic: Short lines, uppercase or title case, large font (optional check)
    clean_text = text.strip()
    if not clean_text:
        return current_section
        
    # Heuristic for section headers in insurance policies
    is_header = False
    
    # All caps headers: "DEFINITIONS", "EXCLUSIONS"
    if clean_text.isupper() and len(clean_text) < 50 and len(clean_text) > 3:
        is_header = True
    
    # Title case headers with specific keywords
    keywords = ["Section", "Part", "Chapter", "Article", "Coverage", "Exclusion", "Definition", "Benefit", "Condition"]
    if any(k in clean_text for k in keywords) and len(clean_text) < 60:
        is_header = True
        
    return clean_text if is_header else current_section

def parse_pdf(
    file_path: str,
    policy_id: str,
    jurisdiction: str | None = None,
    claim_type: str | None = None,
) -> Generator[DocumentChunk, None, None]:
    """
    Parse a PDF file from disk and yield DocumentChunk objects one by one.
    This avoids loading the entire PDF and all chunks into memory at once.
    """
    doc = fitz.open(file_path)
    
    current_section = "General"
    
    # improved text extraction with layout analysis
    for page_index in range(len(doc)):
        page = doc[page_index]
        blocks = page.get_text("dict")["blocks"]
        page_text = ""
        
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"]
                        size = span["size"]
                        
                        # Update section context
                        current_section = _detect_section(text, size, current_section)
                        page_text += text + " "
                        
        # Split the text of this page
        raw_chunks = _recursive_split(page_text, settings.chunk_size, settings.chunk_overlap)
        
        for chunk_text in raw_chunks:
            if len(chunk_text.strip()) < 50:  # Skip very small chunks
                continue
                
            metadata = ChunkMetadata(
                page_number=page_index + 1,
                source_filename=os.path.basename(file_path),
                policy_id=policy_id,
                section=current_section,
                content_type="policy_text",
                jurisdiction=jurisdiction,
                claim_type=claim_type,
            )
            yield DocumentChunk(text=chunk_text.strip(), metadata=metadata)
            
    doc.close()
