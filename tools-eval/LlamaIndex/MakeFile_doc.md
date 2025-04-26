# LlamaIndex with Mistral Makefile

## Key Features:

 - 1.**Environment Setup**:

   - Creates a virtual environment using `uv`.
   - Installs core dependencies (`llama-index-core`, `tqdm`).
   - Provides a separate target for Mistral-specific dependencies (`llama-index-llms-mistralai`, `llama-index-embeddings-mistralai`).

 - 2.**PDF Preparation**:

   - Creates a PDF directory.
   - Copies sample PDFs from the HAL repository when available.

 - 3.**Index Building**:

   - **Standard version**: Builds a vector index using default settings.
   - **Mistral version**: Configures Mistral LLM and embeddings using the API key.
   - Validates the presence of the `MISTRAL_API_KEY` environment variable.
   - Includes a retry mechanism for handling Mistral API rate limits.

 - 4.**Query Interface**:

   - **Standard version**: Uses a built-in chat interface through `index.as_query_engine().chat()`.
   - **Mistral version**: Implements a custom query loop with `query_engine.query(query)`.

 - 5.**Testing**:

   - Tests the standard index by checking for "Index ready" in the output.
   - Tests the Mistral index with a simple query and content-specific response checks.
   - Verifies that the Mistral index can correctly analyze document content.

 - 6.**Cleanup**:

   - A basic clean removes index files.
   - A deeper clean also removes the virtual environment.

 - 7.**Help**:

    - Provides comprehensive documentation of all available targets.

## Targets:

 - `setup` - Set up the virtual environment with core dependencies.
 - `setup_mistral` - Install Mistral-specific dependencies.
 - `prepare_pdfs` - Copy sample PDFs for testing.
 - `build` - Build the standard index.
 - `build_mistral` - Build the Mistral index (requires `MISTRAL_API_KEY`).
 - `retry_build` - Build with retries for rate limits (up to `MAX_RETRIES` attempts).
 - `test` - Test the standard index.
 - `test_mistral` - Test the Mistral index.
 - `clean` - Remove generated index files.
 - `cleaner` - Remove everything, including the virtual environment.
 - `help` - Show help message (default).

## Environment Variables:

 - `MISTRAL_API_KEY` - Required for Mistral targets (obtain from <https://console.mistral.ai/api-keys/>).
 - `MAX_RETRIES` - Number of retry attempts (default: 3).
 - `RETRY_DELAY` - Seconds to wait between retries (default: 60).

## Directory Structure:

 - `venv/` - Virtual environment.
 - `pdfs/` - Directory for PDF files to be indexed.
 - `index/` - Directory for stored index files:

    - The standard version uses `index.json`.
    - The Mistral version uses `index_store.json`.

## Usage:

 - `make setup` - Set up the virtual environment with core dependencies.
 - `make setup_mistral` - Install Mistral-specific dependencies.
 - `make prepare_pdfs` - Prepare the PDF directory with sample documents.
 - `MISTRAL_API_KEY=your_key_here make build_mistral` - Build the Mistral index.
 - `make retry_build` - Build with automatic retries for rate limit handling.
 - `make test` - Test the standard index (checks for "Index ready" in output).
 - `make test_mistral` - Test the Mistral index (checks response content).
 - `make clean` - Remove generated index files.
 - `make cleaner` - Remove everything, including the virtual environment.
 - `make help` - Display available commands and usage information.

## Complete Workflow:

 - **Standard version**: `make setup prepare_pdfs build test`
 - **Mistral version**: `make setup_mistral prepare_pdfs build_mistral test_mistral`
 - **Clean and rebuild**: `make cleaner setup setup_mistral prepare_pdfs build_mistral`
