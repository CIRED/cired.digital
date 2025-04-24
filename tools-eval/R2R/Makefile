# Repository information
REPO_URL := https://github.com/SciPhi-AI/R2R.git
TEMP_DIR := .tmp_r2r_clone
SUBDIR := docker
TARGET_DIR := $(SUBDIR)

# Declare phony targets (targets that don't create files)
.PHONY: all fetch verify_keys clean cleaner hello venv/bin/activate

# Default target
all: hello

# Clone the R2R repository and extract only the docker subdirectory
fetch:
	rm -rf $(TEMP_DIR)
	git clone --filter=blob:none --no-checkout $(REPO_URL) $(TEMP_DIR)
	cd $(TEMP_DIR) && git sparse-checkout init --cone && git sparse-checkout set $(SUBDIR) && git checkout
	mv $(TEMP_DIR)/$(SUBDIR) ./$(TARGET_DIR)
	rm -rf $(TEMP_DIR)
	echo "Successfully fetched $(SUBDIR) from $(REPO_URL)"

# Check for API keys in the running Docker container
verify_keys:
	docker exec myrag-r2r-1 env | grep API_KEY || echo "No API keys found"

# Remove temporary files
clean:
	rm -rf test.txt
	echo "Basic cleanup completed"

# Create and set up Python virtual environment
venv/bin/python3:
	uv venv venv
	uv pip install --python ./venv/bin/python r2r
	echo "Virtual environment created and r2r installed"

# Start R2R containers on localhost
start:
	@echo "Starting R2R containers..."
	./start.sh

# Run the R2R hello world example
hello: start venv/bin/python3
	@echo "Running R2R hello world example..."
	venv/bin/python3 hello_r2r.py

# Stop R2R containers
stop:
	@echo "Stopping R2R containers..."
	sudo ./stop.sh


# Perform a complete cleanup including the Docker directory and virtual environment
cleaner: clean
	rm -rf $(TARGET_DIR)
	rm -rf venv
	echo "Complete cleanup finished"
