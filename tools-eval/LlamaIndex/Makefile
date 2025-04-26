# Makefile for PDF Indexing System (Standard and Mistral versions)

# Configuration
VENV_DIR := venv
PYTHON := $(VENV_DIR)/bin/python3
INDEX_DIR := index
PDF_DIR := pdfs
SAMPLE_PDFS_DIR := ../../data/raw/hal/pdfs
MISTRAL_API_KEY ?= $(shell echo $$MISTRAL_API_KEY)
MAX_RETRIES := 3
RETRY_DELAY := 60

# Phony targets
.PHONY: all setup prepare_pdfs build build_mistral retry_build clean cleaner test test_mistral help

# Default target
all: help

# Set up virtual environment and install core dependencies
setup:
	@echo "Setting up virtual environment..."
	uv venv $(VENV_DIR)
	@echo "Installing core dependencies..."
	. $(VENV_DIR)/bin/activate && python -m pip install llama-index-core tqdm
	@echo "Environment setup complete"

# Install Mistral-specific dependencies
setup_mistral: setup
	@echo "Installing MistralAI dependencies..."
	. $(VENV_DIR)/bin/activate && python -m pip install llama-index-llms-mistralai llama-index-embeddings-mistralai
	@echo "Mistral setup complete"

# Prepare sample PDFs from the HAL repository
prepare_pdfs:
	@echo "Preparing PDF directory..."
	mkdir -p $(PDF_DIR)
	@if [ -d "$(SAMPLE_PDFS_DIR)" ]; then \
		echo "Copying sample PDFs..."; \
		cp $(SAMPLE_PDFS_DIR)/hal_00119451.pdf $(PDF_DIR)/; \
		cp $(SAMPLE_PDFS_DIR)/halshs_00619168.pdf $(PDF_DIR)/; \
		echo "Sample PDFs prepared"; \
	else \
		echo "Sample PDFs directory not found at $(SAMPLE_PDFS_DIR)"; \
		echo "Please add your own PDFs to the $(PDF_DIR) directory"; \
	fi

# Build the standard index
build: setup prepare_pdfs
	@echo "Building standard index..."
	mkdir -p $(INDEX_DIR)
	. $(VENV_DIR)/bin/activate && python build_index.py
	@echo "Standard index built successfully"

# Build the Mistral index with retry logic
build_mistral: setup_mistral prepare_pdfs
	@if [ -z "$(MISTRAL_API_KEY)" ]; then \
		echo "MISTRAL_API_KEY environment variable not set"; \
		echo "Get one at: https://console.mistral.ai/api-keys/"; \
		exit 1; \
	fi
	@echo "Building Mistral index (may take some time)..."
	mkdir -p $(INDEX_DIR)
	. $(VENV_DIR)/bin/activate && python build_index_mistral.py || (echo "Build failed - you may need to wait for rate limits"; exit 1)
	@echo "Mistral index built successfully"

# Retry building Mistral index after rate limit errors
retry_build: setup_mistral prepare_pdfs
	@if [ -z "$(MISTRAL_API_KEY)" ]; then \
		echo "MISTRAL_API_KEY environment variable not set"; \
		exit 1; \
	fi
	@echo "Attempting build with retries (max $(MAX_RETRIES) attempts)..."
	mkdir -p $(INDEX_DIR)
	@for i in $$(seq 1 $(MAX_RETRIES)); do \
		echo "Attempt $$i/$(MAX_RETRIES)"; \
		if . $(VENV_DIR)/bin/activate && python build_index_mistral.py; then \
			echo "Mistral index built successfully"; \
			exit 0; \
		else \
			echo "Attempt $$i failed"; \
			if [ $$i -lt $(MAX_RETRIES) ]; then \
				echo "Waiting $(RETRY_DELAY) seconds before retry..."; \
				sleep $(RETRY_DELAY); \
			fi; \
		fi; \
	done; \
	echo "All build attempts failed - check your Mistral API key and rate limits"; \
	exit 1

# Test the standard index
test: build
	@echo "Testing standard index..."
	echo "2+2" | . $(VENV_DIR)/bin/activate && python build_index.py | grep -q "Index ready" && echo "Standard test passed" || echo "Standard test failed"
	@echo "Standard tests completed"

# Test the Mistral index
test_mistral: build_mistral
	@echo "Testing Mistral index..."
	echo "2+2" | . $(VENV_DIR)/bin/activate && python build_index_mistral.py | grep -q "unable to provide" && echo "Simple query test passed" || echo "Simple query test failed"
	echo "Faut il un revenu d'existence en France, pour qui, combien?" | . $(VENV_DIR)/bin/activate && python build_index_mistral.py | grep -q "allocation universelle" && echo "PDF content test passed" || echo "PDF content test failed"
	@echo "Mistral tests completed"

# Clean up generated files
clean:
	@echo "Cleaning up..."
	rm -rf $(INDEX_DIR)
	@echo "Cleanup complete"

# clean up all
cleaner: clean
	@echo "Deep cleaning..."
	rm -rf $(VENV_DIR)
	@echo "Deep cleanup complete"

