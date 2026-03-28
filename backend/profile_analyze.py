import time
import asyncio
import os

from app.state import get_global_store
from app.agents.retriever import retrieve_chunks
from app.agents.analyst import analyze_claim
from app.agents.critic import validate_citations
from app.schemas.models import AnalysisRequest
from app.ingestion.embeddings import get_model, embed_texts

def profile():
    print("Warming up embedder...")
    tw0 = time.time()
    get_model()
    embed_texts(["warmup"])
    print(f"Warmup took {time.time() - tw0:.2f}s")

    print("\nInitializing store...")
    t0 = time.time()
    store = get_global_store()
    print(f"Store initialized in {time.time() - t0:.2f}s")

    request = AnalysisRequest(policy_id="TATHLIP21255V022021", claim_text="I was admitted to the hospital for 3 days due to acute pneumonia.")
    
    print("\nRetrieving chunks...")
    t1 = time.time()
    retrieved = retrieve_chunks(store, request)
    print(f"Retrieved {len(retrieved)} chunks in {time.time() - t1:.2f}s")
    
    print("\nAnalyzing claim (1st LLM call)...")
    t2 = time.time()
    decision, rationale, citations, risk = analyze_claim(request, retrieved)
    print(f"Decision: {decision}")
    print(f"Analyzed claim in {time.time() - t2:.2f}s")
    
    print("\nValidating citations (2nd LLM call)...")
    t3 = time.time()
    verified = validate_citations(citations, retrieved)
    print(f"Validated citations in {time.time() - t3:.2f}s")
    
    print(f"\nTotal analysis time (minus warmup): {time.time() - t0:.2f}s")

if __name__ == "__main__":
    profile()
