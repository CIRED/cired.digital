"""
hello_r2r.py.

This is a simple example of how to use the R2RClient to create a document, retrieve information using RAG, and print the results.
Downloaded from the docs.sciphi.ai and patched to handle the case where the document already exists.

HDM, 2025-04
"""

from r2r import R2RClient

# Initialize the client
client = R2RClient(
    "http://localhost:7272"
)  # optional, pass in "http://localhost:7272" or "https://api.sciphi.ai"

# Create test file
with open("test.txt", "w") as file:
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
        # Still continue with the rest of the script

# Call RAG directly
rag_response = client.retrieval.rag(
    query="Who is john",
    rag_generation_config={"model": "openai/gpt-4o-mini", "temperature": 0.0},
)

print(f"Search Results:\n{rag_response.results.search_results}")
print(f"Completion:\n{rag_response.results.generated_answer}")
print(f"Citations:\n{rag_response.results.citations}")
