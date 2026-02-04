# Smart Underwriter

Monorepo with a FastAPI backend and React (Vite + TypeScript) frontend.

## Structure
- backend: Ingestion pipeline, vector store, agent orchestration
- frontend: React dashboard with side-by-side policy PDF viewer and AI insights

## Backend setup
1. Create a virtual environment and install dependencies from backend/requirements.txt.
2. Start the API server with uvicorn app.main:app --reload from the backend folder.

## Frontend setup
1. Install dependencies with npm install from the frontend folder.
2. Run npm run dev and open http://localhost:5173.

## API
- POST /ingest?policy_id=policy-001 (multipart file upload)
- POST /analyze (JSON: { policy_id, claim_text })

## Notes
- Configure vector storage via environment variables:
	- VECTOR_STORE=memory|chroma|pinecone
	- CHROMA_PERSIST_DIR, CHROMA_COLLECTION
	- PINECONE_API_KEY, PINECONE_INDEX
- To enable LangGraph orchestration, set USE_LANGGRAPH=true.
- LLM configuration uses Groq: set GROQ_API_KEY and optionally GROQ_CHAT_MODEL.
- Citations-first responses include page number and source filename metadata.
