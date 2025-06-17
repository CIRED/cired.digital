# r2r_test_utils.py
"""Utility functions for R2R smoke testing."""

import logging
import re
import time
import uuid
from pathlib import Path

import pytest
from pytest import TempPathFactory
from r2r import R2RClient

logger = logging.getLogger(__name__)

# Load configuration from common file
SERVER_URL: str = "http://localhost:7272"
TEST_FILE: str = "test.txt"
TEST_CONTENT: str = "QuetzalX is a person that works at CIRED."
QUERY: str = "Who is QuetzalX?"
DOCUMENT_POLLING_TIMEOUT: int = 30  # seconds
DOCUMENT_POLLING_INTERVAL: int = 2  # seconds


# Expose configuration constants as fixtures
@pytest.fixture(scope="session", name="QUERY")
def query_fixture() -> str:
    """Pytest fixture that returns the test query string."""
    return QUERY


# Setup the client with a test document
@pytest.fixture(scope="session")
def client(test_file: Path) -> R2RClient:
    """Pytest fixture that returns an R2RClient with a test document."""
    client = R2RClient(SERVER_URL)

    document_id = create_or_get_document(client, test_file)
    if not document_id:
        raise RuntimeError("Failed to create or retrieve test document for R2R tests.")

    document_id = wait_for_document_ready(document_id, client)
    if not document_id:
        raise RuntimeError("Failed to ingest document for R2R tests.")
    logger.info(f"Document ready with ID: {document_id}")
    try:
        yield client
    finally:
        delete_document(document_id, client)


@pytest.fixture(scope="session")
def test_file(tmp_path_factory: TempPathFactory) -> Path:
    """Pytest fixture that creates a temporary test file for document upload."""
    p: Path = tmp_path_factory.mktemp("smoke") / TEST_FILE
    p.write_text(TEST_CONTENT, encoding="utf-8")
    return p


def is_valid_uuid(value: str) -> bool:
    """Check if a string is a valid UUID."""
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, TypeError):
        return False


def create_or_get_document(client: R2RClient, test_file: Path) -> uuid.UUID | None:
    """Create a document from the test file or retrieve its existing ID."""
    try:
        response = client.documents.create(test_file)
        document_id = response.results.document_id
        assert isinstance(document_id, uuid.UUID), (
            f"Expected document_id to be a valid UUID, got: {document_id}"
        )
        logger.info("Document created.")
        return document_id
    except Exception as e:
        error_msg = str(e)
        if "already exists" in error_msg:
            logger.info("Document already exists. Extracting ID...")
            match = re.search(r"Document ([\w-]+) already exists", error_msg)
            if match:
                document_id = uuid.UUID(match.group(1))
                logger.info(f"Found existing document ID: {document_id}")
                return document_id
            logger.error("Error: Could not parse document ID from error message.")
        else:
            logger.error(f"Unexpected creation error: {e}")
    return None


def wait_for_document_ready(
    document_id: uuid.UUID, client: R2RClient
) -> uuid.UUID | None:
    """Poll the server until the document is ingested or times out."""
    start_time = time.time()
    while time.time() - start_time < DOCUMENT_POLLING_TIMEOUT:
        try:
            doc_info = client.documents.retrieve(document_id)
            ingestion_status = getattr(doc_info.results, "ingestion_status", "unknown")
            logger.info(f"Document status: ingestion={ingestion_status}")

            if ingestion_status == "success":
                return document_id
            elif ingestion_status == "failed":
                logger.error(
                    f"Document processing failed: ingestion={ingestion_status}"
                )
                return None

            time.sleep(DOCUMENT_POLLING_INTERVAL)
        except Exception as poll_error:
            logger.warning(f"Error checking document status: {poll_error}")
            time.sleep(DOCUMENT_POLLING_INTERVAL)

    logger.error(
        f"Timeout waiting for document to be ready after {DOCUMENT_POLLING_TIMEOUT} seconds"
    )
    return None


def delete_document(doc_id: uuid.UUID, client: R2RClient) -> None:
    """Delete a document from the R2R server by ID."""
    try:
        client.documents.delete(doc_id)
        logger.info("Document deleted from server.")
    except Exception as e:
        logger.warning(f"Warning: Failed to delete document: {e}")
