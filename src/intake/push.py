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
    MAX_FILE_SIZE,
    DOCUMENTS_DIR,
    R2R_DEFAULT_BASE_URL,
    setup_logging,
)
from intake.utils import (
    get_catalog_file,
    get_catalog_publications,
    get_existing_documents,
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
        help="Catalog JSON file containing metadata for publications (default: latest prepared catalog)",
    )
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error"],
        default="info",
        help="Set logging level.",
    )
    return parser.parse_args()


def load_catalog_local(catalog_file: Path) -> dict[str, dict[str, Any]]:
    """Load catalog data and index by hal_id."""
    if not catalog_file.exists():
        logging.error("Catalog file not found: %s", catalog_file)
        logging.error(
            "Run hal_query.py and prepare_catalog.py first to create the catalog."
        )
        return {}

    try:
        catalog_data = json.loads(catalog_file.read_text(encoding="utf-8"))
        publications = get_catalog_publications(catalog_data)
        catalog_by_hal_id = {}

        for pub in publications:
            if "halId_s" in pub:
                hal_id = pub["halId_s"]
                catalog_by_hal_id[hal_id] = pub

        
        logging.info(
            "Catalog loaded: %d records",
            len(catalog_by_hal_id),
        )
        return catalog_by_hal_id

    except Exception as e:
        logging.error("Failed to load catalog: %s", e)
        return {}


def establish_available_documents(
    catalog_file: Path, pdf_dir: Path
) -> tuple[dict[str, dict[str, Any]], int, int, int, int]:
    """
    Walk the catalog and verify PDF files exist in the documents directory.

    Returns:
        - Dictionary of available documents (hal_id -> metadata)
        - Total number of records in catalog
        - Number of missing PDF files

    """
    catalog_by_hal_id = load_catalog_local(catalog_file)

    available_docs = {}
    missing_count = 0
    oversized_count = 0
    non_pdf_count = 0

    for hal_id, metadata in catalog_by_hal_id.items():
        if "pdf_url" not in metadata and "fileMain_s" not in metadata:
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
                logging.warning(
                    "File too large for %s: %s (> %d bytes)",
                    hal_id, candidate.name, MAX_FILE_SIZE
                )
                oversized_count += 1
            else:
                available_docs[hal_id] = metadata
        else:
            other_files = (
                list(pdf_dir.glob(f"{hal_id}.*"))
                + list(pdf_dir.glob(f"{hal_id.replace('-', '_')}.*"))
            )
            if other_files:
                logging.warning(
                    "Excluded non-PDF file(s) for %s: %s",
                    hal_id, [f.name for f in other_files]
                )
                non_pdf_count += 1
            else:
                logging.error("Missing PDF file for %s", hal_id)
                missing_count += 1

    
    logging.info(
        "Local summary: %d valid | %d missing | %d oversized | %d non-PDF | out of %d catalog entries",
        len(available_docs),
        missing_count,
        oversized_count,
        non_pdf_count,
        len(catalog_by_hal_id),
    )
    logging.debug("Available docs: %s", list(available_docs.keys()))

    return (
        available_docs,
        len(catalog_by_hal_id),
        missing_count,
        oversized_count,
        non_pdf_count,
    )


def exclude_oversized_pdfs(pdf_files: list[Path]) -> list[Path]:
    """Exclude PDF files exceeding the maximum allowed size."""
    filtered_files = []
    excluded_files = 0

    for pdf_file in pdf_files:
        if pdf_file.stat().st_size > MAX_FILE_SIZE:
            logging.warning(
                "Excluding oversized file (>%d bytes): %s", MAX_FILE_SIZE, pdf_file
            )
            excluded_files += 1
        else:
            filtered_files.append(pdf_file)

    if excluded_files:
        logging.info("Excluded %d oversized file(s) from upload list.", excluded_files)

    return filtered_files


def get_uploadable_documents(
    available_docs: dict[str, dict[str, Any]],
    existing_documents: dict[str, str],
    pdf_dir: Path,
) -> list[Path]:
    """
    Ne traiter ici que des fichiers PDF.
    Get documents that are available locally but not successfully uploaded to server.
    
    Returns list of PDF file paths that should be uploaded.
    """
    uploadable_pdfs = []

    for hal_id, metadata in available_docs.items():
        formatted_metadata = format_metadata_for_upload(metadata)
        doc_title = formatted_metadata.get("title", hal_id)

        ingestion_status = existing_documents.get(doc_title)

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
            elif "pdf_url" in pub:
                filename = hashlib.md5(pub["pdf_url"].encode()).hexdigest()
                metadata_by_file[filename] = pub
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


def upload_pdfs(
    pdf_files: list[Path],
    client: R2RClient,
    existing_documents: dict[str, str],
    metadata_by_file: dict[str, dict[str, object]],
    collection: str | None = None,
    max_upload: int = 0,
) -> tuple[int, int, list[tuple[Path, str]]]:
    """Upload new PDFs and skip existing ones. Stop after max_upload successful uploads if set."""
    success_count = 0
    skipped_count = 0
    failed_files: list[tuple[Path, str]] = []

    if max_upload == 0:
        logging.info(
            "Dry run mode: No files will be uploaded. Try using --max-upload 3."
        )
        return success_count, skipped_count, failed_files

    for pdf_file in pdf_files:
        if max_upload > 0 and success_count >= max_upload:
            logging.info("Reached maximum upload limit: %d files.", max_upload)
            break

        try:
            logging.info(
                "Uploading %d/%d: %s", success_count + 1, len(pdf_files), pdf_file.name
            )
            # Utiliser le titre du document pour la recherche d'existant
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
                    "Skipping file with ingestion_status='%s': %s",
                    ingestion_status,
                    pdf_file,
                )
                skipped_count += 1
                continue

            if ingestion_status == "failed":
                logging.warning(
                    "Re-uploading file with previous ingestion_status='failed': %s",
                    pdf_file,
                )
            else:
                logging.debug("Uploading new file: %s", pdf_file)

            # Prepare upload parameters
            kwargs = {}
            if collection:
                kwargs["collection_name"] = collection

            metadata = None
            file_stem = pdf_file.stem
            if file_stem in metadata_by_file:
                raw_metadata = metadata_by_file[file_stem]
                metadata = format_metadata_for_upload(raw_metadata)

                logging.debug("Adding metadata to %s: %s", pdf_file.name, metadata)
            else:
                logging.debug("No metadata found for file: %s", pdf_file.name)

            # Upload
            client.documents.create(
                file_path=str(pdf_file),
                metadata=metadata,
                **kwargs,  # Other parameters like collection_name
            )

            logging.info("Successfully uploaded file: %s", pdf_file)
            success_count += 1

        except Exception as e:
            logging.error("Failed to process file %s: %s", pdf_file, str(e))
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
    existing_documents: dict[str, str],
    uploadable_files: list[Path],
    success_count: int,
    skipped_count: int,
    failed_files: list[tuple[Path, str]],
) -> int:
    """Print upload statistics and return appropriate exit code."""
    logging.info("=== UPLOAD STATISTICS ===")
    
    logging.info(
        "Catalog records loaded: %d",
        total_records,
    )
    logging.info("Available documents: %d", len(available_docs))
    logging.info("Missing PDF files: %d", missing_files)
    logging.info("Documents on server: %d", len(existing_documents))
    logging.info("Uploadable documents: %d", len(uploadable_files))
    logging.info("Successfully uploaded: %d", success_count)
    logging.info("Skipped: %d", skipped_count)
    logging.info("Failed: %d", len(failed_files))

    if failed_files:
        logging.error("Failed files:")
        for file, error in failed_files:
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

    (
        available_docs,
        total_records,
        missing_files,
        oversized_files,
        non_pdf_files,
    ) = establish_available_documents(catalog_file, args.dir)

    if not available_docs:
        logging.error("No documents available for upload")
        return 1

    client = R2RClient(base_url=args.base_url)
    if not check_r2r_connection(client):
        logging.error("Cannot connect to R2R. Please check if the service is running.")
        return 2

    documents_df = get_existing_documents(client)
    if documents_df is None:
        logging.error("Failed to retrieve documents from R2R.")
        return 3

    existing_documents = {}
    for _, doc in documents_df.iterrows():
        existing_documents[doc["title"]] = doc["ingestion_status"]

    logging.info(
        "Server summary: %d documents present",
        len(existing_documents),
    )

    uploadable_pdfs = get_uploadable_documents(
        available_docs, existing_documents, args.dir
    )

    if not uploadable_pdfs:
        logging.info("No new PDF documents to upload")
        return 0

    uploadable_pdfs = exclude_oversized_pdfs(uploadable_pdfs)
    if not uploadable_pdfs:
        logging.error("No valid PDF files to upload after filtering oversized files.")
        return 4

    metadata_by_file = load_metadata(catalog_file)

    success_count, skipped_count, failed_files = upload_pdfs(
        uploadable_pdfs,
        client,
        existing_documents,
        metadata_by_file,
        collection=args.collection,
        max_upload=args.max_upload,
    )

    return print_upload_statistics(
        total_records,
        list(available_docs.values()),
        missing_files,
        existing_documents,
        uploadable_pdfs,
        success_count,
        skipped_count,
        failed_files,
    )


if __name__ == "__main__":
    sys.exit(main())
