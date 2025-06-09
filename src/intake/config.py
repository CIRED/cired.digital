"""
Centralize configuration for the HAL data processing pipeline.

This module defines all of the project’s constants—paths, URLs, timeouts, batch sizes,
upload limits and logging formats—in one place, so that every script (download.py,
query.py, push.py, etc.) can import them without hard-coding values.

Constants provided:
  • BASE_DIR            – Project root directory (Path)
  • DATA_ROOT           – Root of your HAL data (Path)
  • DOCUMENTS_DIR       – Directory for downloaded documents (Path)
  • PUBLICATIONS_FILE   – Path to catalog.json (Path)
  • CONFERENCE_FILE     – Path to conference.json (Path)
  • HAL_API_URL         – Base URL for the HAL API (str)
  • DOWNLOAD_DELAY_SEC  – Delay between downloads in seconds (int)
  • DOWNLOAD_TIMEOUT    – HTTP timeout for downloads in seconds (int)
  • DEFAULT_MAX_UPLOAD  – Default number of files to push at once (int)
  • MAX_FILE_SIZE       – Maximum allowed file size in bytes (int)
  • HAL_BATCH_SIZE      – Number of records per page when querying HAL (int)
  • HAL_MAX_BATCHES     – Maximum number of pages when querying HAL (int)
  • LOG_FORMAT_SIMPLE   – Simple log message format (str)
  • LOG_FORMAT_DETAILED – Detailed log message format (str)
  • LOG_LEVEL           – Default log level (int)
  • setup_logging()     – Helper to configure the root logger

Usage:
    import config

    config.setup_logging()
    pdfs = list(config.PDF_DIR.iterdir())
    response = requests.get(config.HAL_API_URL, timeout=config.DOWNLOAD_TIMEOUT)
"""

import logging
from pathlib import Path

# Base directories. Note: Assumes that the script is 3 levels down repo root.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if not (BASE_DIR / "data").is_dir():
    import sys

    print(
        f"Error: Expected data/ directory not found at {BASE_DIR / 'data'}",
        file=sys.stderr,
    )
    print(f"BASE_DIR is set to: {BASE_DIR}", file=sys.stderr)
    sys.exit(1)

DATA_ROOT = BASE_DIR / "data" / "source" / "hal"

# File paths
DOCUMENTS_DIR = DATA_ROOT / "documents"
CATALOG_FILE = DATA_ROOT / "catalog.json"
CONFERENCE_FILE = DATA_ROOT / "conference.json"
RAW_HAL_DIR = BASE_DIR / "data" / "source" / "hal"
PREPARED_DIR = BASE_DIR / "data" / "prepared"
BLACKLIST_FILE = BASE_DIR / "data" / "source" / "blacklist.json"

# HAL Query settings
"""
## Query for CIRED:
We query HAL with the acronym of the lab, because the lab has two different structId_i:
- 1042364 since 2020-01-01
- 135977 from 1998-01-01 to 2019-12-31

## Documents filter for open access:
- Fulltext is in HAL "submitType_s:file"
- Fulltext is in HAL OR on the web via unpaywall "(submitType_s:file OR linkExtId_s:openaccess)"

## Fields to retrieve:
TODO: retrieve linkExtId_s linkExtURL_s and download those too
TODO: retrieve releasedDate_s

## References:
https://wiki.ccsd.cnrs.fr/wikis/hal/index.php/Requêtes_sur_les_ressources_de_HAL
https://api.archives-ouvertes.fr/docs/search/?schema=fields#fields

"""
HAL_API_URL = "https://api.archives-ouvertes.fr/search/"
HAL_QUERY = "labStructAcronym_s:CIRED"
HAL_FILTER = "submitType_s:file"
HAL_FIELDS = """docid,halId_s,doiId_s,label_s,producedDate_tdate,authFullName_s,title_s,abstract_s,submitType_s,docType_s,peerReviewing_t,labStructAcronym_s,fileMain_s"""

HAL_BATCH_SIZE = 500
HAL_MAX_BATCHES = 10  # Fetch a maximum of 5000 publications

# Download settings
DOWNLOAD_DELAY = 1  # seconds
DOWNLOAD_TIMEOUT = 60  # seconds
DOWNLOAD_CHUNK_SIZE = 8192  # bytes
HAL_API_TIMEOUT = 60  # seconds
HAL_API_REQUEST_DELAY = 1  # seconds between API requests

# Upload settings
R2R_DEFAULT_BASE_URL = "http://localhost:7272"
MAX_FILE_SIZE = 30_000_000  # bytes


# Logging configuration
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
LOG_FORMAT_SIMPLE = "[%(levelname)s] %(message)s"  # For simpler output


def setup_logging(
    level: int | None = None,
    simple_format: bool = False,
    enable_requests_debug: bool = False,
) -> None:
    """
    Configure logging with consistent settings across all modules.

    Args:
    ----
        level: Logging level (default: LOG_LEVEL from config)
        simple_format: Use simple format without timestamp (default: False)
        enable_requests_debug: Enable debug logging for requests library (default: False)

    """
    log_level = level or LOG_LEVEL
    log_format = LOG_FORMAT_SIMPLE if simple_format else LOG_FORMAT
    logging.basicConfig(level=log_level, format=log_format)

    if enable_requests_debug:
        logging.getLogger("requests").setLevel(logging.DEBUG)
        logging.getLogger("urllib3").setLevel(logging.DEBUG)
