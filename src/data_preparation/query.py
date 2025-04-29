"""
scrape.py.

Query the HAL API to obtain the list of CIRED records
Process the list to separate irrelevant ones related to the homonymous CIRED conference
Save into two JSON files
Includes URL of PDF files when available
Uses pagination to handle large result sets

minh.ha-duong@cnrs.fr, 2024 CC-BY-SA
Modified version
"""

import html
import json
import logging
import os
import time

import requests

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Enable logging for the requests library to see HTTP requests
logging.getLogger("requests").setLevel(logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.DEBUG)


BASE_DIR = os.path.dirname(__file__)
OUT_FILENAME = os.path.join(BASE_DIR, "../data/publications.json")
OTHER_FILENAME = os.path.join(BASE_DIR, "../data/conference.json")
HAL_API_URL = "https://api.archives-ouvertes.fr/search/"

# Query for all CIRED publications without time restriction
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

    with open(OUT_FILENAME, "w", encoding="utf-8") as file:
        json.dump(related_publications, file, ensure_ascii=False, indent=4)

    with open(OTHER_FILENAME, "w", encoding="utf-8") as file:
        json.dump(unrelated_cired_communications, file, ensure_ascii=False, indent=4)

    logging.info(
        f"Found {len(related_publications)} CIRED lab publications saved to %s",
        OUT_FILENAME,
    )
    logging.info(
        f"Found {len(unrelated_cired_communications)} unrelated CIRED conference communications saved to %s",
        OTHER_FILENAME,
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
                f"Fetching batch {current_batch + 1}/{MAX_BATCHES} (records {params['start']}-{params['start'] + BATCH_SIZE - 1})"
            )
            logging.debug(
                f"Request URL: {HAL_API_URL}?{requests.compat.urlencode(params)}"
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
                f"Retrieved {len(batch_publications)} records in this batch. Total so far: {len(all_publications)}"
            )

            # Check if we've reached the end of available records
            if len(batch_publications) < BATCH_SIZE:
                logging.info("Reached end of available records.")
                break

            # Add a small delay to avoid overloading the API
            time.sleep(1)

        except requests.exceptions.Timeout:
            logging.error("La requête HAL a timed out. Essayez plus tard svp.")
            break
        except requests.exceptions.HTTPError as err:
            logging.error("HTTP error dans la requête à HAL %s: ", str(err))
            break
        except requests.exceptions.RequestException as e:
            logging.error("Une exception s'est produite en scrapant HAL: %s", str(e))
            break

        current_batch += 1

    logging.info(
        f"Pagination complete. Retrieved a total of {len(all_publications)} records."
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
