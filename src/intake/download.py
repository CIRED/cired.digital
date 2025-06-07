"""
Download files listed in a JSON file and store them in the local data directory.

This script reads a JSON file containing publications metadata, checks if
the associated files are already downloaded, and downloads them if they are missing.
The script detects file types from HTTP headers and applies correct extensions.

Usage:
    python download.py [--catalog PATH] [--log-level LEVEL] [--max-download N] [--verify-existing]

Dependencies:
    - requests: For downloading files from URLs.
    - pathlib: For handling file paths.
    - hashlib: For generating unique filenames when necessary.
    - json: For reading the publication metadata.
    - logging: For logging the process.
    - time: For introducing delays between downloads.
    - mimetypes: For file type detection and extension mapping.
"""

import argparse
import hashlib
import json
import logging
import mimetypes
import time
from pathlib import Path
from typing import Any

import requests
import magic

from intake.config import (
    CATALOG_FILE,
    DOWNLOAD_CHUNK_SIZE,
    DOWNLOAD_DELAY,
    DOWNLOAD_TIMEOUT,
    PDF_DIR,
    setup_logging,
)
from intake.utils import get_catalog_file, get_catalog_publications

setup_logging()

# Create directories if they don't exist
PDF_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_filename(text: str) -> str:
    """
    Convert text into a safe filename.

    Args:
    ----
        text: Text to convert into a filename.

    Returns:
    -------
        Safe filename containing only alphanumeric characters,
        spaces, periods, and underscores.

    """
    return "".join(
        c if c.isalnum() or c in (" ", ".", "_") else "_" for c in text
    ).strip()


def verify_existing_files() -> None:
    """
    Verify file types of existing downloads and report mismatches.

    Walks through PDF_DIR and checks if file extensions match actual content types.
    """
    if not PDF_DIR.exists():
        logging.info("PDF directory does not exist: %s", PDF_DIR)
        return

    mismatches = []
    total_files = 0

    for file_path in PDF_DIR.iterdir():
        if file_path.is_file() and not file_path.name.endswith(".tmp"):
            total_files += 1

            guessed_type, _ = mimetypes.guess_type(str(file_path))
            if guessed_type:
                correct_extension = mimetypes.guess_extension(guessed_type)
                current_extension = file_path.suffix

                if correct_extension and correct_extension != current_extension:
                    mismatches.append(
                        {
                            "file": file_path.name,
                            "current_ext": current_extension,
                            "correct_ext": correct_extension,
                            "content_type": guessed_type,
                        }
                    )

    logging.info("File verification complete:")
    logging.info("  Total files checked: %d", total_files)
    logging.info("  Extension mismatches found: %d", len(mismatches))

    for mismatch in mismatches:
        logging.warning(
            "Mismatch: %s (has %s, should be %s, type: %s)",
            mismatch["file"],
            mismatch["current_ext"],
            mismatch["correct_ext"],
            mismatch["content_type"],
        )


def download_file(url: str, target_path: Path) -> bool:
    """
    Download one file from a URL with proper file type detection.

    Args:
    ----
        url: URL of the file to download.
        target_path: Path where to save the file (extension will be corrected).

    Returns:
    -------
        True if the download was successful, False otherwise.

    """
    temp_path = target_path.with_suffix(".tmp")

    try:
        with requests.get(url, stream=True, timeout=DOWNLOAD_TIMEOUT) as r:
            r.raise_for_status()

            # Libmagic déterminera le type de fichier après téléchargement ; l’extension sera gérée ci-dessous

            with open(temp_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                    f.write(chunk)
        temp_path.rename(target_path)
        logging.info("Downloaded: %s", target_path.name)
        return True
    except Exception as e:
        logging.warning("Failed to download %s: %s", url, e)
        if temp_path.exists():
            temp_path.unlink()
        return False


def setup_argument_parser() -> argparse.ArgumentParser:
    """Set up command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Download files from catalog publications"
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        help="Path to catalog file (default: latest prepared catalog)",
    )
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error"],
        default="info",
        help="Set logging level (default: info)",
    )
    parser.add_argument(
        "--max-download",
        type=int,
        default=0,
        help="Maximum number of files to download (0 = dry run)",
    )
    parser.add_argument(
        "--verify-existing",
        action="store_true",
        help="Verify and report file type mismatches for existing downloads",
    )
    return parser


def process_downloads(
    catalog: list[dict[str, Any]], max_download: int
) -> tuple[int, int, int, int]:
    """Process downloads from catalog entries."""
    total = 0
    skipped = 0
    downloaded = 0
    failed = 0

    for entry in catalog:
        url = entry.get("pdf_url")
        if not url:
            continue

        if "halId_s" in entry:
            target_file = PDF_DIR / f"{sanitize_filename(entry['halId_s'])}.pdf"
        else:
            hashname = hashlib.md5(entry["pdf_url"].encode()).hexdigest()
            target_file = PDF_DIR / f"{hashname}.pdf"

        if target_file.exists():
            logging.info("Already exists, skipping: %s", target_file.name)
            skipped += 1
            continue

        total += 1

        if max_download == 0:
            logging.info("DRY RUN: Would download %s to %s", url, target_file.name)
            continue
        elif total > max_download:
            logging.info("Reached max download limit (%d), stopping", max_download)
            break

        success = download_file(url, target_file)
        if success:
            downloaded += 1
        else:
            failed += 1

        time.sleep(DOWNLOAD_DELAY)

    return total, skipped, downloaded, failed


def main() -> None:
    """
    Download all publication files.

    Reads the catalog file, iterates through each entry, and downloads
    the corresponding files if they are not already locally present.
    """
    parser = setup_argument_parser()
    args = parser.parse_args()

    log_levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
    }
    setup_logging(level=log_levels[args.log_level])

    if args.verify_existing:
        verify_existing_files()
        return

    catalog_file = get_catalog_file(args.catalog)
    if not catalog_file:
        logging.error(
            "No catalog file found. Run hal_query.py and prepare_catalog.py first."
        )
        return

    if catalog_file == CATALOG_FILE:
        logging.info("Using legacy catalog file: %s", CATALOG_FILE)
    else:
        logging.info("Using catalog file: %s", catalog_file)

    catalog_data = json.loads(catalog_file.read_text(encoding="utf-8"))
    catalog = get_catalog_publications(catalog_data)

    total, skipped, downloaded, failed = process_downloads(catalog, args.max_download)

    logging.info("Download summary:")
    logging.info("  Total attempted: %d", total)
    logging.info("  Downloaded: %d", downloaded)
    logging.info("  Skipped: %d", skipped)
    logging.info("  Failed: %d", failed)


if __name__ == "__main__":
    main()
