# CIRED.digital Beta Dashboard

Interactive analytics dashboard for analyzing CIRED.digital beta usage data (July-September 2025).

## Overview

The beta dashboard provides comprehensive analytics for the CIRED.digital chatbot beta period, including:

- **Executive Dashboard**: High-level KPIs and metrics
- **Traffic & Engagement**: Session patterns, visit length/depth, conversion funnels
- **Query Intelligence**: Query analysis, top terms, zero-result queries
- **Content Performance**: Publication views, co-access patterns

## Architecture

The analysis system consists of three components:

1. **Data Normalization** (`analyze_monitor_logs.py`): Processes raw JSON monitor logs into normalized CSV/Parquet
2. **Configuration** (`analysis_config.yaml`): Defines time windows, exclusion rules, and display options
3. **Dashboard App** (`beta_dashboard_app.py`): Interactive Streamlit application for data exploration

## Prerequisites

Ensure you have the required dependencies installed:

```bash
cd ~/repos/cired.digital
source .venv/bin/activate
uv pip install -e ".[dev]"
```

The dashboard requires:
- Python 3.11+
- streamlit >= 1.28.0
- plotly >= 5.0.0
- pandas
- pyarrow

## Data Preparation

### Step 1: Normalize Monitor Logs

If you have raw JSON monitor logs in `reports/monitor-logs/`, normalize them first:

```bash
python src/analysis/analyze_monitor_logs.py reports/monitor-logs \
    --schema src/monitor/models.py \
    --out data/prepared/monitor_analysis
```

This creates:
- `data/prepared/monitor_analysis.csv` - Normalized event data
- `data/prepared/monitor_analysis.parquet` - Fast-loading binary format
- `data/prepared/monitor_analysis.md` - Quick summary statistics

### Step 2: Review Configuration

Edit `src/analysis/analysis_config.yaml` to adjust:
- Time window (default: 2025-07-01 to 2025-09-30)
- Exclusion rules for dev/test traffic
- Display options and chart selections

## Running the Dashboard

### Basic Usage

```bash
cd ~/repos/cired.digital
source .venv/bin/activate
streamlit run src/analysis/beta_dashboard_app.py -- \
    --config src/analysis/analysis_config.yaml \
    --csv data/prepared/monitor_analysis.parquet
```

The dashboard will open in your browser at `http://localhost:8501`

### Command-Line Options

```bash
streamlit run src/analysis/beta_dashboard_app.py -- \
    --config <path-to-config.yaml> \
    --csv <path-to-data-file>
```

- `--config`: Path to configuration YAML (default: `src/analysis/analysis_config.yaml`)
- `--csv`: Path to data file, supports CSV or Parquet (default: `data/prepared/monitor_analysis.parquet`)

## Dashboard Features

### Executive Dashboard

Key performance indicators:
- Unique sessions count
- Total queries submitted
- Query success rate (% of query sessions receiving responses)
- Average session duration
- Feedback rate (feedback per 100 sessions)
- Average events per session
- Daily sessions time series
- Top 10 publications by investigation

### Traffic & Engagement

Session behavior analysis:
- **Visit Length Distribution**: Histogram of session durations (<1 min, 1-3 min, etc.)
- **Visit Depth Distribution**: Histogram of events per session (0-2, 3-5, etc.)
- **Conversion Funnel**: User journey from sessions → queries → investigations → requests

### Query Intelligence

Query analysis tools:
- **Query Explorer**: Searchable table of all queries with timestamps and response status
- **Top Queries**: Most frequently asked questions
- **Zero-Result Queries**: Queries that didn't receive responses

### Content Performance

Publication analytics:
- **Top Publications**: Most viewed publications by HAL ID
- **Co-Access Analysis**: Publications frequently viewed together in the same session

## Filters and Controls

The sidebar provides filtering options:
- **Include spillover sessions**: Include/exclude sessions that started in beta but have events outside the time window
- **Event counts**: Shows data reduction at each filtering stage

## Data Export

Use the sidebar "Download Filtered Data (CSV)" button to export the currently filtered dataset for further analysis.

## Configuration Reference

### Time Window

```yaml
time:
  timezone: Europe/Paris
  start: 2025-07-01
  end: 2025-09-30
  include_spillover_sessions: true
```

### Exclusion Rules

```yaml
exclusions:
  exclude_bots: true
  dev_session_prefixes:
    - "dev_"
    - "test_"
  source_file_regex_any:
    - "/dev/"
    - "/tests?/"
  query_regex_any:
    - "^(?i)test$"
    - "(?i)lorem"
    - "(?i)foo|bar|asdf|qwerty"
  payload_useragent_regex_any:
    - "(?i)bot|crawler|spider|monitor|uptime"
  max_events_per_hour_without_requests: 120
```

## Troubleshooting

### Dashboard won't start

Ensure dependencies are installed:
```bash
source .venv/bin/activate
uv pip install streamlit plotly
```

### Data file not found

Verify the data file path:
```bash
ls -lh data/prepared/monitor_analysis.parquet
```

If missing, run the normalization script first (see Data Preparation above).

### Empty visualizations

Check the time window in `analysis_config.yaml` matches your data's timestamp range. The dashboard filters events to the beta period (July-September 2025) by default.

### Performance issues

For large datasets (>100k events):
- Use Parquet format instead of CSV (faster loading)
- Reduce the time window in the config
- Apply stricter exclusion rules

## Design Documentation

For detailed design specifications, see:
- `CIRED_digital_beta_dashboard_spec.md` - Complete dashboard specification
- `analysis_config.yaml` - Configuration schema and options

## Maintainer

Minh Ha-Duong <minh.ha-duong@cnrs.fr>

Last updated: October 2025
