import pytest
from src.pipeline.retriever import Retriever

@pytest.fixture(scope="module")
def retriever():
    return Retriever()

def test_scheme_detection(retriever):
    assert retriever._detect_scheme("Tell me about the HDFC Large Cap fund") == "HDFC Large Cap Fund"
    assert retriever._detect_scheme("What are the holdings in hdfc midcap?") == "HDFC Mid-Cap Opportunities Fund"
    assert retriever._detect_scheme("Gold ETF expense ratio") == "HDFC Gold ETF Fund of Fund"
    assert retriever._detect_scheme("How is the weather today?") is None

def test_section_detection(retriever):
    assert retriever._detect_section("What is the exit load?") == "exit_load_tax"
    assert retriever._detect_section("What are the top holdings?") == "holdings"
    assert retriever._detect_section("Who is the fund manager?") == "fund_management"
    assert retriever._detect_section("What is the NAV?") == "fund_overview"
    assert retriever._detect_section("How much is the minimum SIP amount?") == "investment_minimums"
    assert retriever._detect_section("Is this a good fund?") is None

def test_retrieval_execution(retriever):
    # Ensure ChromaDB connection works and returns chunks
    results = retriever.retrieve("What is the exit load for HDFC Large Cap Fund?", top_k=2)
    assert len(results) > 0
    # Should have applied metadata filter for scheme and section
    assert "text" in results[0]
    assert "metadata" in results[0]
    assert results[0]["metadata"]["scheme_name"] == "HDFC Large Cap Fund"
    assert results[0]["metadata"]["section"] == "exit_load_tax"
