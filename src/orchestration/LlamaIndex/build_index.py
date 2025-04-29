# build_index.py
"""
Build or load a local PDF index using LlamaIndex.

This script:
- Loads existing index if available.
- Otherwise scans PDFs in './pdfs', builds a new index, and saves it.
- Launches a simple chat interface to query the indexed documents.
"""


import sys
from pathlib import Path

from llama_index.core import (
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from tqdm import tqdm

index_dir = Path("./index")
pdf_dir = Path("./pdfs")

# Load existing index if present
if (index_dir / "index.json").exists():
    print("🧠 Loading existing index...")
    storage_context = StorageContext.from_defaults(persist_dir=str(index_dir))
    index = load_index_from_storage(storage_context)
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

    index = VectorStoreIndex.from_documents(docs)
    index.storage_context.persist(str(index_dir))

print("✅ Index ready. Launching chat...")
index.as_query_engine().chat()
