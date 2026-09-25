"""
Configuration module — loads environment variables from .env and exposes
them as a centralized Settings object for the rest of the application.
"""

import os
import shutil
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv()

# Vercel's filesystem is read-only except /tmp: copy the vectorstore and metadata DB
# there on cold start and point the settings below at the copies.
if os.getenv("VERCEL"):
    _root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if not os.path.exists("/tmp/vectorstore"):
        shutil.copytree(os.path.join(_root, "vectorstore"), "/tmp/vectorstore")
        os.makedirs("/tmp/db", exist_ok=True)
        shutil.copy(os.path.join(_root, "db", "metadata.db"), "/tmp/db/metadata.db")
    os.environ["CHROMA_PERSIST_DIR"] = "/tmp/vectorstore"
    os.environ["SQLITE_DB_PATH"] = "/tmp/db/metadata.db"
    os.environ.setdefault("FASTEMBED_CACHE_PATH", "/tmp/fastembed")
    os.environ.setdefault("HF_HOME", "/tmp/hf")  # hf-xet writes logs under HF_HOME; $HOME is read-only


class Settings:
    """Centralized application settings loaded from environment variables."""

    # --- LLM Provider ---
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

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
