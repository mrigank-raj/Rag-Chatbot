"""
Pydantic data models for the FastAPI layer.
Enforces request validation and structured responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ChatRequest(BaseModel):
    """Incoming user query."""
    query: str = Field(..., min_length=3, max_length=500, description="The user's question about HDFC mutual funds.")


class ChatResponse(BaseModel):
    """Structured response from the RAG pipeline."""
    answer: str = Field(..., description="The factual answer, or standard refusal for advisory/OOS queries.")
    citation: Optional[str] = Field(None, description="URL of the source Groww page if applicable.")
    last_updated: Optional[str] = Field(None, description="Date the source data was scraped.")
    query_type: str = Field(..., description="Classification of the query: FACTUAL, ADVISORY, or OUT_OF_SCOPE.")
    error: Optional[str] = Field(None, description="Error message if the LLM/Retriever failed.")


class HealthResponse(BaseModel):
    """API health status and system metadata."""
    status: str = Field(..., description="'healthy' if system is running properly.")
    chromadb_status: str = Field(..., description="Status of vector database.")
    llm_status: str = Field(..., description="Status of LLM connection.")
    sources: List[Dict[str, Any]] = Field(..., description="List of configured schemes and their scraping status.")
