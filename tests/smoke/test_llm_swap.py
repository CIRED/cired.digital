"""LLM_swap.py — Test different LLMs using the R2R stack and compare answers."""

import pytest
from smoke.r2r_test_utils import (
    QUERY,
    TEST_CONTENT,
    client,
    create_or_get_document,
    delete_document,
    delete_test_file,
    write_test_file,
)

MODEL_NAMES = [
    "openai/gpt-4o-mini",
    "mistral/open-mistral-7b",
    "deepseek/deepseek-chat",
    "deepseek/deepseek-reasoner",
]


@pytest.mark.smoke
@pytest.mark.parametrize("model", MODEL_NAMES)
def test_llm_model_responses(model):
    write_test_file(content=TEST_CONTENT)
    document_id = create_or_get_document()
    assert document_id, "Échec création du document de test"
    response = client.retrieval.rag(
        query=QUERY,
        rag_generation_config={"model": model, "temperature": 0.0},
    )
    answer = response.results.generated_answer or ""
    assert answer.strip(), f"Réponse vide pour le modèle {model}"
    delete_document(document_id)
    delete_test_file()
