"""
Query HAL API and save raw responses to timestamped JSON files.

This script queries the HAL API for CIRED publications and saves the complete
raw API responses to timestamped files for later processing. No filtering
or processing is applied - the raw HAL data is preserved exactly as received.

Usage:
    python hal_query.py

The raw responses are saved to data/source/hal/raw/ with timestamps.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

from intake.config import (
    HAL_API_REQUEST_DELAY,
    HAL_API_TIMEOUT,
    HAL_API_URL,
    HAL_BATCH_SIZE,
    HAL_MAX_BATCHES,
    HAL_QUERY,
    RAW_HAL_DIR,
    setup_logging,
)

setup_logging(level=logging.DEBUG, enable_requests_debug=True)


def get_paginated_publications(
    base_params: dict[str, str | int],
) -> dict[str, Any]:
    """Retrieve publication records with pagination from the HAL API."""
    all_publications = []
    current_batch = 0

    params = base_params.copy()
    params["rows"] = HAL_BATCH_SIZE

    while current_batch < HAL_MAX_BATCHES:
        start_index = current_batch * HAL_BATCH_SIZE
        params["start"] = start_index

        try:
            logging.debug(
                "Fetching batch %d / max %d (records %d-%d)",
                current_batch + 1,
                HAL_MAX_BATCHES,
                start_index,
                start_index + HAL_BATCH_SIZE - 1,
            )
            logging.debug(
                "Request URL: %s?%s", HAL_API_URL, requests.compat.urlencode(params)
            )
            response = requests.get(HAL_API_URL, params=params, timeout=HAL_API_TIMEOUT)
            response.raise_for_status()

            response_data = response.json()
            batch_publications = response_data["response"]["docs"]

            if not batch_publications:
                logging.info("No more records found. Stopping pagination.")
                break

            all_publications.extend(batch_publications)
            logging.info(
                "Retrieved %d records in this batch. Total so far: %d",
                len(batch_publications),
                len(all_publications),
            )

            if len(batch_publications) < HAL_BATCH_SIZE:
                logging.info("Reached end of available records.")
                break

            time.sleep(HAL_API_REQUEST_DELAY)

        except requests.exceptions.Timeout:
            logging.error("HAL request timed out. Please try again later.")
            break
        except requests.exceptions.HTTPError as err:
            logging.error("HTTP error in HAL request: %s", str(err))
            break
        except requests.exceptions.RequestException as e:
            logging.error("An exception occured while scraping HAL: %s", str(e))
            break

        current_batch += 1

    logging.info(
        "Pagination complete. Retrieved a total of %d records.", len(all_publications)
    )

    return {
        "query_timestamp": datetime.now().isoformat(),
        "query_params": base_params,
        "total_records": len(all_publications),
        "response": {"docs": all_publications},
    }


def save_raw_response(response_data: dict[str, Any]) -> Path:
    """Save raw HAL API response to timestamped file."""
    RAW_HAL_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"hal_response_{timestamp}.json"
    filepath = RAW_HAL_DIR / filename

    filepath.write_text(
        json.dumps(response_data, ensure_ascii=False, indent=4), encoding="utf-8"
    )

    logging.info("Saved raw HAL response to %s", filepath)
    return filepath


def main() -> None:
    """Query HAL API and save raw response."""
    fields = """
docid,halId_s,doiId_s,label_s,producedDate_tdate,authFullName_s,title_s,abstract_s,submitType_s,docType_s,labStructAcronym_s,fileMain_s
"""
    params: dict[str, str | int] = {
        "q": HAL_QUERY,
        "fl": fields.strip(),
        "wt": "json",
    }

    response_data = get_paginated_publications(params)
    if response_data["total_records"] > 0:
        save_raw_response(response_data)
    else:
        logging.warning("No publications found or API request failed")


if __name__ == "__main__":
    main()
