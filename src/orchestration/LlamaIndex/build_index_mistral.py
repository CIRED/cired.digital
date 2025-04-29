# build_index.py
"""
Build or load a local PDF index using LlamaIndex with Mistral models.

This script:
- Initializes Mistral LLM and Embedding models from environment variables.
- Loads existing index if available.
- Otherwise scans PDFs in './pdfs', builds a new index, and saves it.
- Launches an interactive chat to query the indexed documents using Mistral.
"""

import os
import sys
from pathlib import Path

from llama_index.core import (
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.core.settings import Settings
from llama_index.embeddings.mistralai import MistralAIEmbedding
from llama_index.llms.mistralai import MistralAI
from tqdm import tqdm

# Set up Mistral as the LLM
mistral_api_key = os.environ.get("MISTRAL_API_KEY")
if not mistral_api_key:
    print(
        "⚠️  MISTRAL_API_KEY environment variable not set. Please set it and try again."
    )
    sys.exit(1)

# Initialize Mistral LLM
llm = MistralAI(
    api_key=mistral_api_key,
    model="mistral-large-latest",  # or another Mistral model of your choice
)

# Initialize Mistral Embeddings
embed_model = MistralAIEmbedding(
    api_key=mistral_api_key,
    model_name="mistral-embed",  # Mistral's embedding model
)

# Configure global settings
Settings.llm = llm
Settings.embed_model = embed_model

index_dir = Path("./index")
pdf_dir = Path("./pdfs")

# Load existing index if present
if (index_dir / "index_store.json").exists():
    print("🧠 Loading existing index...")
    storage_context = StorageContext.from_defaults(persist_dir=str(index_dir))
    index = load_index_from_storage(storage_context)
    # No need to update service_context as we're using global Settings
else:
    print("📚 Building index from scratch...")
    pdf_files = list(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        print("⚠️  No PDF files found.")
        sys.exit(1)

    docs = []
    for pdf in tqdm(pdf_files, desc="Indexing PDFs", unit="file"):
        reader = SimpleDirectoryReader(input_files=[str(pdf)])
        docs.extend(reader.load_data())

    # Create index (will use global Settings)
    index = VectorStoreIndex.from_documents(docs)
    index.storage_context.persist(str(index_dir))

print("✅ Index ready. Launching chat...")
query_engine = index.as_query_engine()
print("💬 Chat with your PDFs (type 'exit' to quit):")
while True:
    query = input("> ")
    if query.lower() == "exit":
        break
    response = query_engine.query(query)
    print(response)
