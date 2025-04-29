"""Upload PDFs into an R2R instance."""

import argparse
import logging
import sys
from collections import Counter
from pathlib import Path

from r2r import R2RClient

logger = logging.getLogger(__name__)

DEFAULT_MAX_UPLOAD = 5
MAX_FILE_SIZE = 30000000


def get_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Push PDF files into R2R using the official SDK.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--dir",
        type=Path,
        required=True,
        help="Directory containing PDF files. (required)",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively search PDFs in subdirectories.",
    )
    parser.add_argument(
        "--base-url", type=str, default="http://localhost:7272", help="R2R API URL."
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
        "--verbose",
        action="store_true",
        help="Enable detailed debug output.",
    )
    return parser.parse_args()


def prepare_pdf_files(args: argparse.Namespace) -> list[Path]:
    """Prepare and validate the list of PDF files based on user arguments."""
    directory = args.dir
    recursive = args.recursive

    if not directory.is_dir():
        logger.error(f"Provided path is not a directory: {directory}")
        return []

    pattern = "**/*.pdf" if recursive else "*.pdf"
    pdf_files = list(directory.glob(pattern))

    if not pdf_files:
        logger.warning(f"No PDF files found in {directory}")
        return []

    if args.max_upload > 0:
        logger.info(f"Maximum upload limit set to {args.max_upload} PDFs.")

    logger.info(f"Found {len(pdf_files)} PDF files in {directory}.")
    return pdf_files


def exclude_oversized_pdfs(pdf_files: list[Path]) -> list[Path]:
    """Exclude PDF files exceeding the maximum allowed size."""
    filtered_files = []
    excluded_files = 0

    for pdf_file in pdf_files:
        if pdf_file.stat().st_size > MAX_FILE_SIZE:
            logger.warning(
                f"Excluding oversized file (>{MAX_FILE_SIZE} bytes): {pdf_file}"
            )
            excluded_files += 1
        else:
            filtered_files.append(pdf_file)

    if excluded_files:
        logger.info(f"Excluded {excluded_files} oversized file(s) from upload list.")

    return filtered_files


def get_existing_documents(client: R2RClient) -> dict[str, str]:
    """Fetch the titles and ingestion statuses of all existing documents."""
    documents = {}
    limit = 250
    offset = 0

    try:
        while True:
            response = client.documents.list(limit=limit, offset=offset)
            docs = response.results
            if not docs:
                break
            for doc in docs:
                documents[doc.title] = getattr(doc, "ingestion_status", "unknown")
            if len(docs) < limit:
                break
            offset += limit
    except Exception as e:
        logger.error(f"Error fetching document list: {e}")

    return documents


def upload_pdfs(
    pdf_files: list[Path],
    client: R2RClient,
    existing_documents: dict[str, str],
    collection: str = None,
    max_upload: int = 0,
) -> tuple[int, int, list[tuple[Path, str]]]:
    """Upload new PDFs and skip existing ones. Stop after max_upload successful uploads if set."""
    success_count = 0
    skipped_count = 0
    failed_files = []

    for pdf_file in pdf_files:
        if success_count >= max_upload:
            logger.info(f"Reached maximum upload limit: {max_upload} files.")
            break

        try:
            logger.debug(f"Processing file: {pdf_file}")
            ingestion_status = existing_documents.get(pdf_file.name)

            if ingestion_status not in (None, "failed"):
                logger.debug(
                    f"Skipping file with ingestion_status='{ingestion_status}': {pdf_file}"
                )
                skipped_count += 1
                continue

            if ingestion_status == "failed":
                logger.warning(
                    f"Re-uploading file with previous ingestion_status='failed': {pdf_file}"
                )
            else:
                logger.debug(f"Uploading new file: {pdf_file}")

            kwargs = {"collection_name": collection} if collection else {}
            client.documents.create(file_path=str(pdf_file), **kwargs)
            logger.info(f"Successfully uploaded file: {pdf_file}")
            success_count += 1

        except Exception as e:
            logger.error(f"Failed to process file {pdf_file}: {str(e)}")
            failed_files.append((pdf_file, str(e)))

    return success_count, skipped_count, failed_files


def main():
    """
    Upload PDFs to an R2R instance.

    This function:
    - Parses command-line arguments.
    - Prepares and filters the list of PDF files.
    - Connects to the R2R server.
    - Fetches existing documents and logs their ingestion status breakdown.
    - Uploads new PDFs while skipping already ingested ones.
    - Summarizes the upload process with counts of successful, skipped, and failed uploads.
    """
    args = get_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="[%(levelname)s] %(message)s",
    )
    pdf_files = prepare_pdf_files(args)
    if not pdf_files:
        return 1

    pdf_files = exclude_oversized_pdfs(pdf_files)
    if not pdf_files:
        logger.error("No valid PDF files to upload after filtering oversized files.")
        return 1

    client = R2RClient(base_url=args.base_url)

    existing_documents = get_existing_documents(client)
    status_counter = Counter(existing_documents.values())

    logger.info(f"Found {len(existing_documents)} documents already in R2R.")
    for status, count in status_counter.items():
        logger.info(f"- {count} document(s) with ingestion_status='{status}'")

    success_count, skipped_count, failed_files = upload_pdfs(
        pdf_files,
        client,
        existing_documents,
        collection=args.collection,
        max_upload=args.max_upload,
    )

    logger.info(
        f"Upload summary: {success_count} successful, {skipped_count} skipped, {len(failed_files)} failed."
    )
    if failed_files:
        logger.error("Failed files:")
        for file, error in failed_files:
            logger.error(f"- {file}: {error}")
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
