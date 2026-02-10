# CIRED.digital Usage Analysis

Toolkit for analyzing CIRED.digital application usage from monitor logs.

## Overview

This directory contains scripts to analyze user interactions with the CIRED.digital chatbot, generating:

- **Figures**: Visualizations of session activity, visitor origins, and event transitions
- **CSV tables**: Query analysis, token usage, and article access statistics
- **Summary statistics**: Descriptive stats on events and sessions

## Architecture

The analysis system uses a simple, transparent architecture:

1. **Data loader** ([`logloader.py`](logloader.py "logloader.py")): Loads raw JSON monitor logs and provides two clean abstractions:
   - `events_df`: pandas DataFrame of all events with normalized fields
   - `sessions`: List of session dictionaries with grouped events

2. **Analysis scripts**: Specialized scripts that import from `logloader` and produce outputs:
   - `fig_*.py` — Generate PNG visualizations
   - `tabulate_*.py` — Generate CSV tables
   - `describe_*.py` — Generate text summaries

3. **Makefile integration**: All active scripts are orchestrated via `make` targets with proper dependency tracking

## Quick Start

### Generate All Analysis Outputs

```bash
cd cired.digital
make analysis
```

This runs all figure generation, table creation, and descriptive statistics. Outputs go to `reports/analysis/`.

### Individual Targets

```bash
make figures  # Generate all PNG visualizations
make csv      # Generate all CSV tables
make stats    # Generate descriptive statistics summaries
```

## Prerequisites

```bash
cd cired.digital
uv sync --group dev
```

Requires Python 3.11+ with pandas, matplotlib, and standard scientific Python libraries.

## Scripts Reference

### Data Loading

**[`logloader.py`](logloader.py "logloader.py")**: Core module that loads monitor logs from `reports/monitor-logs/`
- Exports: `events_df` (DataFrame), `sessions` (list of dicts)
- Used by all other analysis scripts
- No direct execution needed

### Figure Generation

**[`fig_activity.py`](fig_activity.py "fig_activity.py")**: Session activity timeline
→ `reports/analysis/viz1_session_activity_timeline.png`

**[`fig_provenance.py`](fig_provenance.py "fig_provenance.py")**: Visitor origin analysis
→ `reports/analysis/visitors_origin.png`

**[`fig_sessions.py`](fig_sessions.py "fig_sessions.py")**: Event type transition diagrams
→ `reports/analysis/session_event_type_transitions.png`
→ `reports/analysis/session_event_type_transitions_simplified.png`

### CSV Table Generation

**[`tabulate_queries.py`](tabulate_queries.py "tabulate_queries.py")**: Query analysis
→ `reports/analysis/Queries.csv`
→ `reports/analysis/UniqueQueries.csv`

**[`tabulate_tokens.py`](tabulate_tokens.py "tabulate_tokens.py")**: Token usage statistics
→ `reports/analysis/token_analysis.csv`
→ `reports/analysis/token_analysis_monthly.csv`

**[`tabulate_articles.py`](tabulate_articles.py "tabulate_articles.py")**: Article access patterns
→ `reports/analysis/article_analysis.csv`
→ `reports/analysis/article_analysis_monthly.csv`

### Descriptive Statistics

**[`describe_events.py`](describe_events.py "describe_events.py")**: Event-level summary statistics
→ `reports/analysis/describe_events_summary.txt`

**[`describe_sessions.py`](describe_sessions.py "describe_sessions.py")**: Session-level summary statistics
→ `reports/analysis/describe_sessions_summary.txt`

Can also be run directly for quick inspection:
```bash
cd src/analysis
uv run python describe_events.py
uv run python describe_sessions.py
```

### Utilities

**[`classifier.py`](classifier.py "classifier.py")**: IP geolocation and user-agent classification
Used by other scripts to identify bots, categorize visitors by location/browser

**[`anonymize_monitor_logs.py`](anonymize_monitor_logs.py "anonymize_monitor_logs.py")**: Anonymize logs for redistribution

Removes sensitive data (IPs, user agents, session IDs) while preserving query/response content:

```bash
uv run python src/analysis/anonymize_monitor_logs.py \
  --input reports/monitor-logs \
  --output reports/monitor-logs-anon \
  --zip
```

Options:
- `--dry-run`: Preview without writing
- `--limit N`: Process only N files
- `--zip`: Create compressed archive in `reports/`

Output includes: `METADATA.json`, `SCHEMA.md`, `CHECKSUMS.sha256`

## Makefile Details

### MPLBACKEND Environment Variable

`MPLBACKEND` selects the Matplotlib rendering backend:
- `Agg` (Makefile default): Non-interactive, headless backend for reliable PNG generation in CI/servers
- Interactive backends (`QtAgg`, `TkAgg`): Require GUI/display

Override when needed:
```bash
make MPLBACKEND=QtAgg figures
```

### Cleaning Outputs

```bash
make clean-figures  # Remove generated PNG files
make clean-csv      # Remove generated CSV files
make clean-stats    # Remove generated summary text files
```

## Adding New Analysis Scripts

1. Create your script in `src/analysis/` (e.g., `fig_newviz.py`)
2. Import from `logloader`: `from logloader import events_df, sessions`
3. Add output file to appropriate Makefile variable (`FIGURES`, `CSVS`, or `STATS`)
4. Add target with dependencies:
   ```makefile
   $(REPORT_DIR)/new_output.png: $(SRC_ANALYSIS)/fig_newviz.py $(SRC_ANALYSIS)/logloader.py | $(REPORT_DIR)
       MPLBACKEND=$(MPLBACKEND) $(RUNPY) $(SRC_ANALYSIS)/fig_newviz.py
       @test -f $@
   ```

## Maintainer

Minh Ha-Duong <minh.ha-duong@cnrs.fr>

Last updated: December 2025
