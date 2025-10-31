"""
Load and process monitoring log files stored in a nested directory structure.

Exports:
- events_df: DataFrame with all individual events
- sessions: DataFrame with aggregated session-level metrics

Usage:
    from logloader import events_df, sessions
"""

import glob
import json
import os
from typing import Any

import pandas as pd

DEFAULT_BASE_PATH = "../../reports/monitor-logs"
DEFAULT_MIN_DATE = "20250705"


def load_all_log_files(
    base_path: str = DEFAULT_BASE_PATH, min_date: str = DEFAULT_MIN_DATE
) -> list[dict[str, Any]]:
    """
    Load all JSON files from the log directory structure.

    Handles the recursive YYYY/MM/DD/ folder structure.
    Each JSON file contains: sessionId, timestamp, eventType, payload, server_context.

    Args:
        base_path: Path to monitor-logs directory
        min_date: Only load files from this date onwards (format: YYYYMMDD, e.g., '20250705')

    Returns:
        list: List of event dictionaries

    """
    all_events: list[dict[str, Any]] = []
    file_count = 0
    error_count = 0
    skipped_count = 0

    # Use glob to find all JSON files recursively
    json_pattern = os.path.join(base_path, "**/*.json")
    json_files = glob.glob(json_pattern, recursive=True)

    print(f"Found {len(json_files)} JSON files total")
    if min_date:
        print(f"Filtering for files from {min_date} onwards\n")

    # Load each file
    for file_path in json_files:
        # Filter by date if min_date is specified
        if min_date:
            # Extract date from path: monitor-logs/YYYY/MM/DD/...
            path_parts = file_path.split(os.sep)
            if len(path_parts) >= 4:
                try:
                    year = path_parts[-4]
                    month = path_parts[-3]
                    day = path_parts[-2]
                    file_date = f"{year}{month}{day}"
                    if file_date < min_date:
                        skipped_count += 1
                        continue
                except (ValueError, IndexError):
                    pass

        try:
            with open(file_path) as f:
                event_data = json.load(f)

            # Validate required fields
            if all(
                key in event_data for key in ["sessionId", "timestamp", "eventType"]
            ):
                all_events.append(event_data)
                file_count += 1
            else:
                error_count += 1

        except (OSError, json.JSONDecodeError):
            error_count += 1

    print(f"Successfully loaded: {file_count} files")
    print(f"Skipped (before cutoff): {skipped_count} files")
    if error_count > 0:
        print(f"Errors encountered: {error_count} files")

    return all_events


def create_events_dataframe(all_events: list[dict[str, Any]]) -> pd.DataFrame:
    """
    Create and process the events DataFrame.

    Args:
        all_events: List of event dictionaries

    Returns:
        pd.DataFrame: Processed events DataFrame

    """
    print(f"\nTotal events loaded: {len(all_events)}")

    # Create DataFrame
    df = pd.DataFrame(all_events)

    if df.empty:
        print("WARNING: No events loaded, returning empty DataFrame")
        return df

    # Parse timestamp to datetime with error handling
    try:
        df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y%m%dT%H%M%S%fZ")
    except ValueError as e:
        print(
            f"Warning: Some timestamps couldn't be parsed with the expected format: {e}"
        )
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # Add derived columns for analysis
    df["date"] = df["timestamp"].dt.date
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.day_name()
    df["minute"] = df["timestamp"].dt.floor("1min")

    print(f"DataFrame created with shape: {df.shape}")
    print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")

    return df


def augment_dataframe(events_df: pd.DataFrame) -> None:
    """
    Augment the events DataFrame with additional features.

    Args:
        events_df: DataFrame to modify in place

    """
    # The query text for "request" event types
    events_df["query"] = [
        payload["query"] if etype == "request" else None
        for etype, payload in zip(events_df["eventType"], events_df["payload"])
    ]


def create_sessions_list(events_df: pd.DataFrame) -> list[dict[str, Any]]:
    """
    Create a list of sessions with aggregated metrics.

    Args:
        events_df: DataFrame of events

    Returns:
        List[Dict[str, Any]]: List of session dictionaries

    """
    sessions: list[dict[str, Any]] = []
    for session_id, group in events_df.groupby("sessionId"):
        session_dict: dict[str, Any] = {
            "sessionId": session_id,
            "start_time": group["timestamp"].min(),
            "end_time": group["timestamp"].max(),
            "event_count": len(group),
            "events": group.sort_values("timestamp").to_dict(orient="records"),
        }
        sessions.append(session_dict)

    print(f"\nTotal sessions created: {len(sessions)}")
    return sessions


# ============================================================================
# MODULE INITIALIZATION - Load data when module is imported
# ============================================================================

print("=" * 70)
print("Loading monitor logs...\n")

# Load all events
all_events = load_all_log_files()

# Create events DataFrame
events_df = create_events_dataframe(all_events)

# Augment DataFrame with additional features
if not events_df.empty:
    augment_dataframe(events_df)
    print("DataFrame augmented with query_text column")

# Create sessions DataFrame
sessions = create_sessions_list(events_df)

print("\n✓ Module loaded successfully")
print("=" * 70)
