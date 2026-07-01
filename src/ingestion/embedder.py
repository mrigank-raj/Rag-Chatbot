"""
Embedder module — takes text chunks, generates vector embeddings using the
BGE-small model, and stores them persistently in ChromaDB.
"""

import os
from typing import List

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

from src.utils.config import settings


def get_embedding_model() -> HuggingFaceEmbeddings:
    """
    Initialize and return the HuggingFace embeddings model.
    Downloads the model weights on first run.
    """
    # Use BGE-small as configured in settings (BAAI/bge-small-en-v1.5)
    model_kwargs = {'device': 'cpu'}
    encode_kwargs = {'normalize_embeddings': True} # BGE models perform best with normalized embeddings (Cosine Similarity)
    
    print(f"Loading embedding model: {settings.EMBEDDING_MODEL}...")
    embeddings = HuggingFaceEmbeddings(
        model_name=settings.EMBEDDING_MODEL,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )
    return embeddings


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
