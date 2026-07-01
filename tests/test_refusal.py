import pytest
from src.utils.prompts import REFUSAL_TEMPLATES

def test_advisory_refusal_has_link():
    """Verify that the advisory refusal contains an educational link."""
    response = REFUSAL_TEMPLATES.get("ADVISORY", "")
    assert "amfiindia.com" in response

def test_oos_refusal():
    """Verify out of scope mentions supported schemes."""
    response = REFUSAL_TEMPLATES.get("OUT_OF_SCOPE", "")
    assert "HDFC" in response
    assert "Large Cap" in response
