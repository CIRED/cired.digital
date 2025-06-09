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

    # Déduplication avancée selon DOC TYPE et docid
    records = df_filtered.drop(columns="norm_title").to_dict(orient="records")
    pubs_by_doi: dict[str, list[dict]] = {}
    for pub in records:
        doi = pub.get("doiId_s") or ""
        pubs_by_doi.setdefault(doi, []).append(pub)
    pubs_list: list[dict] = []
    duplicates_excluded = 0
    # Ordre de priorité
    priority = {"ART": 1, "COMM": 2, "UNDEFINED": 3}
    for doi, group in pubs_by_doi.items():
        # ne pas toucher aux publications sans DOI
        if not doi:
            pubs_list.extend(group)
            continue
        if len(group) <= 1:
            pubs_list.extend(group)
            continue
        types = {g.get("docType_s") for g in group}
        # cas ouvrage+chapitre → tout garder
        if "OUV" in types and "COUV" in types:
            pubs_list.extend(group)
            # compteur recalculé ultérieurement
            continue
        # on choisit le type le plus prioritaire
        best_prio = min(priority.get(t, 99) for t in types)
        best_type = next(t for t, p in priority.items() if p == best_prio)
        candidats = [g for g in group if g.get("docType_s") == best_type]
        # si plusieurs ART, on prend le docid max
        if best_type == "ART" and len(candidats) > 1:
            sel = max(candidats, key=lambda g: int(g.get("docid", 0)))
        else:
            sel = candidats[0]
        pubs_list.append(sel)
        # compteur recalculé ultérieurement

    # recalcul de duplicates_excluded pour cohérence des stats
    total_after_wp = total - excluded
    duplicates_excluded = total_after_wp - len(pubs_list)

    result = {
        "processing_timestamp": datetime.now().isoformat(),
        "source_file": source_filename,
        "filtering_statistics": {
            "total_retrieved": total,
            "working_papers_excluded": excluded,
            "duplicates_excluded": duplicates_excluded,
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
        "Statistiques catalogue préparé : récupérés=%d, exclus_working_papers=%d, doublons_exclus=%d, final=%d",
        stats.get("total_retrieved", 0),
        stats.get("working_papers_excluded", 0),
        stats.get("duplicates_excluded", 0),
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
