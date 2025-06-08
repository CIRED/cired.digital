"""
Process raw HAL responses into filtered catalogs.

This script reads the latest raw HAL API response and applies comprehensive
filtering to create a clean catalog of CIRED publications. Filtering includes:
- File size limits
- Working paper deduplication

Usage:
    python prepare_catalog.py [--raw-file PATH] [--log-level LEVEL]

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
    PREPARED_DIR,
    setup_logging,
)
from intake.utils import get_latest_raw_hal_file, normalize_title


def is_working_paper(doc_type: str) -> bool:
    """Check if document type indicates a working paper."""
    if not doc_type:
        return False

    working_paper_types = {"UNDEFINED", "OTHER", "REPORT"}
    return doc_type.upper() in working_paper_types


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

        if published_articles:
            filtered_publications.extend(published_articles)
            excluded_count += len(working_papers)
            if working_papers:
                logging.debug(
                    "Excluded %d working papers for title: %s (published version available)",
                    len(working_papers),
                    normalized_title[:50],
                )
                for wp in working_papers:
                    wp_hal_id = wp.get("halId_s", "unknown")
                    logging.debug("  Working paper excluded: %s", wp_hal_id)
                for pa in published_articles:
                    pa_hal_id = pa.get("halId_s", "unknown")
                    logging.debug("  Published article kept: %s", pa_hal_id)
        else:
            filtered_publications.extend(group)

    return filtered_publications, excluded_count


def process_publications(raw_data: dict[str, Any]) -> dict[str, Any]:
    """Process publications with comprehensive filtering and statistics."""
    publications = raw_data["response"]["docs"]

    stats = {
        "total_retrieved": len(publications),
        "working_papers_excluded": 0,
        "final_count": 0,
    }

    related_publications = []

    for pub in publications:
        pub["label_s"] = html.unescape(pub["label_s"])
        if "producedDate_tdate" in pub:
            pub["producedDate_tdate"] = pub["producedDate_tdate"].split("T")[0]

        related_publications.append(pub)

    filtered_publications = related_publications

    final_publications, working_papers_excluded = filter_working_papers(
        filtered_publications
    )
    stats["working_papers_excluded"] = working_papers_excluded
    stats["final_count"] = len(final_publications)

    logging.info("Filtering statistics:")
    logging.info("  Total retrieved: %d", stats["total_retrieved"])
    logging.info("  Working papers excluded: %d", stats["working_papers_excluded"])
    logging.info("  Final catalog count: %d", stats["final_count"])

    return {
        "processing_timestamp": datetime.now().isoformat(),
        "source_file": str(raw_data.get("source_file", "unknown")),
        "filtering_statistics": stats,
        "publications": sorted(final_publications, key=lambda pub: pub.get("halId_s", "")),
    }


def save_prepared_catalog(catalog_data: dict[str, Any]) -> Path:
    """Save prepared catalog to timestamped file."""
    PREPARED_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"catalog_{timestamp}.json"
    filepath = PREPARED_DIR / filename

    filepath.write_text(
        json.dumps(catalog_data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
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
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error"],
        default="info",
        help="Set logging level (default: info)",
    )

    args = parser.parse_args()

    log_levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
    }

    setup_logging(level=log_levels[args.log_level])

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
        # Afficher les deux premières et les deux dernières entrées pour débogage
        pubs = catalog_data["publications"]
        print("Deux premières entrées :")
        print(json.dumps(pubs[:2], ensure_ascii=False, indent=2, sort_keys=True))
        print("Deux dernières entrées :")
        print(json.dumps(pubs[-2:], ensure_ascii=False, indent=2, sort_keys=True))

    except Exception as e:
        logging.error("Failed to process raw HAL file: %s", e)


if __name__ == "__main__":
    main()
