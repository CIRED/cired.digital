"""
Obtain the list of CIRED records from HAL.

Query archive-ouvertes.fr using the HAL API
Use pagination to handle large result sets
Process the list to separate irrelevant ones related to the homonymous CIRED conference
Save into two JSON files
Include URL of PDF files when available

minh.ha-duong@cnrs.fr, 2024-2025 CC-BY-SA
"""

import html
import json
import logging
import time
from pathlib import Path

import requests

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Enable logging for the requests library to see HTTP requests
logging.getLogger("requests").setLevel(logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.DEBUG)

DATA_DIR = Path(__file__).parent.parent / "data"
PUBLICATIONS_PATH = DATA_DIR / "publications.json"
CONFERENCE_PATH = DATA_DIR / "conference.json"
HAL_API_URL = "https://api.archives-ouvertes.fr/search/"

# Query for all CIRED publications without time restriction
# TODO: try other requests potentially avoiding the homonymous problem:
#   lab= ...(by name(s), by reference(s)
#   collection= ...
QUERY = "CIRED"

# Pagination settings
BATCH_SIZE = 100
MAX_BATCHES = 50


def process_publications(publications: list[dict]) -> None:
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
    PUBLICATIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFERENCE_PATH.parent.mkdir(parents=True, exist_ok=True)

    PUBLICATIONS_PATH.write_text(
        json.dumps(related_publications, ensure_ascii=False, indent=4), encoding="utf-8"
    )

    CONFERENCE_PATH.write_text(
        json.dumps(unrelated_cired_communications, ensure_ascii=False, indent=4),
        encoding="utf-8",
    )

    logging.info(
        "Found %d CIRED lab publications saved to %s",
        len(related_publications),
        PUBLICATIONS_PATH,
    )
    logging.info(
        "Found %d unrelated CIRED conference communications saved to %s",
        len(unrelated_cired_communications),
        CONFERENCE_PATH,
    )


def get_paginated_publications(base_params: dict) -> list[dict]:
    """Retrieve publication records with pagination from the HAL API."""
    all_publications = []
    current_batch = 0

    # Set up pagination parameters
    params = base_params.copy()
    params["rows"] = BATCH_SIZE

    while current_batch < MAX_BATCHES:
        params["start"] = current_batch * BATCH_SIZE

        try:
            logging.debug(
                "Fetching batch %d/%d (records %d-%d)",
                current_batch + 1,
                MAX_BATCHES,
                params["start"],
                params["start"] + BATCH_SIZE - 1,
            )
            logging.debug(
                "Request URL: %s?%s", HAL_API_URL, requests.compat.urlencode(params)
            )
            response = requests.get(HAL_API_URL, params=params, timeout=60)
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
            if len(batch_publications) < BATCH_SIZE:
                logging.info("Reached end of available records.")
                break

            # Add a small delay to avoid overloading the API
            time.sleep(1)

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
    params = {
        "q": QUERY,
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
