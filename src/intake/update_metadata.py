#!/usr/bin/env python
"""
Update metadata for documents in R2R from HAL catalog.

This script:
- Reads source/hal/catalog.json
- Gets existing documents from the server using verify.py
- Matches each document with catalog records by hal_id or title
- Compares meta_ columns with catalog data
- Updates missing metadata using R2R patch API
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from r2r import R2RClient

from intake.config import CATALOG_FILE, R2R_DEFAULT_BASE_URL, setup_logging
from intake.push import format_metadata_for_upload
from intake.verify import get_existing_documents


def load_catalog(catalog_file: Path) -> dict[str, dict[str, Any]]:
    """Load catalog data and index by hal_id."""
    if not catalog_file.exists():
        logging.error(f"Catalog file not found: {catalog_file}")
        logging.error("Run query.py first to create the catalog.")
        return {}

    try:
        publications = json.loads(catalog_file.read_text(encoding="utf-8"))
        catalog_by_hal_id = {}

        for pub in publications:
            if "halId_s" in pub:
                hal_id = pub["halId_s"]
                catalog_by_hal_id[hal_id] = pub

        logging.info(f"Loaded {len(catalog_by_hal_id)} publications from catalog")
        return catalog_by_hal_id

    except Exception as e:
        logging.error(f"Failed to load catalog: {e}")
        return {}


def match_documents_to_catalog(
    documents_df: pd.DataFrame, catalog_by_hal_id: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    """Match server documents to catalog entries."""
    matches = []

    for _, doc in documents_df.iterrows():
        doc_id = doc["id"]
        title = doc["title"]
        meta_hal_id = doc.get("meta_hal_id")

        catalog_entry = None
        match_method = None

        if meta_hal_id and meta_hal_id in catalog_by_hal_id:
            catalog_entry = catalog_by_hal_id[meta_hal_id]
            match_method = "meta_hal_id"

        elif title and title.endswith(".pdf"):
            potential_hal_id = title[:-4]  # Remove .pdf extension
            if potential_hal_id in catalog_by_hal_id:
                catalog_entry = catalog_by_hal_id[potential_hal_id]
                match_method = "title_pattern"

        if catalog_entry:
            matches.append(
                {
                    "doc_id": doc_id,
                    "title": title,
                    "meta_hal_id": meta_hal_id,
                    "catalog_entry": catalog_entry,
                    "match_method": match_method,
                    "document_row": doc,
                }
            )

    logging.info(f"Matched {len(matches)} documents to catalog entries")
    return matches


def needs_metadata_update(
    document_row: Any, catalog_metadata: dict[str, Any]
) -> dict[str, Any]:
    """Check if document needs metadata updates."""
    updates_needed = {}

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
        catalog_value = catalog_metadata.get(catalog_field)
        current_value = document_row.get(meta_column)

        if catalog_value and (
            current_value is None or str(current_value).strip() == ""
        ):
            updates_needed[catalog_field] = catalog_value

    return updates_needed


def update_document_metadata(
    client: R2RClient, doc_id: str, metadata_updates: dict[str, Any]
) -> bool:
    """Update document metadata using R2R patch API."""
    try:
        metadata_list = [
            {"key": key, "value": str(value)} for key, value in metadata_updates.items()
        ]

        client.documents.append_metadata(id=doc_id, metadata=metadata_list)

        logging.info(
            f"Updated metadata for document {doc_id}: {list(metadata_updates.keys())}"
        )
        return True

    except Exception as e:
        logging.error(f"Failed to update metadata for document {doc_id}: {e}")
        return False


def setup_argument_parser() -> argparse.ArgumentParser:
    """Set up command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Update R2R document metadata from HAL catalog",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --help                    Show this help message
  %(prog)s                          Dry run - show what would be updated
  %(prog)s --execute                Actually update the metadata
  %(prog)s --log-level debug         Enable debug logging
  %(prog)s --catalog-file /path/to/catalog.json  Use custom catalog file
        """,
    )
    parser.add_argument(
        "--catalog-file",
        type=Path,
        default=CATALOG_FILE,
        help=f"Path to catalog.json file (default: {CATALOG_FILE})",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=R2R_DEFAULT_BASE_URL,
        help=f"R2R API base URL (default: {R2R_DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually update metadata (default is dry-run mode)",
    )
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error"],
        default="info",
        help="Set logging level (default: info)",
    )
    return parser


def process_matches(
    matches: list[dict[str, Any]], client: R2RClient, execute_mode: bool
) -> tuple[int, int]:
    """Process document matches and update metadata."""
    update_count = 0
    skip_count = 0

    for match in matches:
        doc_id = match["doc_id"]
        catalog_entry = match["catalog_entry"]
        document_row = match["document_row"]

        catalog_metadata = format_metadata_for_upload(catalog_entry)
        updates_needed = needs_metadata_update(document_row, catalog_metadata)

        if not updates_needed:
            logging.debug(f"Document {doc_id} already has complete metadata")
            skip_count += 1
            continue

        logging.info(f"Document {doc_id} needs updates: {list(updates_needed.keys())}")

        if not execute_mode:
            logging.info(f"DRY RUN: Would update {doc_id} with: {updates_needed}")
            update_count += 1
        else:
            if update_document_metadata(client, doc_id, updates_needed):
                update_count += 1

    return update_count, skip_count


def main() -> int:
    """
    Update R2R document metadata from HAL catalog.

    This script reads the HAL catalog, retrieves documents from R2R server,
    matches them by hal_id or title pattern, and updates missing metadata.
    By default runs in dry-run mode to show what would be updated.
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
        logging.info("Running in EXECUTE mode - will actually update metadata")
    else:
        logging.info("Running in DRY-RUN mode - will show what would be updated")
        logging.info("Use --execute to actually update metadata")

    catalog_by_hal_id = load_catalog(args.catalog_file)
    if not catalog_by_hal_id:
        return 1

    client = R2RClient(base_url=args.base_url)

    try:
        documents_df = get_existing_documents(client)
        if documents_df is None:
            logging.error("Failed to retrieve documents from R2R")
            return 1
    except Exception as e:
        logging.error(f"Failed to connect to R2R: {e}")
        return 1

    matches = match_documents_to_catalog(documents_df, catalog_by_hal_id)

    if not matches:
        logging.info("No documents matched to catalog entries")
        return 0

    update_count, skip_count = process_matches(matches, client, args.execute)

    logging.info(f"Summary: {update_count} documents updated, {skip_count} skipped")

    if not args.execute:
        logging.info("This was a dry run - no actual changes were made")
        logging.info("Use --execute to actually update metadata")

    return 0


if __name__ == "__main__":
    sys.exit(main())
