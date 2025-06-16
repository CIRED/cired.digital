# hello_r2r.py
"""hello_r2r.py — Smoke test for R2R stack."""

import pytest

@pytest.mark.smoke
def test_hello_r2r(client, document_id, QUERY, MODEL, TEMPERATURE):
    response = client.retrieval.rag(
        query=QUERY,
        rag_generation_config={"model": MODEL, "temperature": TEMPERATURE},
    )
    answer = response.results.generated_answer or ""
    assert answer.strip(), "Réponse vide pour test_hello_r2r"
