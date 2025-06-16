# hello_r2r.py
"""hello_r2r.py — Smoke test for R2R stack."""

import pytest
from tests.smoke.r2r_test_utils import (
    MODEL,
    QUERY,
    TEMPERATURE,
    TEST_CONTENT,
    client,
    create_or_get_document,
    delete_document,
    delete_test_file,
    write_test_file,
)


@pytest.mark.smoke
def test_hello_r2r():
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
