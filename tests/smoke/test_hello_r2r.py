# hello_r2r.py
"""hello_r2r.py — Smoke test for R2R stack."""

import pytest
import pytest


@pytest.mark.smoke
def test_hello_r2r(client, write_test_file, create_or_get_document, delete_document, delete_test_file, QUERY, TEST_CONTENT, MODEL, TEMPERATURE):
    write_test_file(content=TEST_CONTENT)
    document_id = create_or_get_document()
    assert document_id, "Échec création du document de test"
    response = client.retrieval.rag(
        query=QUERY,
        rag_generation_config={"model": MODEL, "temperature": TEMPERATURE},
    )
    answer = response.results.generated_answer or ""
    assert answer.strip(), "Réponse vide pour test_hello_r2r"
    delete_document(document_id)
    delete_test_file()
