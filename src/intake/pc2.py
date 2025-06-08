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


def process_publications(raw_data: dict[str, Any]) -> dict[str, Any]:
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
            return x[0]
        if isinstance(x, str):
            return x
        return ""

    df["norm_title"] = df.get("title_s", df["label_s"]).apply(first_str).apply(normalize_title)

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

    # Construction du résultat
    result = {
        "processing_timestamp": datetime.now().isoformat(),
        "source_file": raw_data.get("source_file", "unknown"),
        "filtering_statistics": {
            "total_retrieved": total,
            "working_papers_excluded": excluded,
            "final_count": len(df_filtered),
        },
        "publications": sorted(df_filtered.drop(columns="norm_title").to_dict(orient="records"), key=lambda pub: pub.get("halId_s", "")),
    }

    return result


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
        # Nettoyage des NaN pour l'enregistrement
        from math import isnan
        def _clean(pub):
            return {k: v for k, v in pub.items() if not (isinstance(v, float) and isnan(v))}
        catalog_data["publications"] = [_clean(p) for p in catalog_data["publications"]]
        save_prepared_catalog(catalog_data)
        # Afficher les deux premières et les deux dernières entrées pour débogage
        pubs = catalog_data["publications"]
        # Nettoyer les NaN avant affichage debug
        from math import isnan
        def _clean(pub):
            return {k: v for k, v in pub.items() if not (isinstance(v, float) and isnan(v))}
        clean_pubs = [_clean(p) for p in pubs]
        print("Deux premières entrées :")
        print(json.dumps(clean_pubs[:2], ensure_ascii=False, indent=2, sort_keys=True))
        print("Deux dernières entrées :")
        print(json.dumps(clean_pubs[-2:], ensure_ascii=False, indent=2, sort_keys=True))
    except Exception as e:
        logging.error("Failed to process raw HAL file: %s", e)


if __name__ == "__main__":
    main()
