"""
Utility functions for catalog management and title normalization.

This module provides helper functions for finding and working with
timestamped catalog files in the new split workflow, as well as
unified utility functions for title normalization.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd

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
