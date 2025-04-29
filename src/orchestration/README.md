# RAGCTL - RAG Engine Manager CLI

`ragctl.py` is a lightweight command-line tool for managing Retrieval-Augmented Generation (RAG) engines across development and production environments.

It simplifies tasks like starting, stopping, installing, validating, and cleaning up RAG engine instances — all driven by a simple directory structure and shell scripts.


## Features

- 🔎 **Discover Engines:** Auto-detect available RAG engines based on directory structure.
- 🚀 **Lifecycle Commands:** Start, stop, install, clean, validate, and push indexes for each engine.
- ⚙️ **Environment Handling:** Load environment variables from per-engine `env_dev.cfg` and `env_prod.cfg`.
- 🛠️ **Debug Mode:** Optionally show full stdout/stderr from executed scripts.
- 🧹 **No Dependencies:** Uses only the standard Python library.

## Usage

First, check available options:

`python3 ragctl.py --help`

Examples

Start an engine in the development environment:

`python3 ragctl.py start --engine=my_engine`

Stop an engine in the production environment:

`python3 ragctl.py stop --engine=my_engine --env=prod`

List all detected engines and their available commands:

`python3 ragctl.py --list-commands`

## Directory Structure

Each engine should have its own directory structured like this:

```text
my_engine/
├── install.sh
├── validate.sh
├── start.sh
├── stop.sh
├── clean.sh
├── env_dev.cfg
└── env_prod.cfg
```

- Shell scripts define the engine's lifecycle commands.
- `env_dev.cfg` and `env_prod.cfg` configure environment variables for dev/prod modes.

## Requirements

-    Python 3.11+
-    Bash (for running lifecycle scripts)
