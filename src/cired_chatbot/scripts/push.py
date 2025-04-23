#!/usr/bin/env python3
"""Safe PDF upload script with verification and test mode."""

import argparse
import logging
from pathlib import Path
from typing import List, Tuple

from r2r import R2RClient
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def get_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Safely load PDF files into R2R using official SDK."
    )
    parser.add_argument(
        "--dir", type=Path, required=True, help="Directory containing PDF files."
    )
    parser.add_argument(
        "--base-url", type=str, default="http://localhost:7272", help="R2R API URL."
    )
    parser.add_argument(
        "--collection", type=str, help="Collection name for uploaded documents."
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively search PDFs in subdirectories.",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode: Only upload the first PDF file found.",
    )
    return parser.parse_args()


def find_pdf_files(directory: Path, recursive: bool) -> List[Path]:
    """Find all PDF files in the specified directory."""
    if not directory.is_dir():
        raise NotADirectoryError(f"Provided path is not a directory: {directory}")

    pattern = "**/*.pdf" if recursive else "*.pdf"
    return list(directory.glob(pattern))


def get_existing_titles(client: R2RClient) -> set:
    """Fetch the titles of all existing documents."""
    try:
        docs = client.documents.list().results
        return {doc.title for doc in docs}
    except Exception as e:
        logger.error(f"Error fetching document list: {e}")
        return set()


def upload_pdfs(
    pdf_files: List[Path],
    client: R2RClient,
    existing_titles: set,
    collection: str = None,
) -> Tuple[int, int, List[Tuple[Path, str]]]:
    """Upload new PDFs and skip existing ones."""
    success_count = 0
    skipped_count = 0
    failed_files = []

    with tqdm(total=len(pdf_files), desc="Uploading PDFs") as pbar:
        for pdf_file in pdf_files:
            try:
                if pdf_file.name in existing_titles:
                    logger.info(f"Skipping already uploaded file: {pdf_file}")
                    skipped_count += 1
                else:
                    kwargs = {"collection_name": collection} if collection else {}
                    client.documents.create(file_path=str(pdf_file), **kwargs)
                    success_count += 1
            except Exception as e:
                failed_files.append((pdf_file, str(e)))
            finally:
                pbar.update(1)

    return success_count, skipped_count, failed_files


def main():
    """Parse arguments and upload PDF files to the R2R API, with optional test mode."""
    args = get_args()

    try:
        pdf_files = find_pdf_files(args.dir, args.recursive)
    except NotADirectoryError as e:
        logger.error(e)
        return

    if not pdf_files:
        logger.warning(f"No PDF files found in {args.dir}")
        return

    if args.test:
        pdf_files = pdf_files[:1]
        logger.info("Test mode activated: only one PDF will be uploaded.")

    logger.info(f"Found {len(pdf_files)} PDF files.")

    client = R2RClient(base_url=args.base_url)
    existing_titles = get_existing_titles(client)

    success_count, skipped_count, failed_files = upload_pdfs(
        pdf_files, client, existing_titles, args.collection
    )

    logger.info(
        f"\nUpload summary: {success_count} successful, {skipped_count} skipped, {len(failed_files)} failed"
    )
    if failed_files:
        logger.error("\nFailed files:")
        for file, error in failed_files:
            logger.error(f"- {file}: {error}")


if __name__ == "__main__":
    main()
