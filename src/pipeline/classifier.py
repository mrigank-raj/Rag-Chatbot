"""
Query Classifier — classifies user queries into FACTUAL, ADVISORY, or OUT_OF_SCOPE.
Uses a fast heuristic keyword search first, falling back to an LLM for complex queries.
"""

import re
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils.config import settings
from src.utils.prompts import CLASSIFICATION_PROMPT

# Fast heuristic keywords that immediately flag a query as advisory
ADVISORY_KEYWORDS = [
    r"\bshould i\b", r"\brecommend\b", r"\bsuggest\b", r"\bbetter\b", 
    r"\bbest\b", r"\bworth it\b", r"\bcompare\b", r"\bvs\b", r"\bversus\b"
]


class QueryClassifier:
    def __init__(self):
        # We use a small, fast model for classification if available, else standard
        # Even though we configured 70b in settings, we can use 8b for classification to save TPM.
        # But for now, we use the configured model, and rely on Tenacity for rate limits.
        self.llm = ChatGroq(
            temperature=0.0,
            model_name=settings.GROQ_MODEL,
            api_key=settings.GROQ_API_KEY,
            max_tokens=5, # We only need 1 word back
        )
        self.prompt = PromptTemplate.from_template(CLASSIFICATION_PROMPT)
        self.chain = self.prompt | self.llm

    def _heuristic_check(self, query: str) -> str | None:
        """Check for obvious advisory keywords to save an LLM call."""
        query_lower = query.lower()
        for pattern in ADVISORY_KEYWORDS:
            if re.search(pattern, query_lower):
                return "ADVISORY"
        return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _llm_classify(self, query: str) -> str:
        """Call the LLM to classify the query. Retries on 429 RateLimit errors."""
        response = self.chain.invoke({"user_query": query})
        
        # Clean up the response (in case the model is chatty despite instructions)
        content = response.content.strip().upper()
        
        if "FACTUAL" in content:
            return "FACTUAL"
        elif "ADVISORY" in content:
            return "ADVISORY"
        elif "OUT_OF_SCOPE" in content:
            return "OUT_OF_SCOPE"
        
        # Default fallback if the LLM completely fails the instruction
        return "OUT_OF_SCOPE"

    def classify(self, query: str) -> str:
        """
        Classifies the query.
        Returns "FACTUAL", "ADVISORY", or "OUT_OF_SCOPE".
        """
        # 1. Fast path: Heuristic check
        fast_result = self._heuristic_check(query)
        if fast_result:
            return fast_result
            
        # 2. Slow path: LLM check
        try:
            return self._llm_classify(query)
        except Exception as e:
            print(f"[Warning] Classifier LLM failed: {e}")
            # If rate limit exhausts after retries, default to safe refusal
            return "OUT_OF_SCOPE"
