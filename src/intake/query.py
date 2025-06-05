"""
Obtain the list of CIRED records from HAL.

Query archive-ouvertes.fr using the HAL API
Use pagination to handle large result sets
Process the list to separate irrelevant ones related to the homonymous CIRED conference
Save into two JSON files
Include URL of PDF files when available

Pagination is not strictly required since we expect <10000 results,
but the docs says to kindly avoid asking for more than 500/1000 at a time.

API specifications: https://api.archives-ouvertes.fr/docs/search

minh.ha-duong@cnrs.fr, 2024-2025 CC-BY-SA
"""

import html
import json
import logging
import time
from typing import Any

import requests

from intake.config import (
    CATALOG_FILE,
    CONFERENCE_FILE,
    HAL_API_REQUEST_DELAY,
    HAL_API_TIMEOUT,
    HAL_API_URL,
    HAL_BATCH_SIZE,
    HAL_MAX_BATCHES,
    HAL_QUERY,
    setup_logging,
)

setup_logging(level=logging.DEBUG, enable_requests_debug=True)


def process_publications(publications: list[dict[str, Any]]) -> None:
    """Process the publication records and save them into separate JSON files."""
    related_publications = []
    unrelated_cired_communications = []

    for pub in publications:
        pub["label_s"] = html.unescape(pub["label_s"])
        if "producedDate_tdate" in pub:
            pub["producedDate_tdate"] = pub["producedDate_tdate"].split("T")[0]

        # Add PDF URL if available
        if "fileMain_s" in pub:
            pub["pdf_url"] = pub["fileMain_s"]

        lab_acronym_present = (
            "labStructAcronym_s" in pub and "CIRED" in pub["labStructAcronym_s"]
        )
        cired_in_citation = "CIRED" in pub.get("label_s", "")

        if not lab_acronym_present and cired_in_citation:
            unrelated_cired_communications.append(pub)
        else:
            related_publications.append(pub)

    # Ensure output directories exist
    CATALOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFERENCE_FILE.parent.mkdir(parents=True, exist_ok=True)

    CATALOG_FILE.write_text(
        json.dumps(related_publications, ensure_ascii=False, indent=4), encoding="utf-8"
    )

    CONFERENCE_FILE.write_text(
        json.dumps(unrelated_cired_communications, ensure_ascii=False, indent=4),
        encoding="utf-8",
    )

    logging.info(
        "Found %d CIRED lab publications saved to %s",
        len(related_publications),
        CATALOG_FILE,
    )
    logging.info(
        "Found %d unrelated CIRED conference communications saved to %s",
        len(unrelated_cired_communications),
        CONFERENCE_FILE,
    )


def get_paginated_publications(
    base_params: dict[str, str | int],
) -> list[dict[str, Any]]:
    """Retrieve publication records with pagination from the HAL API."""
    all_publications = []
    current_batch = 0

    # Set up pagination parameters
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
            # Check if we've reached the end of available records
            if len(batch_publications) < HAL_BATCH_SIZE:
                logging.info("Reached end of available records.")
                break

            # Add a small delay to avoid overloading the API
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
    return all_publications


def main() -> None:
    """Orchestrate the retrieval and processing of publications."""
    fields = """
docid,halId_s,doiId_s,label_s,producedDate_tdate,authFullName_s,title_s,abstract_s,submitType_s,docType_s,labStructAcronym_s,fileMain_s
"""
    params: dict[str, str | int] = {
        "q": HAL_QUERY,
        # No time restriction
        "fl": fields.strip(),
        "wt": "json",
    }

    publications = get_paginated_publications(params)
    if publications:
        process_publications(publications)
    else:
        logging.warning("No publications found or API request failed")


if __name__ == "__main__":
    main()
