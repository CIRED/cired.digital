"""LLM_swap.py — Test different LLMs using the R2R stack and compare answers."""

import pytest

MODEL_NAMES = [
    "openai/gpt-4o-mini",
    "mistral/open-mistral-7b",
    "deepseek/deepseek-chat",
    "deepseek/deepseek-reasoner",
]


@pytest.mark.smoke
@pytest.mark.parametrize("model", MODEL_NAMES)
def test_llm_model_responses(model, client, document_id, QUERY, TEMPERATURE):
    response = client.retrieval.rag(
        query=QUERY,
        rag_generation_config={"model": model, "temperature": TEMPERATURE},
    )
    answer = response.results.generated_answer or ""
    assert answer.strip(), f"Réponse vide pour le modèle {model}"
