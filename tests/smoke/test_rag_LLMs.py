"""
test_rag_LLMs.py — Test generation with different LLMs.

To parallelize testing the 8 models:
# Install pytest-xdist if not already installed:
1. `uv pip install pytest-xdist`
2. pytest test_rag_LLMs.py  -n 8
"""

import pytest
from r2r import R2RClient

MODEL_NAMES = [
    "openai/gpt-4o-mini",
    "mistral/open-mistral-7b",
    "deepseek/deepseek-chat",
    "deepseek/deepseek-reasoner",
    "anthropic/claude-sonnet-4-20250514",
    "ollama/mistral-small:24b-3.1-instruct-2503-q8_0",
    "ollama/mistral-large:latest",
    "ollama/qwen3:32b",
]


@pytest.mark.smoke
@pytest.mark.parametrize("model", MODEL_NAMES)
def test_llm_model_responses(model: str, client: R2RClient, QUERY: str) -> None:
    """Test that each LLM model returns a non-empty answer for a sample query."""
    response = client.retrieval.rag(
        query=QUERY,
        rag_generation_config={"model": model, "temperature": 0.0},
    )
    answer = response.results.generated_answer or ""
    assert answer.strip(), f"Réponse vide pour le modèle {model}"
