# Makefile for PaperQA Testing

# --- Configuration ---
VENV_DIR := venv
PYTHON := $(VENV_DIR)/bin/python3
PQA := $(VENV_DIR)/bin/pqa
PDF_DIR := pdfs
INDEX_DIR := ~/.pqa # Default PaperQA index location
OPENAI_API_KEY ?= $(shell echo $$OPENAI_API_KEY)

# --- Phony Targets ---
.PHONY: all setup install test clean test_mistral_rate_limit

# --- Default Target ---
all: test

# --- Setup ---
setup:
	@echo "Creating virtual environment..."
	uv venv $(VENV_DIR)
	@echo "Activating virtual environment..."
	@source $(VENV_DIR)/bin/activate
	@echo "Installing PaperQA..."
	$(PYTHON) -m pip install paper-qa

# --- Installation ---
install: setup
	@echo "PaperQA installed in $(VENV_DIR)"

# --- Test ---
test: install
	@echo "Running basic PaperQA test..."
	@$(PYTHON) -c "import os; assert 'OPENAI_API_KEY' in os.environ, 'OPENAI_API_KEY' in os.environ, 'OPENAI_API_KEY not set'"
	@mkdir -p $(PDF_DIR)
	@touch $(PDF_DIR)/dummy.pdf # Create a dummy PDF for testing
	@$(PQA) ask "What is a PDF?" 2>&1 | grep -q "PDF"
	@echo "Basic PaperQA test passed."

# --- Clean ---
clean:
	@echo "Cleaning up..."
	@rm -rf $(VENV_DIR)
	@rm -rf $(PDF_DIR)/*.pdf
	@echo "Cleanup complete."

test_mistral_rate_limit: install
ifndef MISTRAL_API_KEY
	$(error MISTRAL_API_KEY is not set. Please set it and try again.)
endif
	@echo "Testing Mistral API Rate Limit handling"
	$(PQA) --summary_llm_config '{"rate_limit": {"gpt-4o-2024-11-20": "30000 per 1 minute"}}' ask 'How to solve hunger?'

