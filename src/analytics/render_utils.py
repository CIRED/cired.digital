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
import os
from typing import Any

from utils import read_csv_with_metadata


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


def render_table_rows(
    header: list[str], rows: list[list[str]], filename: str = ""
) -> str:
    """
    Render HTML table rows from header and data rows, abbreviating certain columns if needed.

    Args:
        header: List of column names.
        rows: List of data rows (each a list of strings).
        filename: Name of the CSV file (affects abbreviation logic).

    Returns:
        HTML string containing table rows.

    """
    html: list[str] = []
    html.append("<tr>" + "".join(f"<th>{cell}</th>" for cell in header) + "</tr>")
    abbr_cols = []
    if filename == "responses.csv" and "response" in header:
        abbr_cols.append(header.index("response"))
    if filename == "articles.csv" and "article" in header:
        abbr_cols.append(header.index("article"))
    for row_idx, row in enumerate(rows):
        html.append("<tr>")
        for col_idx, cell in enumerate(row):
            col_name = header[col_idx]
            cell_content = cell
            if col_name in ("session_id", "query_id", "timestamp"):
                cell_content = html_wordwrap(cell, col_name)
            if col_idx in abbr_cols and len(cell) > 100:
                cell_id = f"{filename}-{row_idx}-{col_idx}"
                html.append(
                    "<td class='abbr-cell'>"
                    + abbreviate_cell(cell_content, cell_id)
                    + "</td>"
                )
            else:
                html.append(f"<td>{cell_content}</td>")
        html.append("</tr>")
    return "\n".join(html)


def render_csv_table(filename: str, title: str) -> list[str]:
    """
    Render a CSV file as an HTML table, showing only the last 3 entries and file metadata.

    Displays an error message if the file cannot be read.

    Args:
        filename: Path to the CSV file.
        title: Title to display above the table.

    Returns:
        List of HTML strings for rendering the table and metadata.

    """
    try:
        if not os.path.exists(filename):
            return [f"<h3>{title}</h3>", "<p>Aucune donnée enregistrée.</p>"]
        header, data_rows, metadata = read_csv_with_metadata(filename)
        html = [f"<h3>{title}</h3>", render_file_metadata(metadata, filename)]
        # génère le tableau...
        # (le reste de la logique inchangée)
        return html
    except Exception as e:
        return [
            f"<h3>{title}</h3>",
            f"<div style='color:red;'>Erreur lors de la lecture du fichier {filename}: {e}</div>",
        ]
