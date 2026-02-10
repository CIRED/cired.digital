#!/usr/bin/env python3
"""
tabulate_articles.py — Analyze article generation logs.

This script extracts and analyzes article generation data including:
- Reported LLM costs and self-hosting costs
- Reply length in words
- Number of cited documents

Usage:
    python tabulate_articles.py /path/to/monitor-logs --out article_analysis.csv
"""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from bs4 import BeautifulSoup


def _reports_analysis_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "reports" / "analysis"


def _resolve_output_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    if path.parent == Path("."):
        return _reports_analysis_dir() / path.name
    return path


def extract_stats_from_html(html_content: str) -> dict[str, Any]:
    """
    Extract statistics from the generation-stats div in HTML content.

    Args:
        html_content: HTML content containing generation stats

    Returns:
        Dictionary with extracted statistics

    """
    stats: dict[str, int | float | None] = {
        "prompt_tokens": None,
        "completion_tokens": None,
        "llm_cost_cents": None,
        "self_hosting_cost_cents": None,
        "generation_time_sec": None,
    }

    # Parse generation-stats line
    # Format: "Tokens: 0 in, 2 918 out. LLM cost: 0.09 cent. Self hosting cost: 0.22 cent (H100 VPS hourly rate for 2.69s.)."
    stats_pattern = r"Tokens:\s*([\d,\s]+)\s*in,\s*([\d,\s]+)\s*out\.\s*LLM cost:\s*([\d.]+)\s*cent\.\s*Self hosting cost:\s*([\d.]+)\s*cent\s*\(.*?for\s*([\d.]+)s\.\)"

    match = re.search(stats_pattern, html_content)
    if match:
        # Remove spaces and commas from token counts
        prompt_tokens_str = match.group(1).replace(",", "").replace(" ", "")
        completion_tokens_str = match.group(2).replace(",", "").replace(" ", "")

        stats["prompt_tokens"] = int(prompt_tokens_str) if prompt_tokens_str else 0
        stats["completion_tokens"] = (
            int(completion_tokens_str) if completion_tokens_str else 0
        )
        stats["llm_cost_cents"] = float(match.group(3))
        stats["self_hosting_cost_cents"] = float(match.group(4))
        stats["generation_time_sec"] = float(match.group(5))

    return stats


def count_words_in_answer(html_content: str) -> int:
    """
    Count words in the generated answer (excluding bibliography).

    Args:
        html_content: HTML content

    Returns:
        Word count

    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove bibliography section
    for bib in soup.find_all("div", class_="bibliography-container"):
        bib.decompose()

    # Remove stats divs
    for div in soup.find_all(
        "div", class_=["attribution", "generation-stats", "settings-stats"]
    ):
        div.decompose()

    # Get text and count words
    text = soup.get_text(strip=True)
    words = text.split()
    return len(words)


def count_citations(html_content: str) -> dict[str, int]:
    """
    Count the number of citations and unique documents cited.

    Args:
        html_content: HTML content

    Returns:
        Dictionary with citation counts

    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Count citation brackets in the answer
    citation_brackets = soup.find_all("a", class_="citation-bracket")
    num_citations = len(citation_brackets)

    # Count unique documents in bibliography
    document_items = soup.find_all("div", class_="document-item")
    num_documents = len(document_items)

    return {
        "num_citations": num_citations,
        "num_documents": num_documents,
    }


def extract_article_info(article_file: Path) -> dict[str, Any] | None:
    """
    Extract information from an article JSON file.

    Args:
        article_file: Path to a *-article.json file

    Returns:
        Dictionary with article info, or None if parsing fails

    """
    try:
        data = json.loads(article_file.read_text(encoding="utf-8"))

        # Extract basic info
        session_id = data.get("sessionId", "")
        timestamp_str = data.get("timestamp", "")
        payload = data.get("payload", {})

        # Parse timestamp
        try:
            dt = datetime.strptime(timestamp_str, "%Y%m%dT%H%M%S%fZ")
        except Exception:
            dt = None

        # Extract query ID and HTML content
        query_id = payload.get("queryId", "")
        html_content = payload.get("htmlContent", "")

        if not html_content:
            return None

        # Extract query title from HTML (h2 tag)
        soup = BeautifulSoup(html_content, "html.parser")
        h2_tag = soup.find("h2")
        query = h2_tag.get_text(strip=True) if h2_tag else ""

        # Extract statistics
        stats = extract_stats_from_html(html_content)
        word_count = count_words_in_answer(html_content)
        citation_counts = count_citations(html_content)

        return {
            "session_id": session_id,
            "query_id": query_id,
            "datetime": dt,
            "query": query,
            "word_count": word_count,
            "num_citations": citation_counts["num_citations"],
            "num_documents": citation_counts["num_documents"],
            "prompt_tokens": stats["prompt_tokens"],
            "completion_tokens": stats["completion_tokens"],
            "llm_cost_cents": stats["llm_cost_cents"],
            "self_hosting_cost_cents": stats["self_hosting_cost_cents"],
            "total_cost_cents": (stats["llm_cost_cents"] or 0)
            + (stats["self_hosting_cost_cents"] or 0),
            "generation_time_sec": stats["generation_time_sec"],
            "source_file": str(article_file),
        }

    except Exception as e:
        print(f"Error processing {article_file}: {e}")
        return None


def analyze_articles(logs_root: Path) -> pd.DataFrame:
    """
    Analyze articles from all article files in the monitor logs.

    Args:
        logs_root: Root directory of monitor logs

    Returns:
        DataFrame with article analysis

    """
    records = []

    # Find all article files
    article_files = list(logs_root.rglob("*-article.json"))
    print(f"Found {len(article_files)} article files")

    for article_file in article_files:
        info = extract_article_info(article_file)
        if info:
            records.append(info)

    if not records:
        print("No article data found!")
        return pd.DataFrame()

    df = pd.DataFrame(records)

    # Sort by datetime
    if "datetime" in df.columns and df["datetime"].notna().any():
        df = df.sort_values("datetime")

    return df


def print_summary(df: pd.DataFrame) -> None:  # noqa: C901
    """Print summary statistics of article generation."""
    if df.empty:
        print("No data to summarize")
        return

    print("\n" + "=" * 80)
    print("ARTICLE GENERATION SUMMARY")
    print("=" * 80)

    print(f"\nTotal articles analyzed: {len(df)}")
    if df["datetime"].notna().any():
        print(f"Date range: {df['datetime'].min()} to {df['datetime'].max()}")

    print("\n--- Content Statistics ---")
    if df["word_count"].notna().any():
        print(f"Total words generated: {df['word_count'].sum():,}")
        print(f"Average words per article: {df['word_count'].mean():.1f}")
        print(f"Median words per article: {df['word_count'].median():.0f}")
        print(
            f"Min/Max words: {df['word_count'].min():.0f} / {df['word_count'].max():.0f}"
        )

    print("\n--- Citations ---")
    if df["num_citations"].notna().any():
        print(f"Total citations: {df['num_citations'].sum():,}")
        print(f"Average citations per article: {df['num_citations'].mean():.1f}")
        print(f"Median citations per article: {df['num_citations'].median():.0f}")

    if df["num_documents"].notna().any():
        print(f"Total unique documents cited: {df['num_documents'].sum():,}")
        print(f"Average documents per article: {df['num_documents'].mean():.1f}")
        print(f"Median documents per article: {df['num_documents'].median():.0f}")

    print("\n--- Token Counts ---")
    if df["prompt_tokens"].notna().any():
        print(f"Total input tokens: {df['prompt_tokens'].sum():,}")
        print(f"Average input tokens per article: {df['prompt_tokens'].mean():.1f}")

    if df["completion_tokens"].notna().any():
        print(f"Total output tokens: {df['completion_tokens'].sum():,}")
        print(
            f"Average output tokens per article: {df['completion_tokens'].mean():.1f}"
        )

    print("\n--- Costs ---")
    if df["llm_cost_cents"].notna().any():
        total_llm = df["llm_cost_cents"].sum()
        print(f"Total LLM cost: {total_llm:.2f} cents (${total_llm / 100:.2f})")
        print(f"Average LLM cost per article: {df['llm_cost_cents'].mean():.2f} cents")

    if df["self_hosting_cost_cents"].notna().any():
        total_hosting = df["self_hosting_cost_cents"].sum()
        print(
            f"Total self-hosting cost: {total_hosting:.2f} cents (${total_hosting / 100:.2f})"
        )
        print(
            f"Average self-hosting cost per article: {df['self_hosting_cost_cents'].mean():.2f} cents"
        )

    if df["total_cost_cents"].notna().any():
        total_cost = df["total_cost_cents"].sum()
        print(f"Total combined cost: {total_cost:.2f} cents (${total_cost / 100:.2f})")
        print(
            f"Average total cost per article: {df['total_cost_cents'].mean():.2f} cents"
        )

    print("\n--- Timing ---")
    if df["generation_time_sec"].notna().any():
        print(
            f"Total generation time: {df['generation_time_sec'].sum():.1f} seconds ({df['generation_time_sec'].sum() / 60:.1f} minutes)"
        )
        print(
            f"Average generation time: {df['generation_time_sec'].mean():.2f} seconds"
        )
        print(
            f"Median generation time: {df['generation_time_sec'].median():.2f} seconds"
        )

    print("\n--- Top 10 Longest Articles ---")
    if df["word_count"].notna().any():
        top_articles = df.nlargest(10, "word_count")[
            [
                "query",
                "word_count",
                "num_documents",
                "completion_tokens",
                "total_cost_cents",
            ]
        ]
        print(top_articles.to_string(index=False, max_colwidth=60))


def compute_monthly_summary(df: pd.DataFrame) -> pd.DataFrame:  # noqa: C901
    """Compute monthly aggregates for article analysis."""
    if df.empty or "datetime" not in df.columns:
        return pd.DataFrame()

    dfx = df[df["datetime"].notna()].copy()
    if dfx.empty:
        return pd.DataFrame()

    dfx["month"] = dfx["datetime"].dt.to_period("M").astype(str)

    agg: dict[str, Any] = {
        "query_id": "count",
        "word_count": ["sum", "mean", "median"],
        "num_citations": ["sum", "mean", "median"],
        "num_documents": ["sum", "mean", "median"],
        "completion_tokens": ["sum", "mean", "median"],
        "llm_cost_cents": ["sum", "mean"],
        "self_hosting_cost_cents": ["sum", "mean"],
        "total_cost_cents": ["sum", "mean"],
        "generation_time_sec": ["sum", "mean", "median"],
    }
    if dfx["prompt_tokens"].notna().any():
        agg["prompt_tokens"] = ["sum", "mean", "median"]

    monthly = dfx.groupby("month").agg(agg)
    monthly.columns = [
        c if isinstance(c, str) else f"{c[0]}_{c[1]}" for c in monthly.columns
    ]
    monthly = monthly.rename(columns={"query_id": "articles"}).reset_index()
    # Reduce excessive decimal digits for readability with per-column precision
    float_cols = monthly.select_dtypes(include=["float64", "float32"]).columns
    if len(float_cols) > 0:
        # Default rounding: 2 decimals
        monthly[float_cols] = monthly[float_cols].round(2)

        # Increase precision for mean cost columns to avoid 0.0
        for col in [
            "llm_cost_cents_mean",
            "self_hosting_cost_cents_mean",
            "total_cost_cents_mean",
        ]:
            if col in monthly.columns:
                monthly[col] = monthly[col].round(3)

        # Times: keep 2 decimals for means, 1 for sums where appropriate
        for col in [
            "generation_time_sec_mean",
            "generation_time_sec_median",
        ]:
            if col in monthly.columns:
                monthly[col] = monthly[col].round(2)
        if "generation_time_sec_sum" in monthly.columns:
            monthly["generation_time_sec_sum"] = monthly[
                "generation_time_sec_sum"
            ].round(1)

    # Avoid misleading 0.0 values: set certain zeros to None (NA)
    # If prompt tokens are not available for the month, replace 0.0 aggregates by NA
    pt_cols = [
        "prompt_tokens_sum",
        "prompt_tokens_mean",
        "prompt_tokens_median",
    ]
    if "prompt_tokens_sum" in monthly.columns:
        zero_pt_mask = monthly["prompt_tokens_sum"].fillna(0) == 0
        for col in pt_cols:
            if col in monthly.columns:
                monthly.loc[zero_pt_mask, col] = None
        # Replace remaining None/NaN with literal 'NA' for clarity
        for col in pt_cols:
            if col in monthly.columns:
                monthly[col] = monthly[col].astype(object)
                monthly[col] = monthly[col].where(monthly[col].notna(), "NA")

    # For very small mean costs that round to 0.0, show NA instead of 0.0
    cost_mean_cols = [
        "llm_cost_cents_mean",
        "self_hosting_cost_cents_mean",
        "total_cost_cents_mean",
    ]
    for col in cost_mean_cols:
        if col in monthly.columns:
            monthly.loc[monthly[col] == 0, col] = None
    return monthly


def print_monthly_summary(
    monthly: pd.DataFrame, months_filter: list[str] | None = None
) -> None:
    """Pretty-print monthly article summary, optionally filtering to specific months (YYYY-MM)."""
    if monthly.empty:
        print("\nNo monthly article data available")
        return

    dfm = monthly.copy()
    if months_filter:
        dfm = dfm[dfm["month"].isin(months_filter)]
        if dfm.empty:
            print("\nNo article data for selected months")
            return

    print("\n--- Monthly Article Summary (selected) ---")
    cols = [
        "month",
        "articles",
        "word_count_sum",
        "word_count_mean",
        "num_citations_sum",
        "num_documents_sum",
        "completion_tokens_sum",
        "total_cost_cents_sum",
        "generation_time_sec_sum",
    ]
    existing = [c for c in cols if c in dfm.columns]
    print(dfm[existing].to_string(index=False))


def main() -> None:
    """Run the article analysis CLI."""
    parser = argparse.ArgumentParser(
        description="Analyze article generation from monitor logs"
    )
    parser.add_argument(
        "logs_root", type=Path, help="Path to the monitor-logs root directory"
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("article_analysis.csv"),
        help="Output CSV file path (default: article_analysis.csv)",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Only print summary, don't write CSV",
    )

    args = parser.parse_args()

    args.out = _resolve_output_path(args.out)

    if not args.logs_root.exists():
        print(f"Error: {args.logs_root} does not exist")
        return

    print(f"Analyzing articles from: {args.logs_root}")
    df = analyze_articles(args.logs_root)

    if df.empty:
        print("No article data found in the logs")
        return

    # Print summary
    print_summary(df)

    # Monthly summary and optional CSV
    monthly = compute_monthly_summary(df)
    print_monthly_summary(
        monthly, months_filter=["2025-07", "2025-08", "2025-09", "2025-10"]
    )

    # Write CSV
    if not args.summary_only:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(args.out, index=False)
        print(f"\n{'=' * 80}")
        print(f"Detailed results written to: {args.out}")
        print(f"Columns: {', '.join(df.columns)}")
        print(f"{'=' * 80}")
        # Write monthly CSV next to main output
        try:
            monthly_out = Path(args.out).with_name(Path(args.out).stem + "_monthly.csv")
            if not monthly.empty:
                monthly.to_csv(monthly_out, index=False)
                print(f"Monthly summary written to: {monthly_out}")
        except Exception as e:
            print(f"Failed to write monthly CSV: {e}")


if __name__ == "__main__":
    main()
