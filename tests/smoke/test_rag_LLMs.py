"""
test_rag_LLMs.py — Test generation with different LLMs.

To parallelize testing the 8 models:
pytest test_rag_LLMs.py  -n 8
"""

import pytest
from r2r import R2RClient

MODEL_NAMES = [
    "mistral/mistral-small-latest",
    "mistral/mistral-medium-latest",
    # Not used in production, not tested in smoke tests
    #     "mistral/open-mistral-7b",
    #     "anthropic/claude-sonnet-4-20250514",
    #     "openai/gpt-4o-mini",
    #     "deepseek/deepseek-chat",
    # Reasoning model - slow for smoke tests
    #     "deepseek/deepseek-reasoner",
    # Ollama models - not available in the current environment
    #    "ollama/mistral-small:24b-3.1-instruct-2503-q8_0",
    #    "ollama/mistral-large:latest",
    #    "ollama/qwen3:32b",
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
