"""
Utility functions for catalog management and title normalization.

This module provides helper functions for finding and working with
timestamped catalog files in the new split workflow, as well as
unified utility functions for title normalization.
"""

import json
import logging
import re
from collections.abc import Hashable, Mapping
from pathlib import Path
from typing import Any

import pandas as pd
from r2r import R2RClient

from intake.config import CATALOG_FILE, PREPARED_DIR, RAW_HAL_DIR


def get_latest_raw_hal_file() -> Path | None:
    """Find the most recent raw HAL response file."""
    if not RAW_HAL_DIR.exists():
        return None

    hal_files = list(RAW_HAL_DIR.glob("hal_response_*.json"))
    if not hal_files:
        return None

    return max(hal_files, key=lambda f: f.stat().st_mtime)


def get_latest_prepared_catalog() -> Path | None:
    """Find the most recent prepared catalog file."""
    if not PREPARED_DIR.exists():
        return None

    catalog_files = list(PREPARED_DIR.glob("catalog_*.json"))
    if not catalog_files:
        return None

    return max(catalog_files, key=lambda f: f.stat().st_mtime)


def load_latest_prepared_catalog() -> dict[str, Any] | None:
    """Load the most recent prepared catalog."""
    catalog_file = get_latest_prepared_catalog()
    if not catalog_file:
        return None

    try:
        catalog_data: dict[str, Any] = json.loads(
            catalog_file.read_text(encoding="utf-8")
        )
        return catalog_data
    except Exception as e:
        logging.error("Failed to load prepared catalog %s: %s", catalog_file, e)
        return None


def get_catalog_publications(catalog_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract publications list from catalog data structure."""
    if "publications" in catalog_data:
        publications: list[dict[str, Any]] = catalog_data["publications"]
        return publications
    elif isinstance(catalog_data, list):
        publications_list: list[dict[str, Any]] = catalog_data
        return publications_list
    else:
        return []


def get_catalog_file(catalog_arg: Path | None = None) -> Path | None:
    """Get catalog file path with unified fallback logic."""
    if catalog_arg:
        return catalog_arg

    catalog_file = get_latest_prepared_catalog()
    if catalog_file:
        return catalog_file

    if CATALOG_FILE.exists():
        return CATALOG_FILE

    return None


def normalize_title(title: str | list[str] | float | None) -> str:
    """Normalize title for comparison, handling various input types."""
    if not title or (isinstance(title, float) and pd.isna(title)):
        return ""

    if isinstance(title, list):
        title = title[0] if title else ""

    title = str(title).lower()
    title = re.sub(r"[^\w\s]", "", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title


DOCUMENTS_FILE = "documents.csv"
COLUMN_CONFIG: Mapping[str, Mapping[str, str | bool]] = {
    "id": {"dtype": "string", "parse_dates": False},
    "title": {"dtype": "string", "parse_dates": False},
    "size_in_bytes": {"dtype": "int64", "parse_dates": False},
    "ingestion_status": {"dtype": "string", "parse_dates": False},
    "extraction_status": {"dtype": "string", "parse_dates": False},
    "created_at": {"dtype": "string", "parse_dates": True},
    "updated_at": {"dtype": "string", "parse_dates": True},
    "type": {"dtype": "string", "parse_dates": False},
    "metadata": {"dtype": "string", "parse_dates": False},
}


def get_existing_documents(client: R2RClient) -> pd.DataFrame | None:
    """
    Retrieve all documents from the R2R service as a structured DataFrame.

    This function:
    - Exports document metadata from the R2R client to a CSV file.
    - Loads the CSV file into a pandas DataFrame with proper type and date parsing.
    - Parses the 'metadata' column as JSON and flattens it into prefixed columns.

    Args:
    ----
        client (R2RClient): The connected R2R client instance.

    Returns:
    -------
        pd.DataFrame | None: A DataFrame with one row per document and enriched metadata columns,
        or None if retrieval or parsing fails.

    """
    try:
        # 1. Export documents from the R2R server to a local CSV file
        logging.debug(f"Exporting document metadata to '{DOCUMENTS_FILE}'...")
        client.documents.export(
            output_path=DOCUMENTS_FILE, columns=list(COLUMN_CONFIG.keys())
        )

        # 2. Load the CSV into a DataFrame with typed columns and date parsing
        df = pd.read_csv(
            DOCUMENTS_FILE, dtype=get_column_dtypes(), parse_dates=get_date_columns()
        )

        # 3. Parse the 'metadata' column (a JSON string per row) into Python dicts
        df["metadata"] = df["metadata"].apply(json.loads)

        # 4. Flatten the nested metadata into separate columns, prefixed with 'meta_'
        metadata_flat = pd.json_normalize(df["metadata"].tolist()).add_prefix("meta_")

        # 5. Drop the original 'metadata' column and merge the flattened metadata
        df = df.drop(columns=["metadata"]).join(metadata_flat)

        # 6. Done
        logging.info(f"Loaded {len(df)} document records with enriched metadata.")
        return df

    except Exception as e:
        logging.error(f"Failed to load document data: {e}")
        return None


def get_column_dtypes() -> Mapping[Hashable, str]:
    """Extract dtype mapping from column configuration."""
    return {col: str(config["dtype"]) for col, config in COLUMN_CONFIG.items()}


def get_date_columns() -> list[str]:
    """Extract list of columns that should be parsed as dates."""
    return [col for col, config in COLUMN_CONFIG.items() if config["parse_dates"]]
