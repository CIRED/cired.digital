#!/usr/bin/env python3
"""
beta_dashboard_app.py — Interactive dashboard for CIRED.digital beta analysis.

Usage:
    streamlit run beta_dashboard_app.py -- --config analysis_config.yaml --csv monitor_analysis.csv

Features:
    - Executive KPI dashboard
    - Traffic & engagement analysis
    - Query intelligence
    - Content performance metrics
"""

import argparse
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yaml


def load_config(config_path: Path) -> dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_path, encoding="utf-8") as f:
        config: dict[str, Any] = yaml.safe_load(f)
        return config


def load_data(csv_path: Path) -> pd.DataFrame:
    """Load and prepare data from CSV or Parquet file."""
    if csv_path.suffix == ".parquet":
        df = pd.read_parquet(csv_path)
    else:
        df = pd.read_csv(csv_path)

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def apply_time_filter(
    df: pd.DataFrame, config: dict[str, Any], include_spillover: bool
) -> pd.DataFrame:
    """Apply time window filter based on config."""
    tz = ZoneInfo(config["time"]["timezone"])
    start_date = datetime.fromisoformat(str(config["time"]["start"])).replace(tzinfo=tz)
    end_date = datetime.fromisoformat(str(config["time"]["end"])).replace(
        hour=23, minute=59, second=59, tzinfo=tz
    )

    df["local_dt"] = df["timestamp"].dt.tz_convert(tz)
    df["is_beta_period"] = (df["local_dt"] >= start_date) & (df["local_dt"] <= end_date)

    if include_spillover:
        session_starts = df[df["is_beta_period"]].groupby("sessionId")["local_dt"].min()
        beta_sessions = set(session_starts.index)
        return df[df["sessionId"].isin(beta_sessions)].copy()
    else:
        return df[df["is_beta_period"]].copy()


def apply_exclusions(df: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    """Apply exclusion rules for dev/test traffic and bots."""
    exclusions = config.get("exclusions", {})
    df["is_excluded"] = False

    for prefix in exclusions.get("dev_session_prefixes", []):
        df.loc[df["sessionId"].str.startswith(prefix, na=False), "is_excluded"] = True

    for pattern in exclusions.get("source_file_regex_any", []):
        clean_pattern = re.sub(r"\(\?[iLmsux]+\)", "", pattern)
        df.loc[
            df["source_file"].str.contains(
                clean_pattern, case=False, na=False, regex=True
            ),
            "is_excluded",
        ] = True

    for pattern in exclusions.get("query_regex_any", []):
        clean_pattern = re.sub(r"\(\?[iLmsux]+\)", "", pattern)
        df.loc[
            df["query"].str.contains(clean_pattern, case=False, na=False, regex=True),
            "is_excluded",
        ] = True

    for pattern in exclusions.get("payload_useragent_regex_any", []):
        clean_pattern = re.sub(r"\(\?[iLmsux]+\)", "", pattern)
        df.loc[
            df["payload_unknown_json"].str.contains(
                clean_pattern, case=False, na=False, regex=True
            ),
            "is_excluded",
        ] = True

    return df[~df["is_excluded"]].copy()


def compute_session_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute session-level metrics."""
    session_data = []

    for session_id, group in df.groupby("sessionId"):
        first_event = group["local_dt"].min()
        last_event = group["local_dt"].max()
        duration_sec = (last_event - first_event).total_seconds()

        duration_sec = max(0, min(duration_sec, 8 * 3600))

        session_data.append(
            {
                "sessionId": session_id,
                "start_time": first_event,
                "end_time": last_event,
                "duration_sec": duration_sec,
                "event_count": len(group),
                "query_count": group["query"].notna().sum(),
                "has_feedback": group["comment"].notna().any(),
            }
        )

    return pd.DataFrame(session_data)


def render_executive_dashboard(df: pd.DataFrame, session_df: pd.DataFrame) -> None:
    """Render executive KPI dashboard."""
    st.header("Executive Dashboard")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Unique Sessions", len(session_df))

    with col2:
        total_queries = df["query"].notna().sum()
        st.metric("Total Queries", total_queries)

    with col3:
        query_sessions = df[df["query"].notna()]["sessionId"].unique()
        sessions_with_response = df[
            df["sessionId"].isin(query_sessions) & df["response"].notna()
        ]["sessionId"].nunique()
        success_rate = (
            (sessions_with_response / len(query_sessions) * 100)
            if len(query_sessions) > 0
            else 0
        )
        st.metric("Query Success Rate", f"{success_rate:.1f}%")

    with col4:
        avg_duration = session_df["duration_sec"].mean() / 60
        st.metric("Avg Session Duration", f"{avg_duration:.1f} min")

    col5, col6 = st.columns(2)

    with col5:
        feedback_count = session_df["has_feedback"].sum()
        feedback_rate = (
            (feedback_count / len(session_df) * 100) if len(session_df) > 0 else 0
        )
        st.metric("Feedback Rate", f"{feedback_rate:.1f}%")

    with col6:
        avg_depth = session_df["event_count"].mean()
        st.metric("Avg Events/Session", f"{avg_depth:.1f}")

    st.subheader("Sessions Over Time")
    daily_sessions = (
        session_df.set_index("start_time")
        .resample("D")["sessionId"]
        .count()
        .reset_index()
    )
    daily_sessions.columns = ["Date", "Sessions"]

    fig = px.line(
        daily_sessions,
        x="Date",
        y="Sessions",
        title="Daily Sessions",
        markers=True,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top Publications by Investigation")
    article_events = df[df["eventType"] == "article"]
    if not article_events.empty:
        top_articles = article_events["payload_json"].value_counts().head(10)
        if not top_articles.empty:
            st.dataframe(
                pd.DataFrame(
                    {"Publication": top_articles.index, "Views": top_articles.values}
                ),
                use_container_width=True,
            )
    else:
        st.info("No article investigation data available")


def render_traffic_engagement(df: pd.DataFrame, session_df: pd.DataFrame) -> None:
    """Render traffic and engagement analysis."""
    st.header("Traffic & Engagement")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Visit Length Distribution")
        session_df["duration_min"] = session_df["duration_sec"] / 60
        session_df["duration_bucket"] = pd.cut(
            session_df["duration_min"],
            bins=[0, 1, 3, 5, 10, 30, float("inf")],
            labels=["<1 min", "1-3 min", "3-5 min", "5-10 min", "10-30 min", ">30 min"],
        )
        duration_counts = session_df["duration_bucket"].value_counts().sort_index()

        fig = px.bar(
            x=duration_counts.index.astype(str),
            y=duration_counts.values,
            labels={"x": "Duration", "y": "Sessions"},
            title="Session Duration Distribution",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Visit Depth Distribution")
        session_df["depth_bucket"] = pd.cut(
            session_df["event_count"],
            bins=[0, 2, 5, 10, 20, float("inf")],
            labels=["0-2", "3-5", "6-10", "11-20", ">20"],
        )
        depth_counts = session_df["depth_bucket"].value_counts().sort_index()

        fig = px.bar(
            x=depth_counts.index.astype(str),
            y=depth_counts.values,
            labels={"x": "Events per Session", "y": "Sessions"},
            title="Session Depth Distribution",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Conversion Funnel")
    funnel_data = {
        "Stage": ["Sessions", "Queries", "Investigations", "Requests"],
        "Count": [
            len(session_df),
            df["query"].notna().sum(),
            df[df["eventType"] == "article"].shape[0],
            df[df["eventType"] == "request"].shape[0],
        ],
    }
    funnel_df = pd.DataFrame(funnel_data)

    fig = go.Figure(
        go.Funnel(
            y=funnel_df["Stage"],
            x=funnel_df["Count"],
            textinfo="value+percent initial",
        )
    )
    fig.update_layout(title="User Journey Funnel")
    st.plotly_chart(fig, use_container_width=True)


def render_query_intelligence(df: pd.DataFrame) -> None:
    """Render query intelligence analysis."""
    st.header("Query Intelligence")

    queries_df = df[df["query"].notna()][
        ["local_dt", "query", "sessionId", "response"]
    ].copy()
    queries_df["has_response"] = queries_df["response"].notna()

    st.subheader("Query Explorer")
    search_term = st.text_input("Search queries:", "")

    if search_term:
        filtered_queries = queries_df[
            queries_df["query"].str.contains(search_term, case=False, na=False)
        ]
    else:
        filtered_queries = queries_df

    st.dataframe(
        filtered_queries[["local_dt", "query", "has_response"]].head(100),
        use_container_width=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top Queries")
        top_queries = queries_df["query"].value_counts().head(20)
        st.dataframe(
            pd.DataFrame({"Query": top_queries.index, "Count": top_queries.values}),
            use_container_width=True,
        )

    with col2:
        st.subheader("Zero-Result Queries")
        zero_result = queries_df[~queries_df["has_response"]]
        if not zero_result.empty:
            zero_counts = zero_result["query"].value_counts().head(20)
            st.dataframe(
                pd.DataFrame({"Query": zero_counts.index, "Count": zero_counts.values}),
                use_container_width=True,
            )
        else:
            st.info("All queries received responses")


def render_content_performance(df: pd.DataFrame) -> None:
    """Render content performance analysis."""
    st.header("Content Performance")

    article_events = df[df["eventType"] == "article"]

    if article_events.empty:
        st.info("No article investigation data available")
        return

    st.subheader("Top Publications by Views")
    top_pubs = article_events["payload_json"].value_counts().head(20)

    fig = px.bar(
        x=top_pubs.values,
        y=top_pubs.index.astype(str),
        orientation="h",
        labels={"x": "Views", "y": "Publication"},
        title="Most Viewed Publications",
    )
    fig.update_layout(height=600, yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Co-Access Analysis")
    session_articles = (
        article_events.groupby("sessionId")["payload_json"].apply(list).reset_index()
    )

    co_access_pairs = []
    for articles in session_articles["payload_json"]:
        if len(articles) >= 2:
            unique_articles = list(set(articles))
            for i in range(len(unique_articles)):
                for j in range(i + 1, len(unique_articles)):
                    pair = tuple(sorted([unique_articles[i], unique_articles[j]]))
                    co_access_pairs.append(pair)

    if co_access_pairs:
        co_access_df = pd.DataFrame(co_access_pairs, columns=["Article1", "Article2"])
        co_access_counts = co_access_df.value_counts().head(10)

        st.dataframe(
            pd.DataFrame(
                {
                    "Article 1": [p[0] for p in co_access_counts.index],
                    "Article 2": [p[1] for p in co_access_counts.index],
                    "Co-views": co_access_counts.values,
                }
            ),
            use_container_width=True,
        )
    else:
        st.info("No co-access patterns found")


def main() -> None:
    """Run the main dashboard application."""
    st.set_page_config(
        page_title="CIRED.digital Beta Dashboard",
        page_icon="📊",
        layout="wide",
    )

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("src/analysis/analysis_config.yaml"),
        help="Path to config YAML",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("data/prepared/monitor_analysis.parquet"),
        help="Path to data file (CSV or Parquet)",
    )
    args = parser.parse_args()

    config = load_config(args.config)

    st.title(config.get("export", {}).get("default_report_title", "Beta Dashboard"))

    st.sidebar.header("Filters")

    if "df_raw" not in st.session_state:
        with st.spinner("Loading data..."):
            st.session_state.df_raw = load_data(args.csv)

    df_raw = st.session_state.df_raw

    include_spillover = st.sidebar.checkbox(
        "Include spillover sessions",
        value=config["time"].get("include_spillover_sessions", True),
    )

    df_filtered = apply_time_filter(df_raw, config, include_spillover)

    st.sidebar.metric("Total Events (Raw)", len(df_raw))
    st.sidebar.metric("Events After Time Filter", len(df_filtered))

    if config.get("exclusions", {}).get("exclude_bots", True):
        df_filtered = apply_exclusions(df_filtered, config)
        st.sidebar.metric("Events After Exclusions", len(df_filtered))

    session_df = compute_session_metrics(df_filtered)

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Executive",
            "Traffic & Engagement",
            "Query Intelligence",
            "Content Performance",
        ]
    )

    with tab1:
        render_executive_dashboard(df_filtered, session_df)

    with tab2:
        render_traffic_engagement(df_filtered, session_df)

    with tab3:
        render_query_intelligence(df_filtered)

    with tab4:
        render_content_performance(df_filtered)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Export")

    if st.sidebar.button("Download Filtered Data (CSV)"):
        csv_data = df_filtered.to_csv(index=False)
        st.sidebar.download_button(
            label="Download CSV",
            data=csv_data,
            file_name="filtered_monitor_data.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()
