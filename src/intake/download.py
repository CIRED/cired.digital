"""
Download PDFs listed in a JSON file and store them in the local data directory.

This script reads a JSON file containing publications metadata, checks if
the associated PDFs are already downloaded, and downloads them if they are missing. The script also
logs the download process and handles retries for failed downloads.

Usage:
    python download.py

Dependencies:
    - requests: For downloading PDFs from URLs.
    - pathlib: For handling file paths.
    - hashlib: For generating unique filenames when necessary.
    - json: For reading the publication metadata.
    - logging: For logging the process.
    - time: For introducing delays between downloads.
"""

import hashlib
import json
import logging
import time
from pathlib import Path

import requests

from intake.catalog_utils import get_catalog_publications, get_latest_prepared_catalog
from intake.config import (
    CATALOG_FILE,
    DOWNLOAD_CHUNK_SIZE,
    DOWNLOAD_DELAY,
    DOWNLOAD_TIMEOUT,
    PDF_DIR,
    setup_logging,
)

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


def download_pdf(url: str, target_path: Path) -> bool:
    """
    Download one PDF from a URL.

    Args:
    ----
        url: URL of the PDF to download.
        target_path: Path where to save the PDF.

    Returns:
    -------
        True if the download was successful, False otherwise.

    """
    temp_path = target_path.with_suffix(".tmp")

    try:
        with requests.get(url, stream=True, timeout=DOWNLOAD_TIMEOUT) as r:
            r.raise_for_status()
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


def main() -> None:
    """
    Download all publication PDFs.

    Reads the latest prepared catalog, iterates through each entry, and downloads
    the corresponding PDFs if they are not already locally present.
    """
    catalog_file = get_latest_prepared_catalog()
    if not catalog_file:
        if CATALOG_FILE.exists():
            catalog_file = CATALOG_FILE
            logging.info("Using legacy catalog file: %s", CATALOG_FILE)
        else:
            logging.error(
                "No catalog file found. Run hal_query.py and prepare_catalog.py first."
            )
            return
    else:
        logging.info("Using latest prepared catalog: %s", catalog_file)

    catalog_data = json.loads(catalog_file.read_text(encoding="utf-8"))
    CATALOG = get_catalog_publications(catalog_data)

    total = 0
    skipped = 0
    downloaded = 0
    failed = 0

    for entry in CATALOG:
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
        success = download_pdf(url, target_file)
        if success:
            downloaded += 1
        else:
            failed += 1

        time.sleep(DOWNLOAD_DELAY)

    logging.info("Download summary:")
    logging.info("  Total attempted: %d", total)
    logging.info("  Downloaded: %d", downloaded)
    logging.info("  Skipped: %d", skipped)
    logging.info("  Failed: %d", failed)


if __name__ == "__main__":
    main()
