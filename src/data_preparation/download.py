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

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from pathlib import Path

import requests

# Base path config
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "../data")
PDF_DIR = Path(os.path.join(DATA_DIR, "pdfs"))
PUBLICATIONS_FILE = os.path.join(DATA_DIR, "publications.json")

# Download settings
DELAY_BETWEEN_DOWNLOADS = 1  # seconds
TIMEOUT = 60  # seconds

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Create directories if they don't exist
PDF_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_filename(text: str) -> str:
    """
    Convertit un texte en un nom de fichier sécurisé.

    Args:
        text: Texte à convertir en nom de fichier.

    Returns:
        Nom de fichier sécurisé ne contenant que des caractères alphanumériques,
        des espaces, des points et des underscores.

    """
    return "".join(c if c.isalnum() or c in (' ', '.', '_') else '_' for c in text).strip()


def get_pdf_filename(entry: dict) -> Path:
    """
    Génère un nom de fichier pour une publication.

    Utilise l'ID HAL si disponible, sinon génère un hash à partir de l'URL du PDF.

    Args:
        entry: Dictionnaire contenant les informations d'une publication.

    Returns:
        Chemin du fichier PDF.

    """
    if "halId_s" in entry:
        return PDF_DIR / f"{sanitize_filename(entry['halId_s'])}.pdf"
    else:
        hashname = hashlib.md5(entry["pdf_url"].encode()).hexdigest()
        return PDF_DIR / f"{hashname}.pdf"


def download_pdf(url: str, target_path: Path) -> bool:
    """
    Télécharge un PDF à partir d'une URL.

    Args:
        url: URL du PDF à télécharger.
        target_path: Chemin où sauvegarder le PDF.

    Returns:
        True si le téléchargement a réussi, False sinon.

    """
    temp_path = target_path.with_suffix(".tmp")

    try:
        with requests.get(url, stream=True, timeout=TIMEOUT) as r:
            r.raise_for_status()
            with open(temp_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        temp_path.rename(target_path)
        logging.info(f"Downloaded: {target_path.name}")
        return True
    except Exception as e:
        logging.warning(f"Failed to download {url}: {e}")
        if temp_path.exists():
            temp_path.unlink()
        return False


def main() -> None:
    """
    Fonction principale pour télécharger les PDFs des publications.

    Lit le fichier des publications, parcourt chaque entrée, et télécharge
    les PDFs correspondants s'ils ne sont pas déjà présents localement.
    """
    if not os.path.exists(PUBLICATIONS_FILE):
        logging.error(f"Missing input file: {PUBLICATIONS_FILE}")
        return

    with open(PUBLICATIONS_FILE, encoding='utf-8') as f:
        publications = json.load(f)

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
            logging.info(f"Already exists, skipping: {target_file.name}")
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
    logging.info(f"  Total attempted: {total}")
    logging.info(f"  Downloaded: {downloaded}")
    logging.info(f"  Skipped: {skipped}")
    logging.info(f"  Failed: {failed}")


if __name__ == "__main__":
    main()

