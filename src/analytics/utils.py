"""
Utility functions for analytics data processing.

This module provides:
- Sanitization of strings for safe use as filenames or identifiers
- Network classification based on IP address
"""


def sanitize(s: str) -> str:
    """Ensure the string is safe for use as a filename or identifier."""
    return "".join(c if c.isalnum() else "_" for c in s).strip("_")


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
    else:
        return "EXTERNE"
