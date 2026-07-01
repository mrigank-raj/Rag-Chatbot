import pytest
from src.pipeline.classifier import QueryClassifier

# Since this relies on LLM calls for FACTUAL/OOS, it may take a moment to run or hit rate limits.
# The heuristic is fast for ADVISORY.

@pytest.fixture(scope="module")
def classifier():
    return QueryClassifier()

def test_advisory_heuristic(classifier):
    # This should be caught immediately by regex without calling LLM
    assert classifier.classify("Which is better, Large Cap or Mid Cap?") == "ADVISORY"
    assert classifier.classify("Should I invest in HDFC small cap right now?") == "ADVISORY"
    assert classifier.classify("Compare HDFC and SBI mutual funds") == "ADVISORY"

def test_factual_query(classifier):
    # This hits the LLM
    result = classifier.classify("What is the exit load for HDFC Large Cap Fund?")
    assert result == "FACTUAL"

def test_out_of_scope_query(classifier):
    # This hits the LLM
    result = classifier.classify("What is the current stock price of Apple?")
    assert result == "OUT_OF_SCOPE"
