"""
Tabulate queries.

    List all queries made by users.
    Each row corresponds to a query, with columns for user origin, query text, and timestamp.
    Save into "Queries.csv".

    Then list unique queries with counts, saved into "UniqueQueries.csv".

Minh Ha-Duong, CNRS, 2025-11
"""

from pathlib import Path

import pandas as pd


def _reports_analysis_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "reports" / "analysis"


def _resolve_output_path(path: str) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    if p.parent == Path("."):
        return _reports_analysis_dir() / p.name
    return p


def build_all_queries_df(sessions: list[dict[str, object]]) -> pd.DataFrame:
    """
    Extract all user queries from sessions and enrich with origin.

    Returns a DataFrame with columns: query, order, timestamp, origin, ua.
    The order column indicates the position of the query within the session.
    """
    records = []
    for s in sessions:
        origin = str(s.get("origin", "??"))
        ua_class = str(s.get("ua_class", "??"))
        order = 0
        events = s.get("events", [])
        if not isinstance(events, list):
            continue

        for e in events:
            if not isinstance(e, dict):
                continue
            if e.get("eventType") == "request":
                order += 1
                payload = e.get("payload", {})
                if not isinstance(payload, dict):
                    payload = {}
                ts_raw = e.get("timestamp")
                ts_str = "" if ts_raw is None else str(ts_raw)
                records.append(
                    {
                        "query": payload.get("query", ""),
                        "order": order,
                        "timestamp": pd.to_datetime(ts_str, errors="coerce"),
                        "origin": origin,
                        "browser": ua_class,
                    }
                )
    df = pd.DataFrame.from_records(records)
    return df


def main() -> None:
    """Generate Queries.csv and UniqueQueries.csv from monitor logs."""
    # Lazy import to avoid loading monitor logs on module import
    from logloader import sessions

    all_queries = build_all_queries_df(sessions)
    print(f"Total queries extracted: {len(all_queries)}")
    out_all = _resolve_output_path("Queries.csv")
    out_all.parent.mkdir(parents=True, exist_ok=True)
    all_queries.to_csv(out_all, index=False)

    unique_queries = all_queries["query"].value_counts().reset_index()
    unique_queries = unique_queries.rename(columns={"index": "query", "query": "count"})
    out_unique = _resolve_output_path("UniqueQueries.csv")
    out_unique.parent.mkdir(parents=True, exist_ok=True)
    unique_queries.to_csv(out_unique, index=False)


if __name__ == "__main__":
    main()
