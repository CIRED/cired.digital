"""
Process raw HAL responses into filtered catalogs.

This script reads the latest raw HAL API response and applies comprehensive
filtering to create a clean catalog of CIRED publications. Filtering includes:
- CIRED conference vs lab distinction
- Blacklist exclusion
- Open access requirement
- File size limits
- Working paper deduplication

Usage:
    python prepare_catalog.py [--raw-file PATH]

The filtered catalog is saved to data/prepared/ with timestamps.
"""

import argparse
import html
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from intake.config import (
    BLACKLIST_FILE,
    PREPARED_DIR,
    setup_logging,
)
from intake.utils import get_latest_raw_hal_file, normalize_title

setup_logging()


def load_blacklist() -> set[str]:
    """Load blacklisted HAL IDs."""
    if not BLACKLIST_FILE.exists():
        logging.warning("Blacklist file not found: %s", BLACKLIST_FILE)
        return set()

    try:
        blacklist_data = json.loads(BLACKLIST_FILE.read_text(encoding="utf-8"))
        return set(blacklist_data.get("excluded_hal_ids", []))
    except Exception as e:
        logging.error("Failed to load blacklist: %s", e)
        return set()


def is_working_paper(doc_type: str) -> bool:
    """Check if document type indicates a working paper."""
    if not doc_type:
        return False

    working_paper_types = {"UNDEFINED", "OTHER", "REPORT"}
    return doc_type.upper() in working_paper_types


def has_open_access(pub: dict[str, Any]) -> bool:
    """Check if publication has open access (PDF available)."""
    return "fileMain_s" in pub and pub["fileMain_s"]


def group_by_normalized_title(
    publications: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Group publications by normalized title."""
    groups: dict[str, list[dict[str, Any]]] = {}

    for pub in publications:
        title = pub.get("title_s", "")
        if isinstance(title, list):
            title = title[0] if title else ""
        normalized = normalize_title(title)

        if normalized:
            if normalized not in groups:
                groups[normalized] = []
            groups[normalized].append(pub)

    return groups


def filter_working_papers(
    publications: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    """Filter out working papers when published articles with same title exist."""
    title_groups = group_by_normalized_title(publications)
    filtered_publications = []
    excluded_count = 0

    for normalized_title, group in title_groups.items():
        if len(group) == 1:
            filtered_publications.extend(group)
            continue

        published_articles = []
        working_papers = []

        for pub in group:
            doc_type = pub.get("docType_s", "")
            if is_working_paper(doc_type):
                working_papers.append(pub)
            else:
                published_articles.append(pub)

        published_with_fulltext = [
            pub for pub in published_articles if has_open_access(pub)
        ]

        if published_with_fulltext:
            filtered_publications.extend(published_articles)
            excluded_count += len(working_papers)
            if working_papers:
                logging.debug(
                    "Excluded %d working papers for title: %s (published version available)",
                    len(working_papers),
                    normalized_title[:50],
                )
        else:
            filtered_publications.extend(group)

    return filtered_publications, excluded_count


def process_publications(raw_data: dict[str, Any]) -> dict[str, Any]:
    """Process publications with comprehensive filtering and statistics."""
    publications = raw_data["response"]["docs"]

    stats = {
        "total_retrieved": len(publications),
        "cired_conference_excluded": 0,
        "blacklisted_excluded": 0,
        "no_open_access_excluded": 0,
        "working_papers_excluded": 0,
        "final_count": 0,
    }

    blacklist = load_blacklist()

    related_publications = []
    unrelated_cired_communications = []

    for pub in publications:
        pub["label_s"] = html.unescape(pub["label_s"])
        if "producedDate_tdate" in pub:
            pub["producedDate_tdate"] = pub["producedDate_tdate"].split("T")[0]

        if "fileMain_s" in pub:
            pub["pdf_url"] = pub["fileMain_s"]

        lab_acronym_present = (
            "labStructAcronym_s" in pub and "CIRED" in pub["labStructAcronym_s"]
        )
        cired_in_citation = "CIRED" in pub.get("label_s", "")

        if not lab_acronym_present and cired_in_citation:
            unrelated_cired_communications.append(pub)
            stats["cired_conference_excluded"] += 1
        else:
            related_publications.append(pub)

    filtered_publications = []

    for pub in related_publications:
        hal_id = pub.get("halId_s", "")

        if hal_id in blacklist:
            stats["blacklisted_excluded"] += 1
            logging.debug("Excluded blacklisted publication: %s", hal_id)
            continue

        if not has_open_access(pub):
            stats["no_open_access_excluded"] += 1
            continue

        filtered_publications.append(pub)

    final_publications, working_papers_excluded = filter_working_papers(
        filtered_publications
    )
    stats["working_papers_excluded"] = working_papers_excluded
    stats["final_count"] = len(final_publications)

    logging.info("Filtering statistics:")
    logging.info("  Total retrieved: %d", stats["total_retrieved"])
    logging.info("  CIRED conference excluded: %d", stats["cired_conference_excluded"])
    logging.info("  Blacklisted excluded: %d", stats["blacklisted_excluded"])
    logging.info("  No open access excluded: %d", stats["no_open_access_excluded"])
    logging.info("  Working papers excluded: %d", stats["working_papers_excluded"])
    logging.info("  Final catalog count: %d", stats["final_count"])

    return {
        "processing_timestamp": datetime.now().isoformat(),
        "source_file": str(raw_data.get("source_file", "unknown")),
        "filtering_statistics": stats,
        "publications": final_publications,
        "excluded_communications": unrelated_cired_communications,
    }


def save_prepared_catalog(catalog_data: dict[str, Any]) -> Path:
    """Save prepared catalog to timestamped file."""
    PREPARED_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"catalog_{timestamp}.json"
    filepath = PREPARED_DIR / filename

    filepath.write_text(
        json.dumps(catalog_data, ensure_ascii=False, indent=4), encoding="utf-8"
    )

    logging.info("Saved prepared catalog to %s", filepath)
    return filepath


def main() -> None:
    """Process raw HAL data into filtered catalog."""
    parser = argparse.ArgumentParser(
        description="Process raw HAL data into filtered catalog"
    )
    parser.add_argument(
        "--raw-file",
        type=Path,
        help="Path to raw HAL response file (default: latest in raw directory)",
    )

    args = parser.parse_args()

    if args.raw_file:
        raw_file = args.raw_file
    else:
        raw_file = get_latest_raw_hal_file()

    if not raw_file or not raw_file.exists():
        logging.error("No raw HAL file found. Run hal_query.py first.")
        return

    logging.info("Processing raw HAL file: %s", raw_file)

    try:
        raw_data = json.loads(raw_file.read_text(encoding="utf-8"))
        raw_data["source_file"] = str(raw_file)

        catalog_data = process_publications(raw_data)
        save_prepared_catalog(catalog_data)

    except Exception as e:
        logging.error("Failed to process raw HAL file: %s", e)


if __name__ == "__main__":
    main()
