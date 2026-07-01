"""
Configuration module — loads environment variables from .env and exposes
them as a centralized Settings object for the rest of the application.
"""

import os
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv()


class Settings:
    """Centralized application settings loaded from environment variables."""

    # --- LLM Provider ---
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # --- Embedding ---
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

    # --- ChromaDB ---
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./vectorstore")
    CHROMA_COLLECTION: str = os.getenv("CHROMA_COLLECTION", "hdfc_mf_chunks")

    # --- SQLite ---
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "./db/metadata.db")

    # --- URLs ---
    URLS_JSON_PATH: str = os.getenv("URLS_JSON_PATH", "./data/urls.json")


# Singleton instance for easy import across modules
settings = Settings()
