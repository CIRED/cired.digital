"""
Utility functions for rendering HTML representations of CSV data and metadata for analytics purposes.

This module provides helpers to:
- Render file metadata as HTML
- Abbreviate long cell content with expand/collapse controls
- Insert word wrapping in HTML for specific columns
- Render HTML tables from CSV data, with special handling for certain columns
- Render a CSV file as an HTML table with metadata and error handling
"""

import html as html_lib
from typing import Any


def render_file_metadata(metadata: dict[str, Any], filename: str) -> str:
    """Render HTML displaying file metadata (filename, line count, size, first timestamp)."""
    return (
        f"<div style='font-size:small;color:#888;'>"
        f"Fichier: <b>{filename}</b> | "
        f"Lignes: <b>{metadata.get('line_count', 0)}</b> | "
        f"Taille: <b>{metadata.get('filesize', 0)} octets</b> | "
        f"Premier timestamp: <b>{metadata.get('first_timestamp', '')}</b>"
        f"</div>"
    )


def abbreviate_cell(cell: str, cell_id: str, max_length: int = 300) -> str:
    """
    Return HTML for abbreviated cell content with expand/collapse links if the content exceeds max_length.

    Args:
        cell: The cell content to abbreviate.
        cell_id: Unique identifier for the cell (used for toggling display).
        max_length: Maximum length before abbreviation (default: 300).

    Returns:
        HTML string with abbreviated content and expand/collapse controls.

    """
    safe_cell = html_lib.escape(cell)
    if len(cell) <= max_length:
        return safe_cell
    abbr = safe_cell[:max_length] + "…"
    return (
        f"<span id='abbr-{cell_id}'>{abbr} "
        f"<span class='show-link' onclick=\"toggleCell('{cell_id}')\">[plus]</span>"
        f"</span>"
        f"<div id='full-{cell_id}' class='full-cell' style='display:none'>"
        f"{safe_cell} "
        f"<span class='show-link' onclick=\"toggleCell('{cell_id}')\">[moins]</span>"
        f"</div>"
    )


def html_wordwrap(cell: str, col: str) -> str:
    """
    Insert <wbr> tags for word wrapping on underscores for session_id/query_id, and on 'T' for timestamp.

    Args:
        cell: The cell content to wrap.
        col: The column name (affects wrapping logic).

    Returns:
        HTML string with <wbr> tags inserted as appropriate.

    """
    safe_cell = html_lib.escape(cell)
    if col in ("session_id", "query_id"):
        return safe_cell.replace("_", "_<wbr>")
    if col == "timestamp":
        return safe_cell.replace("T", "<wbr>T")
    return safe_cell
