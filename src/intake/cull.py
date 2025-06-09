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
import unicodedata
import re
from r2r import R2RClient

from intake.config import CATALOG_FILE, R2R_DEFAULT_BASE_URL, setup_logging
from intake.push import format_metadata_for_upload
from intake.utils import (
    get_catalog_file,
    get_server_documents,
    load_catalog_by_hal_id,
)


def match_documents_to_catalog(
    documents_df: pd.DataFrame, catalog_by_hal_id: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    """Match server documents to catalog entries."""
    matches = []

    for _, doc in documents_df.iterrows():
        doc_id = doc["id"]
        meta_hal_id = doc.get("meta_hal_id")

        catalog_entry = None

        if meta_hal_id and meta_hal_id in catalog_by_hal_id:
            catalog_entry = catalog_by_hal_id[meta_hal_id]

        if catalog_entry:
            matches.append(
                {
                    "doc_id": doc_id,
                    "title": doc.get("title", ""),
                    "meta_hal_id": meta_hal_id,
                    "catalog_entry": catalog_entry,
                    "document_row": doc,
                }
            )
        else:
            logging.warning("Unable to match doc_id %s (%s)", doc_id, doc.get("title", ""))

    logging.info(
        "Matched %d documents to catalog entries, %d documents remain orphan",
        len(matches),
        len(documents_df) - len(matches),
    )
    return matches


def needs_metadata_update(
    document_row: pd.Series[Any], catalog_metadata: dict[str, Any]
) -> dict[str, Any]:
    """Return the metadata that need to be aligned on the catalog."""
    logging.debug("Inspecting for unaligned metadata")
    logging.debug("Document: %s", str(document_row))
    catalog_metadata = format_metadata_for_upload(catalog_metadata)
    logging.debug("Catalog:  %s", str(catalog_metadata))

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

        updates_needed[catalog_field] = catalog_value

    if updates_needed != {}:
        logging.debug("Updates needed = %s", str(updates_needed))

    return updates_needed


def delete_document(doc_id: str, client: R2RClient, execute_mode: bool) -> bool:
    """Delete a document."""
    logging.debug("Trying to delete document %s", doc_id)

    if not execute_mode:
        logging.info("DRY RUN: not really doing it.")
        return True

    try:
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


def process_matches(
    matches: list[dict[str, Any]], client: R2RClient, execute_mode: bool
) -> tuple[int, int]:
    """Process document matches and delete misdescribed documents."""
    delete_count = 0
    skip_count = 0

    for match in matches:
        doc_id = match["doc_id"]
        catalog_entry = match["catalog_entry"]
        document_row = match["document_row"]

        updates_needed = needs_metadata_update(document_row, catalog_entry)

        if not updates_needed:
            logging.debug(f"Document {doc_id} metadata match the catalog")
            skip_count += 1
            continue

        logging.info(
            f"Document {doc_id} metadata mismatch: {list(updates_needed.keys())}"
        )
        if delete_document(doc_id, client, execute_mode):
            delete_count += 1

    return delete_count, skip_count


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

    matches = match_documents_to_catalog(documents_df, catalog_by_hal_id)

    # Identify orphans (documents missing from catalog)
    matched_ids = {m["doc_id"] for m in matches}
    orphans = [row for _, row in documents_df.iterrows() if row["id"] not in matched_ids]

    # Identify mismatches (documents with inconsistent metadata)
    mismatches = []
    for match in matches:
        diffs = needs_metadata_update(match["document_row"], match["catalog_entry"])
        if diffs:
            mismatches.append({"doc_id": match["doc_id"], "diffs": diffs})

    # Select documents to process based on target
    to_process = []
    if args.target in ("missing", "both"):
        to_process += [("missing", row["id"]) for row in orphans]
    if args.target in ("mismatch", "both"):
        to_process += [("mismatch", m["doc_id"], m["diffs"]) for m in mismatches]

    if not to_process:
        logging.info("No documents to delete based on target criteria")
        return 0

    delete_count = 0
    for item in to_process:
        if item[0] == "missing":
            logging.info(f"Document {item[1]} absent du catalogue")
            if delete_document(item[1], client, args.execute):
                delete_count += 1
        else:
            doc_id, diffs = item[1], item[2]
            logging.info(f"Document {doc_id} métadonnées divergentes: {list(diffs.keys())}")
            if delete_document(doc_id, client, args.execute):
                delete_count += 1

    logging.info(f"Résumé: {delete_count} documents supprimés")

    if not args.execute:
        logging.info("Mode dry-run - aucune suppression effective")
        logging.info("Utilisez --execute pour supprimer réellement")

    return 0


if __name__ == "__main__":
    sys.exit(main())
