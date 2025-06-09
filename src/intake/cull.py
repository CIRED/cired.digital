#!/usr/bin/env python
"""
Align R2R documents with metadata on the HAL catalog by deleting offenders.

This script:
- Reads source/hal/catalog.json
- Gets existing documents from the server
- Matches each document with catalog records by hal_id or title
- Compares meta_ columns with catalog data
- Delete documents with inconsistent meta
"""

from __future__ import annotations  # Needed for pd.Series[Any]

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from r2r import R2RClient

from intake.config import R2R_DEFAULT_BASE_URL, setup_logging
from intake.push import format_metadata_for_upload
from intake.utils import (
    get_catalog_file,
    get_server_documents,
    load_catalog_by_hal_id,
)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments and return namespace."""
    parser = argparse.ArgumentParser(
        description="Delete R2R documents missing or mismatched with the HAL catalog",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  %(prog)s --help                    Show this help message
  %(prog)s                           Dry run - show what would be deleted
  %(prog)s --execute                 Actually delete unaligned documents
  %(prog)s --log-level debug         Enable debug logging
  %(prog)s --catalog /path/to/catalog.json  Use custom catalog file
""",
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        help="Path to catalog.json file (default: latest prepared catalog)",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=R2R_DEFAULT_BASE_URL,
        help=f"R2R API base URL (default: {R2R_DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--target",
        choices=["missing", "mismatch", "both", "failed-ingestions"],
        default="both",
        help="Type of deletion: missing, mismatch, both, or failed-ingestions",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete documents (default: dry-run mode)",
    )
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error"],
        default="info",
        help="Set logging level (default: info)",
    )
    args = parser.parse_args()
    return args


def init_logging(level_name: str) -> None:
    """Initialize logging with level name."""
    level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
    }
    setup_logging(level=level_map[level_name], simple_format=True)
    logging.info("Logging initialized at %s level", level_name.upper())


def load_catalog(catalog_arg: Path | None) -> dict[str, Any]:
    """Load catalog and return mapping of hal_id to metadata."""
    catalog_file = get_catalog_file(catalog_arg)
    if not catalog_file:
        raise FileNotFoundError(
            "No catalog file found. Run hal_query.py and prepare_catalog.py first."
        )
    catalog_by_hal_id, _ = load_catalog_by_hal_id(catalog_file)
    if not catalog_by_hal_id:
        raise RuntimeError("Failed to load catalog metadata.")
    logging.info("Catalog loaded with %d entries", len(catalog_by_hal_id))
    return catalog_by_hal_id


def fetch_and_enrich_docs(client: R2RClient, catalog: dict[str, Any]) -> pd.DataFrame:
    """Fetch documents from R2R and enrich with catalog metadata."""
    df = get_server_documents(client)
    if df is None:
        raise RuntimeError("Failed to retrieve documents from R2R.")
    df["catalog_entry"] = df["meta_hal_id"].map(catalog.get)
    df["is_in_catalog"] = df["catalog_entry"].notnull()
    df["metadata_bad"] = df.apply(
        lambda row: bool(identify_bad_metadata(row, row["catalog_entry"] or {})), axis=1
    )
    logging.info(
        "Fetched %d documents; %d flagged for metadata mismatch",
        len(df),
        df["metadata_bad"].sum(),
    )
    return df


def compute_targets(df: pd.DataFrame, target: str) -> list[str]:
    """Compute list of document ids to delete based on target criteria."""
    if target == "failed-ingestions":
        failures = df.loc[df["ingestion_status"] != "success", "id"].tolist()
        logging.info("Documents to delete (%s): %d", target, len(failures))
        return failures

    orphans = df.loc[~df["is_in_catalog"], "id"].tolist()
    bad_meta = df.loc[df["is_in_catalog"] & df["metadata_bad"], "id"].tolist()
    to_delete: list[str] = []
    if target in ("missing", "both"):
        to_delete += orphans
    if target in ("mismatch", "both"):
        to_delete += bad_meta
    logging.info("Documents to delete (%s): %d", target, len(to_delete))
    return to_delete


def delete_documents(ids: list[str], client: R2RClient, execute: bool) -> int:
    """Delete documents and return count of removed items."""
    removed = 0
    for doc_id in ids:
        logging.info("Deleting document %s", doc_id)
        if execute and remove_document(doc_id, client):
            removed += 1
    logging.info("Deleted %d documents (execute=%s)", removed, execute)
    return removed


def identify_bad_metadata(
    document_row: pd.Series[Any], catalog_metadata: dict[str, Any]
) -> dict[str, Any]:
    """Return the metadata that need to be aligned on the catalog."""
    logging.debug("Inspecting for unaligned metadata")
    logging.debug("Document: %s", str(document_row))
    catalog_metadata = format_metadata_for_upload(catalog_metadata)
    logging.debug("Catalog:  %s", str(catalog_metadata))

    bad_metadata = {}

    field_mapping = {
        "title": "meta_title",
        "citation": "meta_citation",
        "description": "meta_description",
        "publication_date": "meta_publication_date",
        "doi": "meta_doi",
        "hal_id": "meta_hal_id",
        "document_type": "meta_document_type",
        "authors": "meta_authors",
        "source_url": "meta_source_url",
    }

    for catalog_field, meta_column in field_mapping.items():
        current_value = document_row.get(meta_column)
        catalog_value = catalog_metadata.get(catalog_field)

        if catalog_field == "authors":
            logging.debug("Authors comparison.")
            logging.debug("Values are %s == %s", current_value, catalog_value)
            logging.debug("Types %s == %s", type(current_value), type(catalog_value))
            same = str(current_value) == catalog_value
            logging.debug("Comparison %s", str(same))
            if same:
                continue

        if pd.isna(current_value) or (
            isinstance(current_value, str) and current_value.strip() == ""
        ):
            current_value = None

        if current_value == catalog_value:
            continue

        bad_metadata[catalog_field] = catalog_value

    if bad_metadata != {}:
        logging.debug("Bad metadata = %s", str(bad_metadata))

    return bad_metadata


def remove_document(doc_id: str, client: R2RClient) -> bool:
    """Remove a document from the server."""
    try:
        logging.debug("Trying to delete document %s", doc_id)
        response = client.documents.delete(id=doc_id)
        logging.debug("Response for %s", str(response))
        return True
    except Exception:
        logging.error("Failed to delete document")
        return False


def main() -> int:
    """Align R2R document metadata on the HAL catalog."""
    args = parse_args()
    init_logging(args.log_level)

    if args.execute:
        logging.info("Running in EXECUTE mode - will actually delete documents")
    else:
        logging.info("Running in DRY-RUN mode - will show what would be deleted")

    try:
        catalog = load_catalog(args.catalog)
    except Exception as e:
        logging.error("Metadata alignment abort: %s", e)
        return 1

    client = R2RClient(base_url=args.base_url)

    try:
        docs_df = fetch_and_enrich_docs(client, catalog)
    except Exception as e:
        logging.error("Document retrieval error: %s", e)
        return 2

    targets = compute_targets(docs_df, args.target)
    if not targets:
        logging.info("No documents to delete based on target criteria")
        return 0

    delete_count = delete_documents(targets, client, args.execute)
    logging.info("Summary: %d documents removed", delete_count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
