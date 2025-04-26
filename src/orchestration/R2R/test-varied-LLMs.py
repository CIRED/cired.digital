"""
hello_r2r.py.

This is a simple example of how to use the R2RClient to create a document, retrieve information using RAG, and print the results.
Downloaded from the docs.sciphi.ai and patched to handle the case where the document already exists.

HDM, 2025-04
"""

from r2r import R2RClient

MODEL_NAMES = [
    "openai/gpt-4o-mini",
    "mistral/open-mistral-7b",
    "deepseek/deepseek-chat",
    "deepseek/deepseek-reasoner",
]
SERVER_URL = "http://localhost:7272"
TEST_FILE_PATH = "test.txt"
TEST_QUERY = "Who is john"
TEMPERATURE = 0.0


def setup_client():
    """Initialize the client, ensuring it contains the test document."""
    client = R2RClient(SERVER_URL)

    # Create test file
    with open(TEST_FILE_PATH, "w") as file:
        file.write("John is a person that works at Google.")

    # Try to create the document, or continue if it already exists
    try:
        client.documents.create(file_path="test.txt")
        print("Document created successfully.")
    except Exception as e:
        if "already exists" in str(e):
            print("Document already exists. Continuing with existing document...")
        else:
            print(f"Unexpected error: {e}")
    return client


def test_model(client: R2RClient, model_name: str):
    """
    Test a model using RAG.

    Args:
    ----
        model_name (str): The name of the model to test.
        See https://docs.litellm.ai/docs/providers
        Make sure the key is set in the environment variables known to R2R.
    """
    print("----")
    rag_response = client.retrieval.rag(
        query=TEST_QUERY,
        rag_generation_config={"model": model_name, "temperature": 0.0},
    )
    print(f"Completion ({model_name}):\n{rag_response.results.generated_answer}")


client = setup_client()

for model_name in MODEL_NAMES:
    test_model(client, model_name)
