# TODO

- [ ] Remove global pipx installs of ruff, pytest, mypy, and pre-commit
  (`pipx uninstall ruff pytest mypy pre-commit`).
  They shadow the project-local versions managed by uv and can cause version drift.
  Run each tool via `uv run <tool>` (e.g. `uv run ruff`, `uv run pytest`,
  `uv run mypy`, `uv run pre-commit`) instead.
