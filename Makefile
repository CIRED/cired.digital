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

FIGURES := \
	$(REPORT_DIR)/viz1_session_activity_timeline.png \
	$(REPORT_DIR)/visitors_origin.png \
	$(REPORT_DIR)/session_event_type_transitions.png \
	$(REPORT_DIR)/session_event_type_transitions_simplified.png

.PHONY: figures clean-figures

figures: $(FIGURES)

$(REPORT_DIR):
	mkdir -p $@

$(REPORT_DIR)/viz1_session_activity_timeline.png: $(SRC_ANALYSIS)/fig_activity.py $(SRC_ANALYSIS)/logloader.py | $(REPORT_DIR)
	MPLBACKEND=$(MPLBACKEND) $(RUNPY) $(SRC_ANALYSIS)/fig_activity.py
	@test -f $@

$(REPORT_DIR)/visitors_origin.png: $(SRC_ANALYSIS)/fig_provenance.py $(SRC_ANALYSIS)/logloader.py | $(REPORT_DIR)
	MPLBACKEND=$(MPLBACKEND) $(RUNPY) $(SRC_ANALYSIS)/fig_provenance.py
	@test -f $@

$(REPORT_DIR)/session_event_type_transitions.png: $(SRC_ANALYSIS)/fig_sessions.py $(SRC_ANALYSIS)/logloader.py | $(REPORT_DIR)
	MPLBACKEND=$(MPLBACKEND) $(RUNPY) $(SRC_ANALYSIS)/fig_sessions.py
	@test -f $@

$(REPORT_DIR)/session_event_type_transitions_simplified.png: $(REPORT_DIR)/session_event_type_transitions.png
	@test -f $@

clean-figures:
	rm -f $(FIGURES)
