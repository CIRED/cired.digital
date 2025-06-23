#!/usr/bin/env python
"""
Upload PDFs with their metadata into an R2R instance.

Requirements:
    - Python 3.11+
    - r2r-sdk (normally installed in the virtual environment)

Exit codes:
    0 - Success (all operations completed successfully)
    1 - No valid PDF files found to upload
    2 - Some files failed to upload (see logs for details)
    3 - Failed to connect to R2R service
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from r2r import R2RClient

from intake.config import (
    CATALOG_FILE,
    DOCUMENTS_DIR,
    MAX_FILE_SIZE,
    R2R_DEFAULT_BASE_URL,
    setup_logging,
)
from intake.utils import (
    get_catalog_file,
    get_catalog_publications,
    get_latest_prepared_catalog,
    get_server_documents,
    load_catalog_by_hal_id,
)


def get_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Push PDF files into R2R using catalog-based discovery.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=DOCUMENTS_DIR,
        help="Directory containing PDF files for upload and verification.",
    )
    parser.add_argument(
        "--base-url", type=str, default=R2R_DEFAULT_BASE_URL, help="R2R API URL."
    )
    parser.add_argument(
        "--collection", type=str, help="Collection name for uploaded documents."
    )
    parser.add_argument(
        "--max-upload",
        type=int,
        default=0,
        help="Maximum number of PDFs to upload (0 = dry run).",
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=get_latest_prepared_catalog(),
        help="Catalog JSON file containing metadata for publications (default: latest prepared catalog)",
    )
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error"],
        default="info",
        help="Set logging level.",
    )
    return parser.parse_args()


def establish_available_documents(
    catalog_file: Path, pdf_dir: Path
) -> tuple[dict[str, dict[str, Any]], int, int]:
    """
    Walk the catalog and verify PDF files exist in the documents directory.

    Returns:
        - Dictionary of available documents (hal_id -> metadata)
        - Total number of records in catalog
        - Number of missing PDF files
        - Number of oversized PDF files
        - Number of non-PDF files

    """
    catalog_by_hal_id, total_records = load_catalog_by_hal_id(catalog_file)

    available_docs = {}
    missing_count = 0
    oversized_count = 0

    for hal_id, metadata in catalog_by_hal_id.items():
        if "fileMain_s" not in metadata:
            logging.debug("Skipping %s: No PDF available on HAL", hal_id)
            continue

        pdf_file_hyphen = pdf_dir / f"{hal_id}.pdf"
        pdf_file_underscore = pdf_dir / f"{hal_id.replace('-', '_')}.pdf"

        # Check existence and size
        candidate = None
        if pdf_file_hyphen.exists():
            candidate = pdf_file_hyphen
        elif pdf_file_underscore.exists():
            candidate = pdf_file_underscore

        if candidate:
            if candidate.stat().st_size > MAX_FILE_SIZE:
                logging.debug(
                    "File too large for %s: %s has size %d bytes (> %d bytes)",
                    hal_id,
                    candidate.name,
                    candidate.stat().st_size,
                    MAX_FILE_SIZE,
                )
                oversized_count += 1
            else:
                available_docs[hal_id] = metadata
        else:
            other_files = list(pdf_dir.glob(f"{hal_id}.*")) + list(
                pdf_dir.glob(f"{hal_id.replace('-', '_')}.*")
            )
            if other_files:
                logging.debug(
                    "Excluded non-PDF file(s) for %s: %s",
                    hal_id,
                    [f.name for f in other_files],
                )
            else:
                logging.debug("Missing PDF file for %s", hal_id)
                missing_count += 1

    logging.info("Valid documents: %d", len(available_docs))
    logging.info("Missing PDF files: %d", missing_count)
    logging.info("Total catalog entries: %d", len(catalog_by_hal_id))
    logging.debug("Available docs: %s", list(available_docs.keys()))

    return available_docs, total_records, missing_count, oversized_count


def get_uploadable_documents(
    available_docs: dict[str, dict[str, Any]],
    server_documents: dict[str, dict[str, Any]],
    pdf_dir: Path,
) -> list[Path]:
    """
    Get documents that are available locally, type PDF, not oversized.

    Returns a list of PDF file paths that could be uploaded.
    """
    uploadable_pdfs = []

    for hal_id in available_docs:
        # Lookup par hal_id
        entry = server_documents.get(hal_id)
        ingestion_status = entry["status"] if entry else None

        if ingestion_status not in (None, "failed"):
            continue

        pdf_file_hyphen = pdf_dir / f"{hal_id}.pdf"
        pdf_file_underscore = pdf_dir / f"{hal_id.replace('-', '_')}.pdf"

        if pdf_file_hyphen.exists():
            uploadable_pdfs.append(pdf_file_hyphen)
        elif pdf_file_underscore.exists():
            uploadable_pdfs.append(pdf_file_underscore)

    logging.info(
        "Ready to upload: %d PDFs (valid locally but missing or failed on server)",
        len(uploadable_pdfs),
    )
    logging.debug("Uploadable PDFs: %s", [f.name for f in uploadable_pdfs])

    return uploadable_pdfs


def load_metadata(metadata_file: Path) -> dict[str, dict[str, object]]:
    """
    Load metadata from the publications JSON file.

    Returns a dictionary where keys are filename stems (halId_s or hash) and
    values are publication metadata dictionaries.
    """
    metadata_by_file: dict[str, dict[str, object]] = {}

    if not metadata_file.exists():
        logging.warning("Metadata file not found: %s", metadata_file)
        return metadata_by_file

    try:
        catalog_data = json.loads(metadata_file.read_text(encoding="utf-8"))
        publications = get_catalog_publications(catalog_data)
        for pub in publications:
            # Generate the same filename as download.py does
            if "halId_s" in pub:
                # Create two keys - one with hyphen and one with underscore
                hal_id = pub["halId_s"]
                filename_hyphen = hal_id  # Original key with hyphen (hal-XXXXXX)
                filename_underscore = hal_id.replace(
                    "-", "_"
                )  # Alternative key with underscore (hal_XXXXXX)

                metadata_by_file[filename_hyphen] = pub
                metadata_by_file[filename_underscore] = pub
            else:
                continue  # Skip if we can't determine filename

        logging.info(
            "Loaded metadata for %d publications from %s",
            len(publications),
            metadata_file,
        )
    except Exception as e:
        logging.error("Failed to load metadata file %s: %s", metadata_file, str(e))

    return metadata_by_file


def first_if_list(value: object) -> str | None:
    """
    Return the string itself if it's a string, or the first element if it's a list of strings.

    Use for potentially multilingual fields.
    """
    if isinstance(value, str):
        return value
    elif isinstance(value, list) and value and isinstance(value[0], str):
        return value[0]
    return None


def format_metadata_for_upload(metadata: dict[str, object]) -> dict[str, str]:
    """Format HAL metadata for R2R upload."""
    # Define field mappings: HAL field -> R2R field
    # TODO: refactor
    #   Reread HAL API doc and distinguish three kind  of fields:
    #   multi-valued to be kept entirely (authors)
    #   multi-valued to be truncated to first element (supposedly English)
    #   guaranteed scalar fields
    field_mapping = {
        "title_s": "title",
        "label_s": "citation",
        "abstract_s": "description",
        "producedDate_tdate": "publication_date",
        "doiId_s": "doi",
        "halId_s": "hal_id",
        "docType_s": "document_type",
    }

    result: dict[str, str] = {}

    # Keep only the first in possibly multi-valued
    for hal_field, r2r_field in field_mapping.items():
        if value := first_if_list(metadata.get(hal_field)):
            result[r2r_field] = str(value)

    # For authors, keep all the list
    if authors := metadata.get("authFullName_s"):
        result["authors"] = str(authors)

    # Add source URL
    if "doi" in result:
        result["source_url"] = f"https://doi.org/{result['doi']}"
    elif "hal_id" in result:
        result["source_url"] = f"https://hal.science/{result['hal_id']}"

    return result


def upload_documents(
    document_paths: list[Path],
    client: R2RClient,
    server_documents: dict[str, dict[str, object]],
    metadata_by_file: dict[str, dict[str, object]],
    collection: str | None = None,
    max_upload: int = 0,
) -> tuple[int, int, list[tuple[Path, str]]]:
    """Upload documents, skipping those already present or failed on the server. Stop after max_upload successful uploads if set."""
    success_count = 0
    skipped_count = 0
    failed_documents: list[tuple[Path, str]] = []

    if max_upload == 0:
        logging.info(
            "Dry run mode: No files will be uploaded. Try using --max-upload 3."
        )
        return success_count, skipped_count, failed_documents

    for doc_path in document_paths:
        if max_upload > 0 and success_count >= max_upload:
            logging.info("Reached maximum upload limit: %d files.", max_upload)
            break

        try:
            logging.info(
                "Uploading %d/%d: %s",
                success_count + 1,
                len(document_paths),
                doc_path.name,
            )
            file_stem = doc_path.stem
            # Lookup par hal_id (underscore → tiret)
            hal_id = file_stem.replace("_", "-")
            entry = server_documents.get(hal_id)
            ingestion_status = entry["status"] if entry else None

            if ingestion_status not in (None, "failed"):
                logging.debug(
                    "Skipping document with ingestion_status='%s': %s",
                    ingestion_status,
                    doc_path,
                )
                skipped_count += 1
                continue

            if ingestion_status == "failed":
                logging.warning(
                    "Re-uploading document with previous ingestion_status='failed': %s",
                    doc_path,
                )
            else:
                logging.debug("Uploading new document: %s", doc_path)

            # Ready to upload, see API documentation:
            # https://r2r-docs.sciphi.ai/api-and-sdks/documents/create-document

            # Prepare upload parameters
            kwargs = {}
            if collection:
                kwargs["collection_name"] = collection

            metadata = None
            file_stem = doc_path.stem
            if file_stem in metadata_by_file:
                raw_metadata = metadata_by_file[file_stem]
                metadata = format_metadata_for_upload(raw_metadata)

                logging.debug("Adding metadata to %s: %s", doc_path.name, metadata)
            else:
                logging.debug("No metadata found for file: %s", doc_path.name)

            # Upload
            client.documents.create(
                file_path=str(doc_path),
                metadata=metadata,
                **kwargs,  # Other parameters like collection_name
            )

            logging.info("Successfully uploaded document: %s", doc_path)
            success_count += 1

        except Exception as e:
            logging.error("Failed to process document %s: %s", doc_path, str(e))
            failed_documents.append((doc_path, str(e)))

    return success_count, skipped_count, failed_documents


def check_r2r_connection(client: R2RClient) -> bool:
    """
    Check if R2R is accessible before starting uploads.

    Returns
    -------
        True if R2R responds, False otherwise.

    """
    try:
        # Try a simple health check - listing documents with limit 1
        _ = client.documents.list(limit=1)
        logging.info("R2R connection successful.")
        return True
    except Exception as e:
        logging.error("Failed to connect to R2R: %s", e)
        return False


def setup_catalog_file(args: argparse.Namespace) -> tuple[Path | None, int]:
    """Determine which catalog file to use based on arguments."""
    catalog_file = get_catalog_file(args.catalog)
    if not catalog_file:
        logging.error(
            "No catalog file found. Run hal_query.py and prepare_catalog.py first."
        )
        return None, 1

    if catalog_file == CATALOG_FILE:
        logging.info("Using legacy catalog file: %s", CATALOG_FILE)
    else:
        logging.info("Using catalog file: %s", catalog_file)

    return catalog_file, 0


def print_upload_statistics(
    total_records: int,
    available_docs: list[dict[str, Any]],
    missing_files: int,
    oversized_files: int,
    server_documents: dict[str, dict[str, Any]],
    uploadable_files: list[Path],
    success_count: int,
    skipped_count: int,
    failed_documents: list[tuple[Path, str]],
) -> int:
    """Print upload statistics and return appropriate exit code."""
    logging.info("=== UPLOAD STATISTICS ===")
    logging.info("Total catalog entries: %d", total_records)
    logging.info("Missing PDF files: %d", missing_files)
    logging.info("Oversized PDF files: %d", oversized_files)

    logging.info("Local valid documents: %d", len(available_docs))
    logging.info("Documents on server: %d", len(server_documents))
    logging.info("Uploadable documents: %d", len(uploadable_files))
    logging.info("Successfully uploaded: %d", success_count)
    logging.info("Skipped: %d", skipped_count)
    logging.info("Failed: %d", len(failed_documents))
    logging.info("Résumé : total=%d, manquants=%d, volumineux=%d, valides_locaux=%d, sur_serveur=%d, à_téléverser=%d, téléversés=%d, ignorés=%d, échecs=%d",
                 total_records, missing_files, oversized_files, len(available_docs), len(server_documents), len(uploadable_files), success_count, skipped_count, len(failed_documents))

    if failed_documents:
        logging.error("Failed files:")
        for file, error in failed_documents:
            logging.error("- %s: %s", file, error)
        return 5

    return 0


def main() -> int:
    """
    Upload PDFs with metadata to an R2R instance using catalog-based discovery.

    This function implements a 5-step process:
    1. Establish available documents from catalog
    2. Get existing documents from server
    3. Find uploadable documents (available but not on server)
    4. Upload documents respecting limits
    5. Print statistics
    """
    args = get_args()

    log_levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
    }

    setup_logging(
        level=log_levels[args.log_level],
        simple_format=True,
    )

    catalog_file, exit_code = setup_catalog_file(args)
    if exit_code != 0:
        return exit_code

    if catalog_file is None:
        logging.error("No catalog file available")
        return 1

    available_docs, total_records, missing_files, oversized_files = establish_available_documents(
        catalog_file, args.dir
    )

    if not available_docs:
        logging.error("No documents available for upload")
        return 1

    client = R2RClient(base_url=args.base_url)
    if not check_r2r_connection(client):
        logging.error("Cannot connect to R2R. Please check if the service is running.")
        return 2

    documents_df = get_server_documents(client)
    if documents_df is None:
        logging.error("Failed to retrieve documents from R2R.")
        return 3

    # On indexe les docs par metadata.hal_id et on conserve docid + status
    server_documents: dict[str, dict[str, object]] = {}
    for _, row in documents_df.iterrows():
        hal_id = row["meta_hal_id"]
        if pd.isna(hal_id):
            continue
        server_documents[hal_id] = {
            "docid": row.get("id") or row.get("document_id"),
            "status": row["ingestion_status"],
        }

    logging.info(
        "Server summary: %d documents present",
        len(server_documents),
    )

    uploadable_pdfs = get_uploadable_documents(
        available_docs, server_documents, args.dir
    )

    if not uploadable_pdfs:
        logging.info("No new PDF documents to upload")
        return 0

    metadata_by_file = load_metadata(catalog_file)

    success_count, skipped_count, failed_documents = upload_documents(
        uploadable_pdfs,
        client,
        server_documents,
        metadata_by_file,
        collection=args.collection,
        max_upload=args.max_upload,
    )

    return print_upload_statistics(
        total_records,
        list(available_docs.values()),
        missing_files,
        oversized_files,
        server_documents,
        uploadable_pdfs,
        success_count,
        skipped_count,
        failed_documents,
    )


if __name__ == "__main__":
    sys.exit(main())
