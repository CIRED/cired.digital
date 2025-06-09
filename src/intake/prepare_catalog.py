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

import pandas as pd

from intake.config import (
    PREPARED_DIR,
    setup_logging,
)
from intake.utils import get_latest_raw_hal_file, normalize_title


def process_publications(
    raw_data: dict[str, Any], source_filename: str
) -> dict[str, Any]:
    """Process publications with comprehensive filtering and statistics via pandas."""
    # Charger en DataFrame
    df = pd.DataFrame(raw_data["response"]["docs"])

    # Statistiques initiales
    total = len(df)

    # Nettoyage des champs
    df["label_s"] = df["label_s"].apply(html.unescape)
    if "producedDate_tdate" in df.columns:
        df["producedDate_tdate"] = (
            df["producedDate_tdate"].astype(str).str.split("T").str[0]
        )

    # Extraction du premier titre si liste et normalisation
    def first_str(x: Any) -> str:
        if isinstance(x, list) and x:
            return str(x[0])
        if isinstance(x, str):
            return x
        return ""

    df["norm_title"] = (
        df.get("title_s", df["label_s"]).apply(first_str).apply(normalize_title)
    )

    # Filtrage des working papers dans chaque groupe
    def is_working_paper(doc_type: Any) -> bool:
        if not isinstance(doc_type, str):
            return False
        return doc_type.upper() in {"UNDEFINED", "OTHER", "REPORT"}

    def filter_group(group: pd.DataFrame) -> pd.DataFrame:
        mask_wp = group["docType_s"].apply(is_working_paper)
        if (~mask_wp).any():
            return group[~mask_wp]
        return group

    df_filtered = df.groupby("norm_title", group_keys=False).apply(filter_group)

    excluded = total - len(df_filtered)

    # Vectorized DOI deduplication with OUV/COUV special case and keep all no-DOI records
    df2 = df_filtered.drop(columns="norm_title").copy()
    # Priority scoring per document type
    priority_map = {"ART": 1, "COMM": 2, "UNDEFINED": 3}
    df2["prio"] = df2["docType_s"].map(priority_map).fillna(99)
    # Separate records without DOI
    no_doi_df = df2[df2["doiId_s"].isna() | (df2["doiId_s"] == "")]
    df_with_doi = df2[~(df2["doiId_s"].isna() | (df2["doiId_s"] == ""))]
    # Identify DOIs with both OUV and COUV to keep all
    special_dois = (
        df_with_doi.groupby("doiId_s")["docType_s"]
           .agg(lambda s: set(s) >= {"OUV", "COUV"})
           .loc[lambda x: x]
           .index
           .tolist()
    )
    special_df = df_with_doi[df_with_doi["doiId_s"].isin(special_dois)]
    dedup_df = df_with_doi[~df_with_doi["doiId_s"].isin(special_dois)]
    # Sort to keep the best document per DOI
    dedup_df = dedup_df.sort_values(
        by=["doiId_s", "prio", "docid"],
        ascending=[True, True, False]
    )
    # Drop duplicates based on raw DOI field
    unique_df = dedup_df.drop_duplicates(subset="doiId_s", keep="first")
    # Combine no-DOI records, special cases and deduplicated records
    final_df = pd.concat([no_doi_df, special_df, unique_df], ignore_index=True)
    pubs_list = final_df.to_dict(orient="records")
    # Recalculate duplicates_excluded
    duplicates_excluded = (total - excluded) - len(pubs_list)

    result = {
        "processing_timestamp": datetime.now().isoformat(),
        "source_file": source_filename,
        "filtering_statistics": {
            "total_retrieved": total,
            "working_papers_excluded": excluded,
            "doi_duplicates_excluded": duplicates_excluded,
            "final_count": len(pubs_list),
        },
        "publications": sorted(
            pubs_list,
            key=lambda pub: pub.get("halId_s", ""),
        ),
    }

    return result


def save_prepared_catalog(catalog_data: dict[str, Any]) -> Path:
    """Save prepared catalog to timestamped file."""
    PREPARED_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"catalog_{timestamp}.json"
    filepath = PREPARED_DIR / filename
    filepath.write_text(
        json.dumps(catalog_data, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    logging.info("Saved prepared catalog to %s", filepath)
    stats = catalog_data.get("filtering_statistics", {})
    logging.info(
        "Prepared catalog stats: retrieved=%d, working_papers_excluded=%d, doi_duplicates_excluded=%d, final=%d",
        stats.get("total_retrieved", 0),
        stats.get("working_papers_excluded", 0),
        stats.get("doi_duplicates_excluded", 0),
        stats.get("final_count", 0),
    )
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
        catalog_data = process_publications(raw_data, str(raw_file))
        save_prepared_catalog(catalog_data)
    except Exception as e:
        logging.error("Failed to process raw HAL file: %s", e)


if __name__ == "__main__":
    main()
