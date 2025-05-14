"""
Download PDFs listed in a JSON file and store them in the local data directory.

This script reads a JSON file containing metadata for publications, checks if
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

DATA_DIR = Path(__file__).parent / "../data"
PDF_DIR = DATA_DIR / "pdfs"
PUBLICATIONS_FILE = DATA_DIR / "publications.json"

# Download settings
DELAY_BETWEEN_DOWNLOADS = 1  # seconds
TIMEOUT = 60  # seconds

# Logging setup
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Create directories if they don't exist
PDF_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_filename(text: str) -> str:
    """
    Converts text into a safe filename.

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


def get_pdf_filename(entry: dict) -> Path:
    """
    Generates a filename for a publication.

    Uses the HAL ID if available, otherwise generates a hash from the PDF URL.

    Args:
    ----
        entry: Dictionary containing publication information.

    Returns:
    -------
        Path to the PDF file.

    """
    if "halId_s" in entry:
        return PDF_DIR / f"{sanitize_filename(entry['halId_s'])}.pdf"
    else:
        hashname = hashlib.md5(entry["pdf_url"].encode()).hexdigest()
        return PDF_DIR / f"{hashname}.pdf"


def download_pdf(url: str, target_path: Path) -> bool:
    """
    Downloads a PDF from a URL.

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
        with requests.get(url, stream=True, timeout=TIMEOUT) as r:
            r.raise_for_status()
            with open(temp_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
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
    Main function for downloading publication PDFs.

    Reads the publications file, iterates through each entry, and downloads
    the corresponding PDFs if they are not already locally present.
    """
    if not PUBLICATIONS_FILE.exists():
        logging.error("Missing input file: %s", PUBLICATIONS_FILE)
        return

    publications = json.loads(PUBLICATIONS_FILE.read_text(encoding="utf-8"))

    total = 0
    skipped = 0
    downloaded = 0
    failed = 0

    for entry in publications:
        url = entry.get("pdf_url")
        if not url:
            continue

        target_file = get_pdf_filename(entry)

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

        time.sleep(DELAY_BETWEEN_DOWNLOADS)

    logging.info("Download summary:")
    logging.info("  Total attempted: %d", total)
    logging.info("  Downloaded: %d", downloaded)
    logging.info("  Skipped: %d", skipped)
    logging.info("  Failed: %d", failed)


if __name__ == "__main__":
    main()
