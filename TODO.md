# TODO

- [ ] Remove global pipx installs of ruff and pytest (`pipx uninstall ruff pytest`).
  They shadow the project-local versions managed by uv and can cause version drift.
  Use `uv run ruff` and `uv run pytest` instead.
