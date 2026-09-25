"""
Embedder module — takes text chunks, generates vector embeddings using the
BGE-small model, and stores them persistently in ChromaDB.
"""

import os
from functools import lru_cache
from typing import List

from fastembed import TextEmbedding
from langchain_community.vectorstores import Chroma
from langchain_core.embeddings import Embeddings

from src.utils.config import settings


class FastEmbedder(Embeddings):
    """
    BGE-small via fastembed (ONNX). Same model and vectors as sentence-transformers
    (normalized), but ~250 MB of RAM instead of ~1 GB with PyTorch.
    """

    def __init__(self, model_name: str):
        self.model = TextEmbedding(model_name=model_name, cache_dir=os.getenv("FASTEMBED_CACHE_PATH"))

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [v.tolist() for v in self.model.embed(texts)]

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]


@lru_cache(maxsize=1)
def get_embedding_model() -> FastEmbedder:
    """Return the shared embedding model (loaded once; downloads weights on first run)."""
    print(f"Loading embedding model: {settings.EMBEDDING_MODEL}...")
    return FastEmbedder(settings.EMBEDDING_MODEL)


def get_vectorstore() -> Chroma:
    """
    Initialize and return the ChromaDB client pointing to the persistent directory.
    """
    embeddings = get_embedding_model()
    
    # Ensure the persist directory exists
    os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
    
    vectorstore = Chroma(
        collection_name=settings.CHROMA_COLLECTION,
        embedding_function=embeddings,
        persist_directory=settings.CHROMA_PERSIST_DIR
    )
    return vectorstore


def embed_and_store(chunks: List[dict]) -> Chroma:
    """
    Takes a list of chunk dictionaries (with 'text' and 'metadata' keys),
    embeds them, and upserts them into ChromaDB.
    
    Returns the initialized ChromaDB vectorstore.
    """
    if not chunks:
        print("No chunks provided to embed_and_store.")
        return None
        
    vectorstore = get_vectorstore()
    
    texts = [chunk["text"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]
    
    # Generate stable IDs for upsertion (prevents duplicates if run multiple times)
    # Format: {scheme_name_slug}_section_{chunk_index}
    ids = []
    for meta in metadatas:
        import re
        slug = re.sub(r"[^a-z0-9]+", "-", meta["scheme_name"].lower()).strip("-")
        chunk_id = f"{slug}_{meta['section']}_{meta['chunk_index']}"
        ids.append(chunk_id)

    print(f"Embedding and upserting {len(texts)} chunks into ChromaDB...")
    
    # Add texts to Chroma. This will automatically compute embeddings and persist.
    vectorstore.add_texts(
        texts=texts,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"Successfully stored {len(texts)} chunks in {settings.CHROMA_PERSIST_DIR}")
    return vectorstore


# ---------------------------------------------------------------------------
# Quick Test (when run directly)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Test initialization
    print("Testing VectorStore connection...")
    vs = get_vectorstore()
    print(f"Current chunk count in DB: {vs._collection.count()}")
