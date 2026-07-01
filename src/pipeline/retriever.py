"""
Retriever module — handles semantic search and metadata filtering in ChromaDB.
"""

import re
from typing import List

from src.ingestion.embedder import get_vectorstore


# Mapping user-friendly terms to exact scheme names in our DB
SCHEME_ALIASES = {
    "HDFC Large Cap Fund": ["large cap", "largecap", "hdfc large"],
    "HDFC Mid-Cap Opportunities Fund": ["mid cap", "midcap", "mid-cap", "hdfc mid", "opportunities"],
    "HDFC Small Cap Fund": ["small cap", "smallcap", "hdfc small"],
    "HDFC Gold ETF Fund of Fund": ["gold", "gold etf", "gold fund"],
    "HDFC Silver ETF Fund of Fund": ["silver", "silver etf", "silver fund"],
}

# Mapping user keywords to specific logical sections for tight metadata filtering
SECTION_ALIASES = {
    "exit_load_tax": ["exit load", "tax", "stamp duty", "redeem", "lock in", "lock-in"],
    "holdings": ["holdings", "stocks", "portfolio", "allocation", "invested in", "companies"],
    "investment_minimums": ["minimum", "sip amount", "min investment", "start sip"],
    "fund_management": ["manager", "managed by", "fund manager", "who manages"],
    "fund_overview": ["nav", "aum", "size", "expense ratio", "rating", "riskometer", "benchmark"],
}


class Retriever:
    def __init__(self):
        self.vectorstore = get_vectorstore()

    def _detect_scheme(self, query: str) -> str | None:
        """Detect if the user is asking about a specific scheme."""
        query_lower = query.lower()
        for scheme_name, aliases in SCHEME_ALIASES.items():
            for alias in aliases:
                if alias in query_lower:
                    return scheme_name
        return None

    def _detect_section(self, query: str) -> str | None:
        """Detect if the user is asking about a specific topic/section."""
        query_lower = query.lower()
        for section, aliases in SECTION_ALIASES.items():
            for alias in aliases:
                if alias in query_lower:
                    return section
        return None

    def retrieve(self, query: str, top_k: int = 3) -> List[dict]:
        """
        Retrieves the top-k most relevant chunks for a query.
        Applies metadata filtering automatically if scheme or section keywords are detected.
        """
        scheme_filter = self._detect_scheme(query)
        section_filter = self._detect_section(query)

        # Build the ChromaDB 'where' dictionary dynamically
        where_clause = {}
        
        if scheme_filter and section_filter:
            where_clause = {
                "$and": [
                    {"scheme_name": scheme_filter},
                    {"section": section_filter}
                ]
            }
        elif scheme_filter:
            where_clause = {"scheme_name": scheme_filter}
        elif section_filter:
            where_clause = {"section": section_filter}

        print(f"[Retriever] Query: '{query}'")
        if where_clause:
            print(f"[Retriever] Applied metadata filter: {where_clause}")
        else:
            print("[Retriever] No precise metadata filters detected. Using pure semantic search.")

        # Execute semantic search with the metadata filters
        docs = self.vectorstore.similarity_search(
            query=query,
            k=top_k,
            filter=where_clause if where_clause else None
        )

        # Format results
        results = []
        for doc in docs:
            results.append({
                "text": doc.page_content,
                "metadata": doc.metadata
            })
            
        return results
