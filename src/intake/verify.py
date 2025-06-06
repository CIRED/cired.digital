#!/usr/bin/env python
"""
Inspect the contents of R2R document store.

Requirements:
    - Python 3.11+
    - r2r Python SDK and Pandas (the shebang above will create a temp venv)
"""

import argparse
import logging
import re
import sys

import pandas as pd
from r2r import R2RClient

from intake.config import R2R_DEFAULT_BASE_URL, setup_logging
from intake.utils import get_existing_documents


def check_r2r(client: R2RClient) -> bool:
    """Check that R2R is up and replying."""
    try:
        _ = client.documents.list(limit=1)
        logging.debug("R2R client is up and responding.")
        return True
    except Exception as e:
        logging.warning(f"Failed to get reply from R2R: {e}")
        return False


def overview(documents: pd.DataFrame) -> int:
    """
    Print comprehensive overview including basic stats and all issue counts.

    Returns
    -------
        None

    """
    print("=" * 60)
    print("📋 R2R DOCUMENT STORE OVERVIEW")
    print("=" * 60)

    # Basic info
    documents.info()
    print("\n📊 Summary statistics (numerical columns):")
    num_stats = documents.describe(include=[float, int]).round(0).astype("Int64")
    formatted_stats = num_stats.apply(lambda col: col.map("{:,}".format))
    print(formatted_stats)

    print("\n📝 Summary statistics (object/string columns):")
    obj_stats = documents.describe(include=[object, "string"]).transpose()
    print(obj_stats)

    # Issue counts summary
    print("\n" + "=" * 60)
    print("🔍 ISSUE SUMMARY")
    print("=" * 60)

    # Count each type of issue directly using helper functions
    short_title_count = len(_find_short_titles(documents))
    failed_ingestion_count = len(_find_failed_ingestions(documents))
    repeat_halid_count = len(_find_repeat_halid(documents))
    repeat_doi_count = len(_find_repeat_dois(documents))
    repeat_title_count = len(_find_repeat_titles(documents))

    print(f"🚨 Documents with short/missing titles: {short_title_count:,}")
    print(f"❌ Documents with failed ingestion: {failed_ingestion_count:,}")
    print(f"🔁 Documents with duplicate HAL IDs: {repeat_halid_count:,}")
    print(f"🔁 Documents with duplicate DOIs: {repeat_doi_count:,}")
    print(f"🔁 Documents with duplicate titles: {repeat_title_count:,}")

    total_issues = (
        short_title_count
        + failed_ingestion_count
        + repeat_halid_count
        + repeat_doi_count
        + repeat_title_count
    )
    print(f"⚠️  Total number of issues: {total_issues:,}")
    print(f"📋 Total documents: {len(documents):,}")

    if total_issues == 0:
        print("✅ No issues detected!")
    else:
        issue_rate = (total_issues / len(documents)) * 100 if len(documents) > 0 else 0
        print(f"📊 Issue rate: {issue_rate:.1f}%")

    return total_issues


def _is_anomalous_title(title: str | float | None) -> bool:
    """Check if a title is anomalous (null, empty, or single word)."""
    if pd.isna(title):
        return True
    title = str(title).strip()
    return title == "" or len(title.split()) <= 1


def _find_short_titles(documents: pd.DataFrame) -> pd.DataFrame:
    """Find documents with null or one word titles."""
    if "title" not in documents.columns:
        return pd.DataFrame()

    anomalies = documents[documents["title"].apply(_is_anomalous_title)]
    return anomalies.sort_values("title", na_position="first")


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

    anomalies = _find_short_titles(documents)
    print(f"\n🚨 Found {len(anomalies)} anomalous title(s):")
    for _, row in anomalies.iterrows():
        print(
            f"• ID: {row['id']} — Title: '{row['title']}' — Meta_title: '{row['meta_title']}' — Meta_source_url: '{row['meta_source_url']}'"
        )
    return len(anomalies)


def _find_failed_ingestions(documents: pd.DataFrame) -> pd.DataFrame:
    """Find documents with unsuccessful ingestion status."""
    if "ingestion_status" not in documents.columns:
        return pd.DataFrame()
    return documents[documents["ingestion_status"] != "success"]


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

    failures = _find_failed_ingestions(documents)
    if failures.empty:
        print("✅ All documents were successfully ingested.")
        return 0
    print(f"\n❌ Found {len(failures)} documents with failed ingestion:")
    for _, row in failures.iterrows():
        print(
            f"• ID: {row['id']}\n  Status: {row['ingestion_status']}\n  Failure: {row.get('meta_failure', 'N/A')}"
        )
    return len(failures)


def _find_repeat_halid(documents: pd.DataFrame) -> pd.DataFrame:
    """Find documents with repeated HAL Id."""
    if "meta_hal_id" not in documents.columns:
        return pd.DataFrame()
    dup_mask = documents["meta_hal_id"].duplicated(keep=False)
    duplicates = documents[dup_mask & documents["meta_hal_id"].notna()]
    return duplicates.sort_values("meta_hal_id")


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

    duplicates = _find_repeat_halid(documents)
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


def _find_repeat_dois(documents: pd.DataFrame) -> pd.DataFrame:
    """Find documents with repeated DOIs."""
    if "meta_doi" not in documents.columns:
        return pd.DataFrame()

    # Filter out null/empty DOIs and find duplicates
    valid_dois = documents[
        documents["meta_doi"].notna() & (documents["meta_doi"] != "")
    ]
    dup_mask = valid_dois["meta_doi"].duplicated(keep=False)
    duplicates = valid_dois[dup_mask]
    return duplicates.sort_values("meta_doi")


def show_repeat_dois(documents: pd.DataFrame) -> int:
    """
    Print and count sets of documents with repeated DOIs.

    Returns
    -------
        int: Total number of documents with repeated DOIs.

    """
    if "meta_doi" not in documents.columns:
        print("⚠️ No 'meta_doi' column found.")
        return 0

    duplicates = _find_repeat_dois(documents)
    if duplicates.empty:
        print("✅ No repeated DOIs found.")
        return 0

    print(f"\n🔁 Found {len(duplicates)} documents with repeated DOIs:")
    grouped = duplicates.groupby("meta_doi")

    for doi, group in grouped:
        print(f"\n• DOI: {doi}")
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


def normalize_title(title: str | float | None) -> str:
    """Normalize title by lowercasing, stripping punctuation, and collapsing spaces."""
    if pd.isna(title):
        return ""
    title = str(title).lower()
    title = re.sub(r"[^\w\s]", "", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title


def _find_repeat_titles(documents: pd.DataFrame) -> pd.DataFrame:
    """Find documents with repeated titles (normalized)."""
    if "title" not in documents.columns:
        return pd.DataFrame()

    # Create a copy to avoid modifying the original
    docs_copy = documents.copy()
    docs_copy["normalized_title"] = docs_copy["title"].apply(normalize_title)
    dup_mask = docs_copy.duplicated("normalized_title", keep=False)
    duplicates = docs_copy[dup_mask]
    return duplicates.sort_values("normalized_title")


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

    duplicates = _find_repeat_titles(documents)
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
    "overview": overview,
    "short-titles": show_short_titles,
    "failed-ingestions": show_failed_ingestions,
    "halids": show_repeat_halid,
    "titles": show_repeat_titles,
    "dois": show_repeat_dois,
}


def get_help_lines() -> str:
    """Fetch the help from the functions' docstrings for CLI help display."""
    max_len = max(len(cmd) for cmd in COMMANDS)
    lines = []

    for cmd, fn in COMMANDS.items():
        doc = fn.__doc__ or "[no doc]"
        first_line = doc.strip().splitlines()[0]
        lines.append(f"  {cmd.ljust(max_len)}  {first_line}")

    return "\n".join(lines)


def main() -> int:
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
        print("\nNo argument given. Here is the overview:\n")
        _, documents = setup()
        issues = overview(documents)
        return issues
    else:
        args = parser.parse_args()

    if args.what not in COMMANDS:
        parser.error(f"Unknown command: {args.what}")

    _, documents = setup()

    issues = COMMANDS[args.what](documents)
    return issues


if __name__ == "__main__":
    main()
