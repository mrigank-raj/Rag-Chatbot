"""
Response Generator — the core RAG logic.
Orchestrates the classifier, retriever, and LLM to produce a structured response.
Implements exponential backoff via tenacity to handle strict API limits.
"""

import json
from typing import Dict, Any

from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils.config import settings
from src.utils.prompts import GENERATION_PROMPT, REFUSAL_TEMPLATES
from src.pipeline.classifier import QueryClassifier
from src.pipeline.retriever import Retriever


class ResponseGenerator:
    def __init__(self):
        self.classifier = QueryClassifier()
        self.retriever = Retriever()
        
        # Primary model (usually 70b)
        self.llm = ChatGroq(
            temperature=0.0,
            model_name=settings.GROQ_MODEL,
            api_key=settings.GROQ_API_KEY,
        )
        self.prompt = PromptTemplate.from_template(GENERATION_PROMPT)
        self.chain = self.prompt | self.llm

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _generate_llm_response(self, query: str, context_text: str) -> str:
        """Call the LLM. Retries automatically on 429 RateLimit errors."""
        response = self.chain.invoke({
            "context": context_text,
            "user_query": query
        })
        return response.content.strip()

    def generate(self, query: str) -> Dict[str, Any]:
        """
        End-to-end RAG generation.
        Returns a dictionary representing the structured API response.
        """
        # 1. Classify the query
        query_type = self.classifier.classify(query)
        
        # 2. Handle non-factual queries immediately (Refusal)
        if query_type in ["ADVISORY", "OUT_OF_SCOPE"]:
            return {
                "answer": REFUSAL_TEMPLATES[query_type],
                "citation": None,
                "last_updated": None,
                "query_type": query_type
            }
            
        # 3. Retrieve relevant chunks for FACTUAL queries
        chunks = self.retriever.retrieve(query, top_k=3)
        
        if not chunks:
            return {
                "answer": "I don't have enough information to answer that question based on the HDFC fund documents.",
                "citation": None,
                "last_updated": None,
                "query_type": query_type
            }
            
        # 4. Prepare context for the LLM
        # Combine text from all retrieved chunks
        context_parts = []
        for i, c in enumerate(chunks):
            # Include scheme name in context so the LLM knows what fund the stats belong to
            scheme = c["metadata"].get("scheme_name", "Unknown Scheme")
            context_parts.append(f"[Source {i+1}: {scheme}]\n{c['text']}")
            
        context_text = "\n\n".join(context_parts)
        
        # 5. Generate Response
        try:
            answer = self._generate_llm_response(query, context_text)
        except Exception as e:
            print(f"[Generator] LLM failed after retries: {e}")
            return {
                "answer": "Sorry, I am currently experiencing high traffic. Please try again in a few seconds.",
                "citation": None,
                "last_updated": None,
                "query_type": query_type,
                "error": str(e)
            }
            
        # 6. Extract the best citation (using the top chunk's metadata)
        top_chunk_meta = chunks[0]["metadata"]
        citation = top_chunk_meta.get("source_url")
        last_updated = top_chunk_meta.get("scraped_date")
        
        return {
            "answer": answer,
            "citation": citation,
            "last_updated": last_updated,
            "query_type": query_type
        }
