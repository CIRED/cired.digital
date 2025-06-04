#!/usr/bin/env -S uvx --with-requirements requirements.txt python
"""
Inspect the contents of R2R document store.

Requirements:
    - Python 3.11+
    - r2r Python SDK and Pandas (the shebang above will create a temp venv)
"""

import argparse
import json
import logging
import re
import sys
from collections.abc import Hashable, Mapping

import pandas as pd
from r2r import R2RClient

from config import R2R_DEFAULT_BASE_URL, setup_logging

DOCUMENTS_FILE = "documents.csv"
DOCUMENTS_COLUMNS = [
    "id",
    "title",
    "size_in_bytes",
    "ingestion_status",
    "extraction_status",
    "created_at",
    "updated_at",
    "type",
    "metadata",
]
COLUMNS_TYPES: Mapping[Hashable, str] = {
    "id": "string",
    "title": "string",
    "size_in_bytes": "int64",
    "ingestion_status": "string",
    "extraction_status": "string",
    "type": "string",
    "metadata": "string",
}
DATE_COLUMNS = ["created_at", "updated_at"]


def check_r2r(client: R2RClient) -> bool:
    """Check that R2R is up and replying."""
    try:
        _ = client.documents.list(limit=1)
        logging.debug("R2R client is up and responding.")
        return True
    except Exception as e:
        logging.warning(f"Failed to get reply from R2R: {e}")
        return False


def get_existing_documents(client: R2RClient) -> pd.DataFrame | None:
    """
    Retrieve all documents from the R2R service as a structured DataFrame.

    This function:
    - Exports document metadata from the R2R client to a CSV file.
    - Loads the CSV file into a pandas DataFrame with proper type and date parsing.
    - Parses the 'metadata' column as JSON and flattens it into prefixed columns.

    Args:
    ----
        client (R2RClient): The connected R2R client instance.

    Returns:
    -------
        pd.DataFrame | None: A DataFrame with one row per document and enriched metadata columns,
        or None if retrieval or parsing fails.

    """
    try:
        # 1. Export documents from the R2R server to a local CSV file
        logging.debug(f"Exporting document metadata to '{DOCUMENTS_FILE}'...")
        client.documents.export(output_path=DOCUMENTS_FILE, columns=DOCUMENTS_COLUMNS)

        # 2. Load the CSV into a DataFrame with typed columns and date parsing
        df = pd.read_csv(DOCUMENTS_FILE, dtype=COLUMNS_TYPES, parse_dates=DATE_COLUMNS)

        # 3. Parse the 'metadata' column (a JSON string per row) into Python dicts
        df["metadata"] = df["metadata"].apply(json.loads)

        # 4. Flatten the nested metadata into separate columns, prefixed with 'meta_'
        metadata_flat = pd.json_normalize(df["metadata"].tolist()).add_prefix("meta_")

        # 5. Drop the original 'metadata' column and merge the flattened metadata
        df = df.drop(columns=["metadata"]).join(metadata_flat)

        # 6. Done
        logging.info(f"Loaded {len(df)} document records with enriched metadata.")
        return df

    except Exception as e:
        logging.error(f"Failed to load document data: {e}")
        return None


def describe_table(documents: pd.DataFrame) -> None:
    """
    Print basic description of the R2R document store contents.

    Returns
    -------
        None

    """
    documents.info()
    print("\n📊 Summary statistics (numerical columns):")
    num_stats = documents.describe(include=[float, int]).round(0).astype("Int64")
    formatted_stats = num_stats.apply(lambda col: col.map("{:,}".format))
    print(formatted_stats)

    print("\n📝 Summary statistics (object/string columns):")
    obj_stats = documents.describe(include=[object, "string"]).transpose()
    print(obj_stats)


def show_short_titles(documents: pd.DataFrame) -> int:
    """
    Print and count documents with null or one word title.

    Returns
    -------
        int: Total number of documents with suspiciously short title.

    """
    if "title" not in documents.columns:
        print("⚠️ No 'title' column found.")
        return 1
    if "meta_title" not in documents.columns:
        print("⚠️ No 'meta_title' column found.")
        return 2

    def is_anomalous(title: str | float | None) -> bool:
        if pd.isna(title):
            return True
        title = str(title).strip()
        return title == "" or len(title.split()) <= 1

    anomalies = documents[documents["title"].apply(is_anomalous)]
    anomalies = anomalies.sort_values("title", na_position="first")
    print(f"\n🚨 Found {len(anomalies)} anomalous title(s):")
    for _, row in anomalies.iterrows():
        print(
            f"• ID: {row['id']} — Title: '{row['title']}' — Meta_title: '{row['meta_title']}' — Meta_source_url: '{row['meta_source_url']}'"
        )
    return len(anomalies)


def show_failed_ingestions(documents: pd.DataFrame) -> int:
    """
    Print and count documents with unsuccessfull ingestion status.

    Returns
    -------
        int: Total number of documents with unsuccessfull ingestion status.

    """
    if "ingestion_status" not in documents.columns:
        print("⚠️ No 'ingestion_status' column found.")
        return 0
    failures = documents[documents["ingestion_status"] != "success"]
    if failures.empty:
        print("✅ All documents were successfully ingested.")
        return 0
    print(f"\n❌ Found {len(failures)} documents with failed ingestion:")
    for _, row in failures.iterrows():
        print(
            f"• ID: {row['id']}\n  Status: {row['ingestion_status']}\n  Failure: {row.get('meta_failure', 'N/A')}"
        )
    return len(failures)


def show_repeat_halid(documents: pd.DataFrame) -> int:
    """
    Print and count sets of documents with repeated HAL Id.

    Returns
    -------
        int: Total number of documents with repeated HAL Ids.

    """
    if "meta_hal_id" not in documents.columns:
        print("⚠️ No 'meta_hal_id' column found.")
        return 0
    dup_mask = documents["meta_hal_id"].duplicated(keep=False)
    duplicates = documents[dup_mask & documents["meta_hal_id"].notna()].sort_values(
        "meta_hal_id"
    )
    if duplicates.empty:
        print("✅ No repeated HAL IDs found.")
        return 0
    print(f"\n🔁 Found {len(duplicates)} documents with repeated HAL IDs:")
    grouped = duplicates.groupby("meta_hal_id")
    for hal_id, group in grouped:
        print(f"\n• HAL ID: {hal_id}")
        for _, row in group.iterrows():
            print(
                f"  - ID: {row['id']} - Ingestion: {row['ingestion_status']}, Extraction: {row['extraction_status']}"
            )
    return len(duplicates)


def normalize_title(title: str | float | None) -> str:
    """Normalize title by lowercasing, stripping punctuation, and collapsing spaces."""
    if pd.isna(title):
        return ""
    title = str(title).lower()
    title = re.sub(r"[^\w\s]", "", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title


def show_repeat_titles(documents: pd.DataFrame) -> int:
    """
    Print and count sets of documents with repeated titles.

    Ignores casing, spacing and punctuation when comparing titles.

    Returns
    -------
        int: Total number of documents with non-unique normalized titles.

    """
    if "title" not in documents.columns:
        print("⚠️ No 'title' column found.")
        return 0
    documents["normalized_title"] = documents["title"].apply(normalize_title)
    dup_mask = documents.duplicated("normalized_title", keep=False)
    duplicates = documents[dup_mask].sort_values("normalized_title")
    if duplicates.empty:
        print("✅ No repeated titles found.")
        return 0
    print(f"\n🔁 Found {len(duplicates)} documents with repeated titles (normalized):")
    grouped = duplicates.groupby("normalized_title")
    for norm_title, group in grouped:
        print(f"\n• Normalized title: '{norm_title}'")
        for _, row in group.iterrows():
            print(
                f"  - ID: {row['id']}\n"
                f"    Title: '{row['title']}'\n"
                f"    Size: {row['size_in_bytes']:,} bytes\n"
                f"    Ingestion: {row['ingestion_status']}, Extraction: {row['extraction_status']}\n"
                f"    HAL ID: {row.get('meta_hal_id', 'N/A')}\n"
                f"    Citation: {row.get('meta_citation', 'N/A')}"
            )
    return len(duplicates)


def setup() -> tuple[R2RClient, pd.DataFrame]:
    """Retrieve the documents in store."""
    setup_logging()
    logging.info(f"Connecting to R2R at {R2R_DEFAULT_BASE_URL}...")
    client = R2RClient(base_url=R2R_DEFAULT_BASE_URL)

    if not check_r2r(client):
        logging.error("R2R service is unreachable.")
        exit(3)

    documents = get_existing_documents(client)
    if documents is None:
        logging.error("Could not retrieve documents from R2R.")
        exit(1)

    return client, documents


COMMANDS = {
    "overview": describe_table,
    "short-titles": show_short_titles,
    "failed-ingestions": show_failed_ingestions,
    "repeat-halid": show_repeat_halid,
    "repeat-titles": show_repeat_titles,
}


def get_help_lines() -> str:
    """Fetch the help from the functions' docstrings for CLI help display."""
    max_len = max(len(cmd) for cmd in COMMANDS)
    lines = []

    for cmd, fn in COMMANDS.items():
        doc = fn.__doc__ or "[no doc]"
        first_line = doc.strip().splitlines()[0]
        lines.append(f"  {cmd.ljust(max_len)}  {first_line}")

    lines.append(f"  {'all'.ljust(max_len)}  Run all checks in sequence.")
    return "\n".join(lines)


def main() -> None:
    """Inspect the state of the R2R documents store."""
    parser = argparse.ArgumentParser(
        description=f"Inspect the state of the R2R documents store at {R2R_DEFAULT_BASE_URL}.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "what",
        help="What to inspect, must be one of the following:\n" + get_help_lines(),
    )

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(2)

    args = parser.parse_args()

    if args.what not in COMMANDS and args.what != "all":
        parser.error(f"Unknown command: {args.what}")

    _, documents = setup()

    if args.what == "all":
        for fn in COMMANDS.values():
            fn(documents)
    else:
        COMMANDS[args.what](documents)


if __name__ == "__main__":
    main()
