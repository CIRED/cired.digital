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

PDF_DIR.mkdir(parents=True, exist_ok=True)

def sanitize_filename(text):
    return "".join(c if c.isalnum() or c in (' ', '.', '_') else '_' for c in text).strip()

def get_pdf_filename(entry):
    if "halId_s" in entry:
        return PDF_DIR / f"{sanitize_filename(entry['halId_s'])}.pdf"
    else:
        hashname = hashlib.md5(entry["pdf_url"].encode()).hexdigest()
        return PDF_DIR / f"{hashname}.pdf"

def download_pdf(url, target_path):
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

def main():
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

