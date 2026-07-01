"""
Utility script to view the vector embeddings and chunks stored in ChromaDB.
Run with: python scripts/view_embeddings.py
"""

import os
import sys

# Ensure the root directory is in the PYTHONPATH so imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.ingestion.embedder import get_vectorstore


def view_embeddings(limit: int = 2):
    print("Connecting to ChromaDB...")
    vectorstore = get_vectorstore()
    
    collection = vectorstore._collection
    count = collection.count()
    print(f"\nTotal chunks in database: {count}")
    
    if count == 0:
        print("Database is empty. Please run scripts/ingest.py first.")
        return

    print(f"\nFetching {limit} sample chunk(s) with embeddings...")
    # By default, collection.get() does not return embeddings. We must specify it.
    results = collection.get(
        limit=limit,
        include=["documents", "metadatas", "embeddings"]
    )
    
    for i in range(len(results["ids"])):
        doc_id = results["ids"][i]
        text = results["documents"][i]
        meta = results["metadatas"][i]
        embedding = results["embeddings"][i]
        
        print("\n" + "="*50)
        print(f"CHUNK ID: {doc_id}")
        print(f"SCHEME:   {meta.get('scheme_name')} (Section: {meta.get('section')})")
        print("-" * 50)
        print(f"TEXT:\n{text[:200]}...") # truncate text for readability
        print("-" * 50)
        print(f"EMBEDDING (Vector dimensions: {len(embedding)}):")
        
        # Print the first 5 and last 5 dimensions to show what the vector looks like
        preview = [round(val, 4) for val in embedding[:5]] + ["..."] + [round(val, 4) for val in embedding[-5:]]
        print(f"{preview}")
        print("="*50)


if __name__ == "__main__":
    view_embeddings()
