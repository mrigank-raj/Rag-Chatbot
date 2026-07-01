"""
FastAPI route definitions for the RAG assistant.
Handles the /api/chat and /api/health endpoints.
"""

from fastapi import APIRouter, HTTPException

from src.api.models import ChatRequest, ChatResponse, HealthResponse
from src.pipeline.generator import ResponseGenerator
from src.ingestion.embedder import get_vectorstore
from src.utils.metadata import MetadataDB
from src.utils.config import settings

router = APIRouter()

# Initialize the core RAG generator once at startup
# (This loads the LLM client, vectorstore connection, and prompt templates)
try:
    generator = ResponseGenerator()
except Exception as e:
    print(f"[Error] Failed to initialize ResponseGenerator: {e}")
    generator = None


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint.
    Takes a user query, runs it through the RAG pipeline (classify -> retrieve -> generate),
    and returns a structured factual answer with citations.
    """
    if not generator:
        raise HTTPException(status_code=500, detail="RAG Pipeline is not initialized properly.")
    
    try:
        # Run the full pipeline
        result = generator.generate(request.query)
        
        # If the pipeline caught an error internally (e.g. Rate Limit after retries)
        if result.get("error"):
            # Return 503 Service Unavailable so the frontend knows it's a temporary issue
            raise HTTPException(status_code=503, detail=result["error"])
            
        return ChatResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.get("/health", response_model=HealthResponse)
async def health_endpoint():
    """
    Health check endpoint.
    Verifies Vector DB, LLM connection, and lists scraped sources from SQLite.
    """
    chromadb_status = "unhealthy"
    llm_status = "unhealthy"
    
    # Check VectorDB
    try:
        vs = get_vectorstore()
        count = vs._collection.count()
        if count > 0:
            chromadb_status = f"healthy ({count} chunks)"
        else:
            chromadb_status = "empty"
    except Exception as e:
        chromadb_status = f"error: {str(e)}"
        
    # Check LLM (if generator initialized)
    if generator:
        llm_status = "configured"
        
    # Get metadata from SQLite
    sources = []
    try:
        db = MetadataDB(settings.SQLITE_DB_PATH)
        sources = db.get_all_sources()
    except Exception as e:
        print(f"[Error] Failed to fetch SQLite sources: {e}")

    return HealthResponse(
        status="healthy" if chromadb_status.startswith("healthy") else "degraded",
        chromadb_status=chromadb_status,
        llm_status=llm_status,
        sources=sources
    )
