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

from intake.config import CATALOG_FILE, R2R_DEFAULT_BASE_URL, setup_logging
from intake.push import format_metadata_for_upload
from intake.utils import (
    get_catalog_file,
    get_server_documents,
    load_catalog_by_hal_id,
)


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


def setup_argument_parser() -> argparse.ArgumentParser:
    """Set up command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Delete R2R documents missing or mismatched with the HAL catalog",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
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
        choices=["missing", "mismatch", "both"],
        default="both",
        help="Type of deletion: missing = only orphans, mismatch = only metadata mismatches, both = both (default)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete documents (default is dry-run mode)",
    )
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error"],
        default="info",
        help="Set logging level (default: info)",
    )
    return parser


def main() -> int:
    """
    Align R2R document metadata on the HAL catalog.

    This script reads the HAL catalog, retrieves documents from R2R server,
    matches them by hal_id or title pattern, compares the metadata and
    DELETE DOCUMENTS with unaligned metadata.
    By default runs in dry-run mode to show what would be deleted.
    """
    parser = setup_argument_parser()
    args = parser.parse_args()

    log_levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
    }

    setup_logging(level=log_levels[args.log_level], simple_format=True)

    if args.execute:
        logging.info("Running in EXECUTE mode - will actually delete documents")
    else:
        logging.info("Running in DRY-RUN mode - will show what would be deleted")

    catalog_file = get_catalog_file(args.catalog)
    if not catalog_file:
        logging.error(
            "No catalog file found. Run hal_query.py and prepare_catalog.py first."
        )
        return 1

    if catalog_file == CATALOG_FILE:
        logging.info("Using legacy catalog file: %s", CATALOG_FILE)
    else:
        logging.info("Using catalog file: %s", catalog_file)

    catalog_by_hal_id, _ = load_catalog_by_hal_id(catalog_file)
    if not catalog_by_hal_id:
        logging.error("Metadata alignment abort: Failed to load catalog.")
        return 1

    client = R2RClient(base_url=args.base_url)

    try:
        documents_df = get_server_documents(client)
        if documents_df is None:
            logging.error(
                "Metadata alignment abort: Failed to retrieve documents from R2R."
            )
            return 2
    except Exception as e:
        logging.error("Metadata alignment abort: Failed to connect to R2R: %s", str(e))
        return 3

    # Enrich the DataFrame with catalog info and metadata check
    documents_df["catalog_entry"] = documents_df["meta_hal_id"].map(
        lambda hid: catalog_by_hal_id.get(hid)
    )
    documents_df["is_in_catalog"] = documents_df["catalog_entry"].notnull()

    def check_metadata(row):
        return bool(identify_bad_metadata(row, row["catalog_entry"] or {}))

    documents_df["metadata_bad"] = documents_df.apply(check_metadata, axis=1)

    orphans = documents_df.loc[~documents_df["is_in_catalog"], "id"]
    bad_meta = documents_df.loc[
        documents_df["is_in_catalog"] & documents_df["metadata_bad"], "id"
    ]

    to_delete = []
    if args.target in ("missing", "both"):
        to_delete += list(orphans)
    if args.target in ("mismatch", "both"):
        to_delete += list(bad_meta)

    if not to_delete:
        logging.info("No documents to delete based on target criteria")
        return 0

    delete_count = 0
    for doc_id in to_delete:
        logging.info(
            "Suppressing document %s (%s)",
            doc_id,
            documents_df["title"].get(doc_id, "Unknown Title"),
        )
        if args.execute:
            if remove_document(doc_id, client):
                delete_count += 1

    logging.info("Summary: %s documents removed from the server", delete_count)

    if not args.execute:
        logging.info("Mode dry-run - nothing removed")
        logging.info("Use --execute to really remove documents from server")
    return 0


if __name__ == "__main__":
    sys.exit(main())
