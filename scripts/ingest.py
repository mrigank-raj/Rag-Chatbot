"""
Ingestion Pipeline Orchestrator — runs the full end-to-end data ingestion process:
1. Scrape HTML pages from Groww (scraper.py)
2. Chunk the text by semantic sections (chunker.py)
3. Embed and store the chunks in ChromaDB (embedder.py)
4. Log the source status to SQLite (metadata.py)
"""

import os
import sys

# Ensure the root directory is in the PYTHONPATH so imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.ingestion.scraper import scrape_all
from src.ingestion.chunker import chunk_all
from src.ingestion.embedder import embed_and_store
from src.utils.metadata import MetadataDB
from src.utils.config import settings


def run_pipeline():
    print("==================================================")
    print(">> Starting HDFC MF Data Ingestion Pipeline")
    print("==================================================\n")

    # Step 1: Scrape
    print("--- [1/4] Scraping Groww Pages ---")
    scrape_results = scrape_all()
    print("Scraping completed.\n")

    # Step 2: Chunk
    print("--- [2/4] Semantic Section Chunking ---")
    chunks = chunk_all()
    print("Chunking completed.\n")

    # Step 3: Embed & Store in ChromaDB
    print("--- [3/4] Generating Embeddings & Storing in ChromaDB ---")
    if not chunks:
        print("[ERROR] No chunks generated. Aborting embedding step.")
    else:
        vectorstore = embed_and_store(chunks)
        print("VectorDB upsert completed.\n")

    # Step 4: Update SQLite Metadata DB
    print("--- [4/4] Updating Metadata Database ---")
    db = MetadataDB(settings.SQLITE_DB_PATH)
    
    # Calculate chunk counts per source URL
    chunk_counts = {}
    for c in chunks:
        url = c["metadata"]["source_url"]
        chunk_counts[url] = chunk_counts.get(url, 0) + 1

    for result in scrape_results:
        url = result["url"]
        scheme_name = result["scheme_name"]
        
        db.add_source(
            url=url,
            scheme_name=scheme_name,
            document_type="groww_page",
            chunk_count=chunk_counts.get(url, 0),
            status=result["status"]
        )
        print(f"  Logged to DB: {scheme_name} (Status: {result['status']})")
        
    print("\nMetadata logging completed.")

    print("\n==================================================")
    print("[OK] Ingestion Pipeline Finished Successfully!")
    print(f"Database Path: {settings.SQLITE_DB_PATH}")
    print(f"Vector Store Path: {settings.CHROMA_PERSIST_DIR}")
    print("==================================================")


if __name__ == "__main__":
    run_pipeline()
