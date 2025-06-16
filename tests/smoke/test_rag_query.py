"""Tests for RAG query functionality."""

import logging

import pytest
from r2r import R2RClient

logger = logging.getLogger(__name__)


@pytest.mark.smoke
def test_hello_r2r(client: R2RClient, QUERY: str) -> None:
    """Test that RAG returns a non-empty answer for a sample query."""
    response = client.retrieval.rag(query=QUERY)
    logger.info("R2R response: %r", response)
    answer = response.results.generated_answer or ""
    assert answer.strip(), "Réponse vide pour test_hello_r2r"
