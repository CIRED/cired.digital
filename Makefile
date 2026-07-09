# Build analysis figures into reports/analysis
# Usage:
#   make figures
#   make clean-figures
#
# Override RUNPY if needed, e.g.
#   make RUNPY="python3" figures
#   make RUNPY="poetry run python" figures

RUNPY ?= uv run python
# MPLBACKEND selects the Matplotlib rendering backend.
# - Default Agg = headless/non-interactive (reliable in CI, servers, containers).
# - Using an interactive backend (e.g. QtAgg/TkAgg) requires a working GUI/display.
# In this Makefile we force a backend so figure generation doesn't try to open a window.
# Override if you know what you're doing:
#   make MPLBACKEND=QtAgg figures
MPLBACKEND ?= Agg

PROJECT_ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
SRC_ANALYSIS := $(PROJECT_ROOT)/src/analysis
REPORT_DIR := $(PROJECT_ROOT)/reports/analysis
LOGS_ROOT ?= $(PROJECT_ROOT)/reports/monitor-logs

FIGURES := \
	$(REPORT_DIR)/viz1_session_activity_timeline.png \
	$(REPORT_DIR)/visitors_origin.png \
	$(REPORT_DIR)/session_event_type_transitions.png \
	$(REPORT_DIR)/session_event_type_transitions_simplified.png

CSVS := \
	$(REPORT_DIR)/Queries.csv \
	$(REPORT_DIR)/UniqueQueries.csv \
	$(REPORT_DIR)/token_analysis.csv \
	$(REPORT_DIR)/token_analysis_monthly.csv \
	$(REPORT_DIR)/article_analysis.csv \
	$(REPORT_DIR)/article_analysis_monthly.csv

STATS := \
	$(REPORT_DIR)/describe_events_summary.txt \
	$(REPORT_DIR)/describe_sessions_summary.txt


REFERENCE_DIR ?= $(HOME)/CNRS/papiers/sent/CIRED.digital final report/fig

REFERENCE_FIGURES := \
	viz1_session_activity_timeline.png \
	visitors_origin.png \
	session_event_type_transitions.png \
	session_event_type_transitions_simplified.png

ANON_DIR := $(PROJECT_ROOT)/reports/monitor-logs-anon
ANON_ZIP := $(PROJECT_ROOT)/reports/monitor-logs-anon_$(shell date -u +%Y%m%d).zip

.PHONY: figures csv stats analysis dataset clean-figures clean-csv clean-stats test

figures: $(FIGURES)

csv: $(CSVS)

stats: $(STATS)

analysis: figures csv stats

$(REPORT_DIR):
	mkdir -p $@

$(REPORT_DIR)/viz1_session_activity_timeline.png: $(SRC_ANALYSIS)/fig_activity.py $(SRC_ANALYSIS)/logloader.py | $(REPORT_DIR)
	LOGS_ROOT=$(LOGS_ROOT) MPLBACKEND=$(MPLBACKEND) $(RUNPY) $(SRC_ANALYSIS)/fig_activity.py
	@test -f $@

$(REPORT_DIR)/visitors_origin.png: $(SRC_ANALYSIS)/fig_provenance.py $(SRC_ANALYSIS)/logloader.py | $(REPORT_DIR)
	LOGS_ROOT=$(LOGS_ROOT) MPLBACKEND=$(MPLBACKEND) $(RUNPY) $(SRC_ANALYSIS)/fig_provenance.py
	@test -f $@

$(REPORT_DIR)/session_event_type_transitions.png: $(SRC_ANALYSIS)/fig_sessions.py $(SRC_ANALYSIS)/logloader.py | $(REPORT_DIR)
	LOGS_ROOT=$(LOGS_ROOT) MPLBACKEND=$(MPLBACKEND) $(RUNPY) $(SRC_ANALYSIS)/fig_sessions.py
	@test -f $@

$(REPORT_DIR)/session_event_type_transitions_simplified.png: $(REPORT_DIR)/session_event_type_transitions.png
	@test -f $@

$(REPORT_DIR)/Queries.csv: $(SRC_ANALYSIS)/tabulate_queries.py $(SRC_ANALYSIS)/logloader.py | $(REPORT_DIR)
	LOGS_ROOT=$(LOGS_ROOT) $(RUNPY) $(SRC_ANALYSIS)/tabulate_queries.py
	@test -f $@

$(REPORT_DIR)/UniqueQueries.csv: $(REPORT_DIR)/Queries.csv
	@test -f $@

$(REPORT_DIR)/token_analysis.csv: $(SRC_ANALYSIS)/tabulate_tokens.py | $(REPORT_DIR)
	$(RUNPY) $(SRC_ANALYSIS)/tabulate_tokens.py $(LOGS_ROOT) --out $@
	@test -f $@

$(REPORT_DIR)/token_analysis_monthly.csv: $(REPORT_DIR)/token_analysis.csv
	@test -f $@

$(REPORT_DIR)/article_analysis.csv: $(SRC_ANALYSIS)/tabulate_articles.py | $(REPORT_DIR)
	$(RUNPY) $(SRC_ANALYSIS)/tabulate_articles.py $(LOGS_ROOT) --out $@
	@test -f $@

$(REPORT_DIR)/article_analysis_monthly.csv: $(REPORT_DIR)/article_analysis.csv
	@test -f $@

$(REPORT_DIR)/describe_events_summary.txt: $(SRC_ANALYSIS)/describe_events.py $(SRC_ANALYSIS)/logloader.py | $(REPORT_DIR)
	LOGS_ROOT=$(LOGS_ROOT) $(RUNPY) $(SRC_ANALYSIS)/describe_events.py > $@

$(REPORT_DIR)/describe_sessions_summary.txt: $(SRC_ANALYSIS)/describe_sessions.py $(SRC_ANALYSIS)/logloader.py | $(REPORT_DIR)
	LOGS_ROOT=$(LOGS_ROOT) $(RUNPY) $(SRC_ANALYSIS)/describe_sessions.py > $@

dataset:
	rm -rf $(ANON_DIR)
	$(RUNPY) $(SRC_ANALYSIS)/anonymize_monitor_logs.py \
		--input $(LOGS_ROOT) --output $(ANON_DIR) --zip
	@echo "Dataset archive: $$(ls $(PROJECT_ROOT)/reports/monitor-logs-anon_*.zip)"

test: analysis
	@fail=0; \
	for f in $(REFERENCE_FIGURES); do \
		if cmp -s "$(REFERENCE_DIR)/$$f" "$(REPORT_DIR)/$$f"; then \
			echo "PASS $$f"; \
		else \
			echo "FAIL $$f"; fail=1; \
		fi; \
	done; \
	[ $$fail -eq 0 ] && echo "All regression tests passed." || { echo "Regression test(s) failed."; exit 1; }

clean-figures:
	rm -f $(FIGURES)

clean-csv:
	rm -f $(CSVS)

clean-stats:
	rm -f $(STATS)

# --- Slides (MeSSH26) ---------------------------------------------------------
# Quarto -> Beamer (metropolis). Writing-side build: consumes committed figures
# in slides/slides-assets only, no data pipeline, no uv. To refresh those
# figures from logs, run `make figures` and copy the wanted PNGs into
# slides/slides-assets.
SLIDES_QMD := $(PROJECT_ROOT)/slides/slides-messh.qmd
SLIDES_PDF := $(PROJECT_ROOT)/slides/slides-messh.pdf
SLIDES_ASSETS := $(wildcard $(PROJECT_ROOT)/slides/slides-assets/*)

.PHONY: slides clean-slides
slides: $(SLIDES_PDF)

$(SLIDES_PDF): $(SLIDES_QMD) $(SLIDES_ASSETS)
	cd $(PROJECT_ROOT)/slides && quarto render slides-messh.qmd --to beamer

clean-slides:
	rm -f $(SLIDES_PDF)
