# CIRED.digital — Beta Dashboard (One‑Shot, In‑Memory)

Prepared by ChatGPT prompté par Ha‑Duong Minh
Date: 2025‑10‑17

## Scope & Constraints
- **Objective:** Single, reproducible analysis pass of beta usage (no DB, no cadence).
- **Data:** JSON monitor logs → normalized CSV/Parquet via `analyze_monitor_logs.py`.
- **Time window:** **Beta only: 2025‑07‑01 → 2025‑09‑30** (Europe/Paris).
- **Exclusions:** Development/testing traffic excluded via rules below.
- **Runtime model:** In‑memory (fits in RAM); deterministic run from a config file.

## Global Filters & Rules
- **Time filter:** include events with local timestamp in `[2025‑07‑01, 2025‑09‑30]` (Europe/Paris). For files with only UTC timestamps, convert to local first.
- **Session boundary:** include sessions that start within the beta window; optionally keep spillover events in same session.
- **Devs/testers exclusion (apply all that match):**
  - Known dev session IDs (prefixes) or test folders (regex): `dev_.*`, `test_.*` if present in `sessionId` or `source_file`.
  - Queries containing boilerplate/dev text: `^test$`, `lorem`, `foo`, `bar`, `asdf`, `qwerty`.
  - User agents or provenance known as CI/CD monitors and bots (if present in payload_unknown_json): `uptime|crawler|monitor|bot` (case‑insensitive).
  - Extremely high event frequency sessions (> 120 events/hour) with zero `request/response` pairs.
- **Bots:** Treat as excluded for metrics; provide a side table if needed.

## Outputs (deliverables for coding agent)
1. **Interactive dashboard app** (single file): supports subsetting and regenerates all visuals.
2. **Static report export**: PDF/HTML snapshot from the same app state.
3. **Reproducible run config**: `analysis_config.yaml` (see template).

---

## 1) Executive Dashboard (KPI Snapshot)
**Purpose:** quick read for project owners (beta only).

**KPIs**
- **Unique users (approx.)**: proxy via `sessionId` de‑dup within period.
- **Sessions**: count of `sessionStart` (or distinct `sessionId` if no explicit start).
- **Total queries** and **Query success rate**: `% queries with results > 0 or with subsequent investigation/request`.
- **Top 10 publications** by investigations; show HAL link if available.
- **Avg session duration** (sessionEnd - sessionStart) and **Avg depth** (events/session).
- **Feedback rate** (#feedback / 100 sessions) and **sentiment** (if detected).

**Controls**
- Time range (date picker restricted to beta window)
- Provenance (CIRED, RENATER, Public)
- Access method (Web, Mobile, API if present)
- Include/exclude spillover sessions

**Implementation (in‑memory)**
- Compute metrics from normalized CSV with columns suggested by `analyze_monitor_logs.py`:
  - Core: `sessionId`, `timestamp`, `eventType`, `query`, `retrievalTime`, `generationTime`, `response`, `comment`, `payload_unknown_json`, `source_file`.
  - Derive `local_dt` from `timestamp` using Europe/Paris tz.
  - Flag sessions/events as excluded by the rules above; filter before KPI computation.
- Visuals: small KPI cards; trend line for sessions/queries across the selected time.

---

## 2) Traffic & Engagement
**Purpose:** characterize visit patterns.

**Charts**
- **Sessions by day/week** (time series), segmented by provenance.
- **Visit length histogram**: buckets `<1, 1–3, 3–5, 5–10, 10–30, >30 min`.
- **Visit depth histogram**: clicks per visit (0–2, 3–5, 6–10, 11–20, >20).
- **Funnel**: `session → query → investigation → request` (counts and conversion).

**Controls**
- Time range, provenance, access method, include/exclude bots.
- Toggle “spillover sessions” handling.

**Implementation**
- Session duration: difference between first and last event in session (or explicit start/end if present).
- Depth: count of events per session; optionally only user‑initiated types (`request`, `article`, `response`, `userInput`).
- Funnel: pivot from event types in filtered data; define investigation as presence of `article`/view‑type event; request as HAL click or pdf download (from known fields or `payload_unknown_json`).

---

## 3) Query Intelligence
**Purpose:** understand questions and serve them better.

**Views**
- **Searchable table** of queries (timestamp, text, results count if any, clicked items if present, session link).
- **Top terms** word cloud / bar chart.
- **Zero‑result queries** (or no subsequent investigation) with counts.
- **Theme mapping** (optional): simple keyword mapping file `cired_themes.csv` for a first pass.

**Controls**
- Time range, provenance, language (if detectable), success=Yes/No.

**Implementation**
- Use `query` column; `results_count` proxied by whether a response followed with `retrievalTime` or `generationTime`, or a subsequent investigation/request within same session.
- Language detection optional (fasttext/compact model) if agent includes it; otherwise skip.
- For theme mapping, allow agent to read a CSV with `keyword,theme` and perform case‑insensitive contains on queries.

---

## 4) Content Performance
**Purpose:** what gets viewed/downloaded and how it’s discovered.

**Views**
- **Top publications**: by investigations and by requests.
- **By theme / data type / YOP** (if available from metadata join).
- **Discovery paths**: “queries → publications” table; simple co‑access pairs (“users who viewed X also viewed Y”).

**Controls**
- Time range, theme, data type, YOP.

**Implementation**
- Publication ID: from `article`/`response` payloads if present; else parse `payload_unknown_json` for HAL IDs/URLs.
- Co‑access: for each session, produce all unordered pairs of publications viewed; aggregate counts; show top pairs.

---

## Derived Fields & Normalization Notes
- **local_dt**: `timestamp` converted to `Europe/Paris`.
- **is_beta_period**: `2025‑07‑01 ≤ local_dt.date ≤ 2025‑09‑30`.
- **is_spillover**: events in sessions that start in beta but event time outside range.
- **is_dev_test**: boolean from exclusion rules (regex on sessionId/source_file/query and bot UA terms).
- **is_bot**: from payload heuristics or separate bot list.
- **is_query_success**: response present OR subsequent investigation/request within same session.
- **session_duration_sec**: per session; clamp negatives; exclude > 8h as outliers.
- **click_depth**: events per session (optionally only a whitelist).

## Reproducible Run (no DB)
1. Generate normalized CSV/Parquet:
   ```bash
   python analyze_monitor_logs.py reports/monitor-logs --out monitor_analysis
   ```
2. Run dashboard app with config:
   ```bash
   python beta_dashboard_app.py --config analysis_config.yaml --csv monitor_analysis.csv
   ```

## Agent Implementation Requirements
- **Language:** Python 3.11+
- **UI Framework:** Streamlit *or* Panel (Bokeh); charts with Plotly or Altair.
- **Data:** Pandas in‑memory DataFrame; no external DB.
- **State:** All filters applied in memory; download buttons for CSV/PNG/PDF exports.
- **Rebuild:** “Recompute all” button that re‑applies filters and regenerates visuals.
- **Determinism:** No randomness unless seeded and recorded in the session state.
- **Performance:** Target <1s interactions on ~5k–50k rows.

## File Inputs for the Agent
- **`monitor_analysis.csv`**: normalized events (columns from `analyze_monitor_logs.py`).
- **`analysis_config.yaml`**: time window, exclusions, display options.
- **(Optional) `cired_themes.csv`**: minimal keyword→theme map.
- **(Optional) `publications_meta.csv`**: HAL metadata to enrich publication views.

## Validation & Sanity Checks
- Print total rows in → rows after time filter → rows after dev/bot exclusion.
- Cross‑tab event types to match the known distribution in beta.
- Sample 20 queries and show their session timelines for manual inspection.
