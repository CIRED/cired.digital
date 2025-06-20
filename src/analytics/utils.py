"""
Utility functions for analytics data processing, including CSV file operations and network classification.

This module provides:
- Network classification based on IP address
- Writing rows to CSV files with header management
- Reading CSV files with extraction of metadata (file size, line count, first timestamp)
"""

import csv
import os
from typing import Any


def classify_network(ip_address: str) -> str:
    """
    Classify the network type based on the IP address.

    Args:
        ip_address: The IP address to classify.

    Returns:
        A string representing the network type (e.g., 'CIRED', 'ENPC', 'EXTERNE').

    """
    if ip_address.startswith("193.51.120."):
        return "CIRED"
    elif ip_address.startswith("192.168."):
        return "ENPC"
    else:
        return "EXTERNE"


def write_to_csv(filename: str, headers: list[str], data: list[Any]) -> None:
    """
    Write a row of data to a CSV file, creating the file and writing headers if it does not exist.

    Args:
        filename: Path to the CSV file.
        headers: List of column headers.
        data: List of data values to write as a row.

    """
    file_exists = os.path.exists(filename)
    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(headers)
        writer.writerow(data)


def read_csv_with_metadata(
    filename: str,
) -> tuple[list[str], list[list[str]], dict[str, Any]]:
    """
    Read a CSV file and return its header, data rows, and a metadata dictionary.

    Args:
        filename: Path to the CSV file.

    Returns:
        A tuple (header, data_rows, metadata) where:
            header: List of column names.
            data_rows: List of data rows (each a list of strings).
            metadata: Dict with 'filesize', 'line_count', and 'first_timestamp'.

    """
    if not os.path.exists(filename):
        return [], [], {"filesize": 0, "line_count": 0, "first_timestamp": ""}
    filesize = os.path.getsize(filename)
    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
    line_count = len(rows)
    first_timestamp = ""
    header = rows[0] if rows else []
    data_rows = rows[1:] if len(rows) > 1 else []
    # Correction: check if there is at least one data row and enough columns
    if line_count > 1 and header:
        for i, col in enumerate(header):
            if "time" in col.lower() and len(rows[1]) > i:
                first_timestamp = rows[1][i]
                break
    metadata = {
        "filesize": filesize,
        "line_count": line_count,
        "first_timestamp": first_timestamp,
    }
    return header, data_rows, metadata
