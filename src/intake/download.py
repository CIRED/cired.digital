"""
Download files listed in a JSON file and store them in the local data directory.

This script reads a JSON file containing publications metadata, checks if
the associated files are already downloaded, and downloads them if they are missing.
The script detects file types from HTTP headers and applies correct extensions.

Usage:
    python download.py [--catalog PATH] [--log-level LEVEL] [--max-download N] [--verify-types]

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

import magic
import requests

from intake.config import (
    CATALOG_FILE,
    DOCUMENTS_DIR,
    DOWNLOAD_CHUNK_SIZE,
    DOWNLOAD_DELAY,
    DOWNLOAD_TIMEOUT,
    MAX_FILE_SIZE,
    setup_logging,
)
from intake.utils import get_catalog_file, get_catalog_publications

setup_logging()

# Create directories if they don't exist
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)


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
    Verify file types of existing downloads.

    Prompt user to automatically correct incorrect extensions upon confirmation.
    """
    if not DOCUMENTS_DIR.exists():
        logging.info("Documents directory does not exist: %s", DOCUMENTS_DIR)
        return

    mismatches = []
    total_files = 0

    for file_path in DOCUMENTS_DIR.iterdir():
        if file_path.is_file() and not file_path.name.endswith(".tmp"):
            total_files += 1

            # Détection du type de fichier via libmagic au lieu de mimetypes
            detected_mime = magic.from_file(str(file_path), mime=True)
            correct_extension = (
                mimetypes.guess_extension(detected_mime) or file_path.suffix
            )
            current_extension = file_path.suffix

            if correct_extension and correct_extension != current_extension:
                mismatches.append(
                    {
                        "file": file_path.name,
                        "current_ext": current_extension,
                        "correct_ext": correct_extension,
                        "content_type": detected_mime,
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
    if mismatches:
        response = input(
            "\nDetected incorrect extensions. Do you want to automatically correct them? [y/N]: "
        )
        if response.lower() in ("y", "yes"):
            for mismatch in mismatches:
                old_path = DOCUMENTS_DIR / mismatch["file"]
                new_path = old_path.with_suffix(mismatch["correct_ext"])
                old_path.rename(new_path)
                logging.info("Renamed %s to %s", mismatch["file"], new_path.name)
        else:
            logging.info("User cancelled corrections.")
    else:
        logging.info("All extensions are correct.")


def verify_file_sizes() -> None:
    """Verify that existing files do not exceed MAX_FILE_SIZE."""
    oversized = []
    total_files = 0
    for file_path in DOCUMENTS_DIR.iterdir():
        if file_path.is_file():
            total_files += 1
            size = file_path.stat().st_size
            if size > MAX_FILE_SIZE:
                oversized.append({"file": file_path.name, "size": size})
    logging.info("File size verification complete:")
    logging.info("  Total files checked: %d", total_files)
    logging.info("  Oversized files found: %d", len(oversized))
    for entry in oversized:
        logging.warning(
            "Oversized: %s (%d bytes > %d bytes)",
            entry["file"],
            entry["size"],
            MAX_FILE_SIZE,
        )
    if not oversized:
        logging.info("All files within size limit.")


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
        # Détection du type de fichier via libmagic
        detected_mime = magic.from_file(temp_path, mime=True)
        extension = mimetypes.guess_extension(detected_mime) or target_path.suffix
        target_path = target_path.with_suffix(extension)
        temp_path = target_path.with_suffix(".tmp")
        logging.debug(
            "Detected MIME via magic: %s, using extension: %s",
            detected_mime,
            extension,
        )
        temp_path.rename(target_path)
        logging.info("Downloaded: %s", target_path.name)
        return True
    except Exception as e:
        # Suggère un embargo si code HTTP 403 Forbidden
        if isinstance(e, requests.exceptions.HTTPError) and getattr(e.response, "status_code", None) == 403:
            logging.warning(
                "Failed to download %s: %s (HTTP 403 Forbidden – le fichier peut être sous embargo)",
                url,
                e,
            )
        else:
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
        "--verify-types",
        action="store_true",
        help="Verify and report file type mismatches for existing downloads",
    )
    parser.add_argument(
        "--verify-sizes",
        action="store_true",
        help="Verify file size limits for existing downloads",
    )
    return parser


def process_downloads(
    catalog: list[dict[str, Any]], max_download: int
) -> tuple[int, int, int, int]:
    """Process downloads from catalog entries."""
    # Cache des stems de fichiers existants (évite iterdir à chaque tour)
    existing_stems = {p.stem for p in DOCUMENTS_DIR.iterdir() if p.is_file()}
    total = 0
    skipped = 0
    downloaded = 0
    failed = 0

    for entry in catalog:
        url = entry.get("fileMain_s")
        if not url:
            continue

        if "halId_s" in entry:
            target_file = DOCUMENTS_DIR / f"{sanitize_filename(entry['halId_s'])}.pdf"
        else:
            hashname = hashlib.md5(url.encode()).hexdigest()
            target_file = DOCUMENTS_DIR / f"{hashname}.pdf"

        basename = target_file.stem
        if basename in existing_stems:
            logging.info("Already exists (any ext), skipping: %s.*", basename)
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

    if args.verify_sizes:
        verify_file_sizes()
        return
    if args.verify_types:
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
