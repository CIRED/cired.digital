"""
Tabulate queries.

    List all queries made by users.
    Each row corresponds to a query, with columns for user origin, query text, and timestamp.
    Save into "Queries.csv".

    Then list unique queries with counts, saved into "UniqueQueries.csv".

Minh Ha-Duong, CNRS, 2025-11
"""

import pandas as pd
from logloader import sessions


def build_all_queries_df() -> pd.DataFrame:
    """
    Extract all user queries from sessions and enrich with origin.

    Returns a DataFrame with columns: query, order, timestamp, origin, ua.
    The order column indicates the position of the query within the session.
    """
    records = []
    for s in sessions:
        origin = s.get("origin", "??")
        ua_class = s.get("ua_class", "??")
        order = 0
        for e in s["events"]:
            if e["eventType"] == "request":
                order += 1
                records.append(
                    {
                        "query": e["payload"].get("query", ""),
                        "order": order,
                        "timestamp": pd.to_datetime(e["timestamp"]),
                        "origin": origin,
                        "browser": ua_class,
                    }
                )
    df = pd.DataFrame.from_records(records)
    return df


def main() -> None:
    """Generate Queries.csv and UniqueQueries.csv from monitor logs."""
    all_queries = build_all_queries_df()
    print(f"Total queries extracted: {len(all_queries)}")
    all_queries.to_csv("Queries.csv", index=False)

    unique_queries = all_queries["query"].value_counts().reset_index()
    unique_queries = unique_queries.rename(columns={"index": "query", "query": "count"})
    unique_queries.to_csv("UniqueQueries.csv", index=False)


if __name__ == "__main__":
    main()
