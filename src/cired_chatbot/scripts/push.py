"""Upload PDFs into an R2R instance."""

import argparse
import logging
from pathlib import Path

from r2r import R2RClient
from tqdm import tqdm

logger = logging.getLogger(__name__)

DEFAULT_MAX_UPLOAD = 5
MAX_FILE_SIZE = 30000000

def get_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Push PDF files into R2R using the official SDK."
    )
    parser.add_argument(
        "--dir", type=Path, required=True, help="Directory containing PDF files."
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
        help=f"Maximum number of PDFs to upload (0 = no limit). Default is {DEFAULT_MAX_UPLOAD}."
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
            logger.warning(f"Excluding oversized file (>{MAX_FILE_SIZE} bytes): {pdf_file}")
            excluded_files += 1
        else:
            filtered_files.append(pdf_file)

    if excluded_files:
        logger.info(f"Excluded {excluded_files} oversized file(s) from upload list.")

    return filtered_files

def get_existing_titles(client: R2RClient) -> set:
    """Fetch the titles of all existing documents, handling pagination."""
    titles = set()
    limit = 250
    offset = 0

    try:
        while True:
            response = client.documents.list(limit=limit, offset=offset)
            docs = response.results
            if not docs:
                break
            titles.update(doc.title for doc in docs)
            offset += limit
    except Exception as e:
        logger.error(f"Error fetching document list: {e}")

    return titles


def upload_pdfs(
    pdf_files: list[Path],
    client: R2RClient,
    existing_titles: set,
    collection: str = None,
    max_upload: int = 0,
) -> tuple[int, int, list[tuple[Path, str]]]:
    """Upload new PDFs and skip existing ones. Stop after max_upload successful uploads if set."""
    success_count = 0
    skipped_count = 0
    failed_files = []

    with tqdm(total=len(pdf_files), desc="Uploading PDFs") as pbar:
        for pdf_file in pdf_files:
            if max_upload > 0 and success_count >= max_upload:
                logger.info(f"Reached maximum upload limit: {max_upload} files.")
                break

            try:
                logger.debug(f"Processing file: {pdf_file}")
                if pdf_file.name in existing_titles:
                    logger.debug(f"Skipping already uploaded file: {pdf_file} (found in existing titles)")
                    skipped_count += 1
                else:
                    logger.debug(f"Attempting to upload new file: {pdf_file}")
                    kwargs = {"collection_name": collection} if collection else {}
                    client.documents.create(file_path=str(pdf_file), **kwargs)
                    logger.info(f"Successfully uploaded file: {pdf_file}")
                    success_count += 1
            except Exception as e:
                logger.error(f"Failed to process file {pdf_file}: {str(e)}")
                failed_files.append((pdf_file, str(e)))
            finally:
                pbar.update(1)

    return success_count, skipped_count, failed_files


def main():
    args = get_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="[%(levelname)s] %(message)s",
    )
    pdf_files = prepare_pdf_files(args)
    if not pdf_files:
        return

    pdf_files = exclude_oversized_pdfs(pdf_files)
    if not pdf_files:
        logger.error("No valid PDF files to upload after filtering oversized files.")
        return

    client = R2RClient(base_url=args.base_url)
    existing_titles = get_existing_titles(client)
    logger.info(f"Found {len(existing_titles)} documents already in R2R.")

    success_count, skipped_count, failed_files = upload_pdfs(
        pdf_files,
        client,
        existing_titles,
        collection=args.collection,
        max_upload=args.max_upload,
    )

    logger.info(
        f"\nUpload summary: {success_count} successful, {skipped_count} skipped, {len(failed_files)} failed."
    )
    if failed_files:
        logger.error("\nFailed files:")
        for file, error in failed_files:
            logger.error(f"- {file}: {error}")


if __name__ == "__main__":
    main()
