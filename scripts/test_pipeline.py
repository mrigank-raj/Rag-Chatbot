"""
End-to-End test for the RAG Core Pipeline.
Tests the Classifier -> Retriever -> Generator flow.
"""

import sys
import os

# Ensure the root directory is in the PYTHONPATH so imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.pipeline.generator import ResponseGenerator

def test_pipeline():
    print("Initializing Response Generator...\n")
    generator = ResponseGenerator()
    
    test_queries = [
        # 1. Factual (Precise metadata filtering should kick in here)
        "What is the exit load and tax implication for HDFC Large Cap Fund?",
        
        # 2. Factual (Holdings section filter)
        "What are the top holdings in the HDFC Mid-Cap fund?",
        
        # 3. Advisory (Should be rejected instantly by heuristic)
        "Which is better, the HDFC Small cap or the mid cap fund?",
        
        # 4. Out of scope (Should be rejected by LLM classifier)
        "What is the current stock price of Apple?",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print("="*60)
        print(f"TEST {i}")
        print(f"QUERY: {query}")
        print("-" * 60)
        
        response = generator.generate(query)
        
        print(f"TYPE:     {response['query_type']}")
        print(f"ANSWER:   {response['answer']}")
        print(f"CITATION: {response['citation']}")
        print(f"UPDATED:  {response['last_updated']}")
        print("="*60 + "\n")

if __name__ == "__main__":
    test_pipeline()
