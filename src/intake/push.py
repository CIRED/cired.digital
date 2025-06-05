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
import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Any

from r2r import R2RClient

from intake.config import (
    CATALOG_FILE,
    DEFAULT_MAX_UPLOAD,
    MAX_FILE_SIZE,
    PDF_DIR,
    R2R_DEFAULT_BASE_URL,
    setup_logging,
)
from intake.verify import get_existing_documents as get_existing_documents_from_verify


def get_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Push PDF files into R2R using catalog-based discovery.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=PDF_DIR,
        help=f"Directory containing PDF files for verification. (default: {PDF_DIR})",
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
        default=DEFAULT_MAX_UPLOAD,
        help="Maximum number of PDFs to upload (0 = dry run no upload).",
    )
    parser.add_argument(
        "--metadata-file",
        type=Path,
        default=CATALOG_FILE,
        help=f"Catalog JSON file containing metadata for publications. (default: {CATALOG_FILE})",
    )
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Skip sending metadata with documents.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable detailed debug output.",
    )
    return parser.parse_args()


def load_catalog_local(catalog_file: Path) -> dict[str, dict[str, Any]]:
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

        logging.info("Loaded %d publications from catalog", len(catalog_by_hal_id))
        return catalog_by_hal_id

    except Exception as e:
        logging.error(f"Failed to load catalog: {e}")
        return {}


def establish_available_documents(
    catalog_file: Path, pdf_dir: Path
) -> tuple[dict[str, dict[str, Any]], int, int]:
    """
    Walk the catalog and verify PDF files exist in the pdfs directory.

    Returns:
        - Dictionary of available documents (hal_id -> metadata)
        - Total number of records in catalog
        - Number of missing PDF files

    """
    catalog_by_hal_id = load_catalog_local(catalog_file)

    available_docs = {}
    missing_count = 0

    for hal_id, metadata in catalog_by_hal_id.items():
        pdf_file_hyphen = pdf_dir / f"{hal_id}.pdf"
        pdf_file_underscore = pdf_dir / f"{hal_id.replace('-', '_')}.pdf"

        if pdf_file_hyphen.exists() or pdf_file_underscore.exists():
            available_docs[hal_id] = metadata
        else:
            logging.error(f"Missing PDF file for {hal_id}")
            missing_count += 1

    logging.info(
        f"Available documents: {len(available_docs)}, Missing files: {missing_count}, Total records: {len(catalog_by_hal_id)}"
    )
    logging.debug(f"Available docs: {list(available_docs.keys())}")

    return available_docs, len(catalog_by_hal_id), missing_count


def exclude_oversized_pdfs(pdf_files: list[Path]) -> list[Path]:
    """Exclude PDF files exceeding the maximum allowed size."""
    filtered_files = []
    excluded_files = 0

    for pdf_file in pdf_files:
        if pdf_file.stat().st_size > MAX_FILE_SIZE:
            logging.warning(
                f"Excluding oversized file (>{MAX_FILE_SIZE} bytes): {pdf_file}"
            )
            excluded_files += 1
        else:
            filtered_files.append(pdf_file)

    if excluded_files:
        logging.info(f"Excluded {excluded_files} oversized file(s) from upload list.")

    return filtered_files


def get_uploadable_documents(
    available_docs: dict[str, dict[str, Any]], existing_documents: dict[str, str], pdf_dir: Path
) -> list[Path]:
    """
    Get documents that are available locally but not successfully uploaded to server.

    Returns list of PDF file paths that should be uploaded.
    """
    uploadable_files = []

    for hal_id, metadata in available_docs.items():
        formatted_metadata = format_metadata_for_upload(metadata)
        doc_title = formatted_metadata.get("title", hal_id)

        ingestion_status = existing_documents.get(doc_title)

        if ingestion_status not in (None, "failed"):
            continue

        pdf_file_hyphen = pdf_dir / f"{hal_id}.pdf"
        pdf_file_underscore = pdf_dir / f"{hal_id.replace('-', '_')}.pdf"

        if pdf_file_hyphen.exists():
            uploadable_files.append(pdf_file_hyphen)
        elif pdf_file_underscore.exists():
            uploadable_files.append(pdf_file_underscore)

    logging.info(f"Uploadable documents: {len(uploadable_files)}")
    logging.debug(f"Uploadable files: {[f.name for f in uploadable_files]}")

    return uploadable_files


def load_metadata(metadata_file: Path) -> dict[str, dict[str, object]]:
    """
    Load metadata from the publications JSON file.

    Returns a dictionary where keys are filename stems (halId_s or hash) and
    values are publication metadata dictionaries.
    """
    metadata_by_file: dict[str, dict[str, object]] = {}

    if not metadata_file.exists():
        logging.warning(f"Metadata file not found: {metadata_file}")
        return metadata_by_file

    try:
        publications = json.loads(metadata_file.read_text(encoding="utf-8"))
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
            elif "pdf_url" in pub:
                filename = hashlib.md5(pub["pdf_url"].encode()).hexdigest()
                metadata_by_file[filename] = pub
            else:
                continue  # Skip if we can't determine filename

        logging.info(
            f"Loaded metadata for {len(publications)} publications from {metadata_file}"
        )
    except Exception as e:
        logging.error(f"Failed to load metadata file {metadata_file}: {str(e)}")

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


def upload_pdfs(
    pdf_files: list[Path],
    client: R2RClient,
    existing_documents: dict[str, str],
    metadata_by_file: dict[str, dict[str, object]],
    collection: str | None = None,
    max_upload: int = 0,
    include_metadata: bool = True,
) -> tuple[int, int, list[tuple[Path, str]]]:
    """Upload new PDFs and skip existing ones. Stop after max_upload successful uploads if set."""
    success_count = 0
    skipped_count = 0
    failed_files = []

    for pdf_file in pdf_files:
        if max_upload > 0 and success_count >= max_upload:
            logging.info(f"Reached maximum upload limit: {max_upload} files.")
            break

        try:
            logging.debug(f"Processing file: {pdf_file}")
            # Utiliser le titre du document pour la recherche d’existant
            file_stem = pdf_file.stem
            raw_metadata_for_title = metadata_by_file.get(file_stem, {})
            formatted_for_title = (
                format_metadata_for_upload(raw_metadata_for_title)
                if raw_metadata_for_title
                else {}
            )
            doc_title = formatted_for_title.get("title", file_stem)
            ingestion_status = existing_documents.get(doc_title)

            if ingestion_status not in (None, "failed"):
                logging.debug(
                    f"Skipping file with ingestion_status='{ingestion_status}': {pdf_file}"
                )
                skipped_count += 1
                continue

            if ingestion_status == "failed":
                logging.warning(
                    f"Re-uploading file with previous ingestion_status='failed': {pdf_file}"
                )
            else:
                logging.debug(f"Uploading new file: {pdf_file}")

            # Prepare upload parameters
            kwargs = {}
            if collection:
                kwargs["collection_name"] = collection

            # Add metadata if available
            metadata = None
            if include_metadata:
                file_stem = pdf_file.stem
                if file_stem in metadata_by_file:
                    raw_metadata = metadata_by_file[file_stem]
                    formatted_metadata = format_metadata_for_upload(raw_metadata)

                    # CHANGE: Pass metadata as a separate parameter, not mixed with other kwargs
                    metadata = formatted_metadata
                    logging.debug(
                        f"Adding metadata to {pdf_file.name}: {formatted_metadata}"
                    )
                else:
                    logging.debug(f"No metadata found for file: {pdf_file.name}")

            # Upload the document - CHANGE: Pass metadata as a separate parameter
            client.documents.create(
                file_path=str(pdf_file),
                metadata=metadata,  # Pass metadata as a separate parameter
                **kwargs,  # Other parameters like collection_name
            )

            logging.info(f"Successfully uploaded file: {pdf_file}")
            success_count += 1

        except Exception as e:
            logging.error(f"Failed to process file {pdf_file}: {str(e)}")
            failed_files.append((pdf_file, str(e)))

    return success_count, skipped_count, failed_files


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
        logging.error(f"Failed to connect to R2R: {e}")
        return False


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

    setup_logging(
        level=logging.DEBUG if args.verbose else None,
        simple_format=True,
    )

    available_docs, total_records, missing_files = establish_available_documents(
        args.metadata_file, args.dir
    )

    if not available_docs:
        logging.error("No documents available for upload")
        return 1

    client = R2RClient(base_url=args.base_url)
    if not check_r2r_connection(client):
        logging.error("Cannot connect to R2R. Please check if the service is running.")
        return 3

    documents_df = get_existing_documents_from_verify(client)
    if documents_df is None:
        logging.error("Failed to retrieve documents from R2R.")
        return 3

    existing_documents = {}
    for _, doc in documents_df.iterrows():
        existing_documents[doc["title"]] = doc["ingestion_status"]

    uploadable_files = get_uploadable_documents(
        available_docs, existing_documents, args.dir
    )

    if not uploadable_files:
        logging.info("No new documents to upload")
        return 0

    uploadable_files = exclude_oversized_pdfs(uploadable_files)
    if not uploadable_files:
        logging.error("No valid PDF files to upload after filtering oversized files.")
        return 1

    metadata_by_file = {}
    if not args.no_metadata:
        metadata_by_file = load_metadata(args.metadata_file)

    success_count, skipped_count, failed_files = upload_pdfs(
        uploadable_files,
        client,
        existing_documents,
        metadata_by_file,
        collection=args.collection,
        max_upload=args.max_upload,
        include_metadata=not args.no_metadata,
    )

    logging.info("=== UPLOAD STATISTICS ===")
    logging.info(f"Total catalog records: {total_records}")
    logging.info(f"Available documents: {len(available_docs)}")
    logging.info(f"Missing PDF files: {missing_files}")
    logging.info(f"Documents on server: {len(existing_documents)}")
    logging.info(f"Uploadable documents: {len(uploadable_files)}")
    logging.info(f"Successfully uploaded: {success_count}")
    logging.info(f"Skipped: {skipped_count}")
    logging.info(f"Failed: {len(failed_files)}")

    if failed_files:
        logging.error("Failed files:")
        for file, error in failed_files:
            logging.error(f"- {file}: {error}")
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
