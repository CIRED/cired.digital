#!/usr/bin/env python3
"""
analyze_token_usage.py — Analyze token counts from monitor logs.

This script extracts and analyzes token usage (input/output) per query,
including model, timing information, and costs.

Usage:
    python analyze_token_usage.py /path/to/monitor-logs --out token_analysis.csv
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


def extract_token_info(response_file: Path) -> dict[str, Any] | None:
    """
    Extract token and timing information from a response JSON file.

    Args:
        response_file: Path to a *-response.json file

    Returns:
        Dictionary with token and timing info, or None if parsing fails

    """
    try:
        data = json.loads(response_file.read_text(encoding="utf-8"))

        # Extract basic info
        session_id = data.get("sessionId", "")
        timestamp = data.get("timestamp", "")
        payload = data.get("payload", {})

        # Extract query ID and timing
        query_id = payload.get("queryId", "")
        retrieval_time = payload.get("retrievalTime", 0)
        generation_time = payload.get("generationTime", 0)

        # Extract token usage from response.results.metadata.usage
        response_data = payload.get("response", {})
        results = response_data.get("results", {})
        metadata = results.get("metadata", {})
        usage = metadata.get("usage", {})

        # prompt_tokens are not available in response files (will be cross-referenced with Mistral console)
        prompt_tokens = None  # NA
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = None  # NA (cannot calculate without prompt_tokens)

        # Try to find the corresponding request file to get model and query
        request_file = find_corresponding_request(response_file, query_id)
        model = None
        query_text = None

        if request_file and request_file.exists():
            try:
                request_data = json.loads(request_file.read_text(encoding="utf-8"))
                request_payload = request_data.get("payload", {})
                settings = request_payload.get("settings", {})
                model = settings.get("model", "unknown")
                query_text = request_payload.get("query", "")
            except Exception:
                pass

        # Parse timestamp
        try:
            if timestamp.endswith("Z"):
                ts_str = timestamp[:-1]
            else:
                ts_str = timestamp
            # Handle the compact format: 20250721T073947330Z
            if "T" in ts_str and len(ts_str) >= 15:
                dt = datetime.strptime(ts_str[:15], "%Y%m%dT%H%M%S")
            else:
                dt = datetime.fromisoformat(ts_str)
        except Exception:
            dt = None

        return {
            "session_id": session_id,
            "query_id": query_id,
            "timestamp": timestamp,
            "datetime": dt,
            "query": query_text,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "retrieval_time_ms": retrieval_time,
            "generation_time_ms": generation_time,
            "total_time_ms": retrieval_time + generation_time,
            "source_file": str(response_file),
        }

    except Exception as e:
        print(f"Error processing {response_file}: {e}")
        return None


def find_corresponding_request(response_file: Path, query_id: str) -> Path | None:
    """Find the request file that corresponds to a response file."""
    # Request files are in the same directory with the same session prefix
    parent_dir = response_file.parent

    # Try to find request file with the same query ID in the name or content
    for request_file in parent_dir.glob("*-request.json"):
        try:
            data = json.loads(request_file.read_text(encoding="utf-8"))
            if data.get("payload", {}).get("queryId") == query_id:
                return request_file
        except Exception:
            continue

    return None


def analyze_tokens(logs_root: Path) -> pd.DataFrame:
    """
    Analyze token usage from all response files in the monitor logs.

    Args:
        logs_root: Root directory of monitor logs

    Returns:
        DataFrame with token usage analysis

    """
    records = []

    # Find all response files
    response_files = list(logs_root.rglob("*-response.json"))
    print(f"Found {len(response_files)} response files")

    for response_file in response_files:
        info = extract_token_info(response_file)
        if info:
            records.append(info)

    if not records:
        print("No token data found!")
        return pd.DataFrame()

    df = pd.DataFrame(records)

    # Sort by datetime
    if "datetime" in df.columns and df["datetime"].notna().any():
        df = df.sort_values("datetime")

    return df


def print_summary(df: pd.DataFrame) -> None:
    """Print summary statistics of token usage."""
    if df.empty:
        print("No data to summarize")
        return

    print("\n" + "=" * 80)
    print("TOKEN USAGE SUMMARY")
    print("=" * 80)

    print(f"\nTotal queries analyzed: {len(df)}")
    if df["datetime"].notna().any():
        print(f"Date range: {df['datetime'].min()} to {df['datetime'].max()}")

    print("\n--- Token Counts ---")
    # Handle NA values - only sum/average if there are non-NA values
    if df["prompt_tokens"].notna().any():
        print(f"Total input tokens: {df['prompt_tokens'].sum():,}")
        print(f"Average input tokens per query: {df['prompt_tokens'].mean():.1f}")
        print(f"Median input tokens: {df['prompt_tokens'].median():.0f}")
    else:
        print("Input tokens: Not available")

    if df["completion_tokens"].notna().any():
        print(f"\nTotal output tokens: {df['completion_tokens'].sum():,}")
        print(f"Average output tokens per query: {df['completion_tokens'].mean():.1f}")
        print(f"Median output tokens: {df['completion_tokens'].median():.0f}")
    else:
        print("\nOutput tokens: Not available")

    if df["total_tokens"].notna().any():
        print(f"\nTotal tokens: {df['total_tokens'].sum():,}")
        print(f"Average total tokens per query: {df['total_tokens'].mean():.1f}")
    else:
        print("\nTotal tokens: Not available")

    print("\n--- Timing ---")
    if df["retrieval_time_ms"].notna().any():
        print(f"Average retrieval time: {df['retrieval_time_ms'].mean():.0f} ms")
    if df["generation_time_ms"].notna().any():
        print(f"Average generation time: {df['generation_time_ms'].mean():.0f} ms")
    if df["total_time_ms"].notna().any():
        print(f"Average total time: {df['total_time_ms'].mean():.0f} ms")

    if "model" in df.columns and df["model"].notna().any():
        print("\n--- By Model ---")
        agg_dict = {"query_id": "count"}

        # Only include columns that have non-NA values
        if df["prompt_tokens"].notna().any():
            agg_dict["prompt_tokens"] = ["sum", "mean"]
        if df["completion_tokens"].notna().any():
            agg_dict["completion_tokens"] = ["sum", "mean"]
        if df["total_tokens"].notna().any():
            agg_dict["total_tokens"] = ["sum", "mean"]
        if df["total_time_ms"].notna().any():
            agg_dict["total_time_ms"] = "mean"

        model_stats = df.groupby("model").agg(agg_dict).round(1)
        print(model_stats)

    print("\n--- Top 10 Queries by Output Tokens ---")
    if (
        "query" in df.columns
        and df["query"].notna().any()
        and df["completion_tokens"].notna().any()
    ):
        cols = ["query", "model", "completion_tokens", "total_time_ms"]
        # Only include prompt_tokens and total_tokens if they have values
        if df["prompt_tokens"].notna().any():
            cols.insert(2, "prompt_tokens")
        if df["total_tokens"].notna().any():
            cols.insert(-1, "total_tokens")

        top_queries = df.nlargest(10, "completion_tokens")[cols]
        print(top_queries.to_string(index=False, max_colwidth=60))


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze token usage from monitor logs"
    )
    parser.add_argument(
        "logs_root", type=Path, help="Path to the monitor-logs root directory"
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("token_analysis.csv"),
        help="Output CSV file path (default: token_analysis.csv)",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Only print summary, don't write CSV",
    )

    args = parser.parse_args()

    if not args.logs_root.exists():
        print(f"Error: {args.logs_root} does not exist")
        return

    print(f"Analyzing token usage from: {args.logs_root}")
    df = analyze_tokens(args.logs_root)

    if df.empty:
        print("No token data found in the logs")
        return

    # Print summary
    print_summary(df)

    # Write CSV
    if not args.summary_only:
        df.to_csv(args.out, index=False)
        print(f"\n{'=' * 80}")
        print(f"Detailed results written to: {args.out}")
        print(f"Columns: {', '.join(df.columns)}")
        print(f"{'=' * 80}")


if __name__ == "__main__":
    main()
