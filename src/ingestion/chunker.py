"""
Section-Aware Text Chunker — splits scraped Groww fund pages into semantically
meaningful chunks by detecting logical section boundaries before applying
character-level splitting within oversized sections.
"""

import os
import json
import re
from datetime import datetime, timezone

from langchain.text_splitter import RecursiveCharacterTextSplitter


# ---------------------------------------------------------------------------
# Section headers detected in Groww pages (order matters — matched top-down)
# ---------------------------------------------------------------------------
SECTION_HEADERS = [
    "Return calculator",
    "Holdings (",
    "Min. for 1st investment",
    "Returns and rankings",
    "Exit load, stamp duty and tax",
    "Compare similar funds",
    "Fund management",
    "About",
    "Fund house",
]

# Map section headers to clean section labels for metadata
SECTION_LABELS = {
    "Return calculator": "return_calculator",
    "Holdings (": "holdings",
    "Min. for 1st investment": "investment_minimums",
    "Returns and rankings": "returns_rankings",
    "Exit load, stamp duty and tax": "exit_load_tax",
    "Compare similar funds": "compare_funds",
    "Fund management": "fund_management",
    "About": "about",
    "Fund house": "fund_house",
}

# Max chunk size in characters — sections under this limit stay as one chunk
MAX_CHUNK_SIZE = 800

# Overlap for fallback splitting of oversized sections
CHUNK_OVERLAP = 50

# Fallback splitter for oversized sections (e.g., Holdings with 40+ stocks)
_fallback_splitter = RecursiveCharacterTextSplitter(
    chunk_size=MAX_CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " "],
    length_function=len,
)


def _detect_sections(text: str) -> list[dict]:
    """
    Split text into logical sections by detecting header keywords.

    Returns a list of dicts: [{"label": str, "content": str}, ...]
    The first section (before any header match) is labeled "fund_overview".
    """
    lines = text.splitlines()
    sections = []
    current_label = "fund_overview"
    current_lines = []

    for line in lines:
        stripped = line.strip()

        # Check if this line matches a section header
        matched_header = None
        for header in SECTION_HEADERS:
            if stripped.startswith(header):
                matched_header = header
                break

        if matched_header:
            # Save the previous section
            if current_lines:
                content = "\n".join(current_lines).strip()
                if content:
                    sections.append({
                        "label": current_label,
                        "content": content,
                    })

            # Start a new section
            current_label = SECTION_LABELS.get(matched_header, "other")
            current_lines = [stripped]
        else:
            current_lines.append(stripped)

    # Don't forget the last section
    if current_lines:
        content = "\n".join(current_lines).strip()
        if content:
            sections.append({
                "label": current_label,
                "content": content,
            })

    return sections


def _split_section(section_content: str, max_size: int = MAX_CHUNK_SIZE) -> list[str]:
    """
    If a section exceeds max_size, split it using RecursiveCharacterTextSplitter.
    Otherwise return it as a single chunk.
    """
    if len(section_content) <= max_size:
        return [section_content]

    # Use LangChain's splitter for oversized sections
    return _fallback_splitter.split_text(section_content)


def chunk_file(
    file_path: str,
    source_url: str,
    scheme_name: str,
    category: str,
    scraped_date: str | None = None,
) -> list[dict]:
    """
    Read a cleaned text file, split it into section-aware chunks, and
    attach metadata to each chunk.

    Returns:
        List of dicts with keys: "text", "metadata"
    """
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    if not scraped_date:
        scraped_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Pass 1: Detect logical sections
    sections = _detect_sections(text)

    # Pass 2: Split oversized sections, build final chunks
    chunks = []
    chunk_index = 0

    for section in sections:
        sub_chunks = _split_section(section["content"])

        for sub_text in sub_chunks:
            if not sub_text.strip():
                continue

            chunks.append({
                "text": sub_text.strip(),
                "metadata": {
                    "source_url": source_url,
                    "scheme_name": scheme_name,
                    "category": category,
                    "document_type": "groww_page",
                    "section": section["label"],
                    "scraped_date": scraped_date,
                    "chunk_index": chunk_index,
                },
            })
            chunk_index += 1

    return chunks


def chunk_all(
    urls_path: str = "data/urls.json",
    raw_dir: str = "data/raw",
) -> list[dict]:
    """
    Chunk all scraped files listed in urls.json.

    Returns the full list of chunks across all 5 schemes.
    """
    with open(urls_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_chunks = []

    print(f"Starting chunking for {len(data['sources'])} schemes...\n")

    for source in data["sources"]:
        scheme_name = source["scheme_name"]
        url = source["url"]
        category = source["category"]

        # Derive the expected raw file path
        slug = re.sub(r"[^a-z0-9]+", "-", scheme_name.lower()).strip("-")
        file_path = os.path.join(raw_dir, f"{slug}.txt")

        if not os.path.exists(file_path):
            print(f"  [SKIP] {scheme_name}: raw file not found at {file_path}")
            continue

        chunks = chunk_file(
            file_path=file_path,
            source_url=url,
            scheme_name=scheme_name,
            category=category,
        )

        all_chunks.extend(chunks)

        # Print section breakdown
        section_counts = {}
        for c in chunks:
            label = c["metadata"]["section"]
            section_counts[label] = section_counts.get(label, 0) + 1

        print(f"  {scheme_name}: {len(chunks)} chunks")
        for label, count in section_counts.items():
            print(f"    - {label}: {count} chunk(s)")

    print(f"\nTotal chunks across all schemes: {len(all_chunks)}")
    return all_chunks


# ---------------------------------------------------------------------------
# CLI entry point — run directly with: python -m src.ingestion.chunker
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    chunks = chunk_all()

    # Print a sample chunk for verification
    if chunks:
        print("\n--- Sample Chunk (fund_overview) ---")
        for c in chunks:
            if c["metadata"]["section"] == "fund_overview":
                print(f"Section: {c['metadata']['section']}")
                print(f"Scheme:  {c['metadata']['scheme_name']}")
                print(f"Length:  {len(c['text'])} chars")
                print(f"Text:\n{c['text'][:500].encode('ascii', 'replace').decode()}")
                break

        print("\n--- Sample Chunk (exit_load_tax) ---")
        for c in chunks:
            if c["metadata"]["section"] == "exit_load_tax":
                print(f"Section: {c['metadata']['section']}")
                print(f"Scheme:  {c['metadata']['scheme_name']}")
                print(f"Length:  {len(c['text'])} chars")
                print(f"Text:\n{c['text'][:500].encode('ascii', 'replace').decode()}")
                break
