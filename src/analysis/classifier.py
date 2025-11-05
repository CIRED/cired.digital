"""
Classify IP addresses.

This module classifies client IP (CIRED/RENATER/research,
French residential, bots, etc.)

Exports:
- classify_ip(ip): Identify an IP's origin/bot category.
- classify_ua(ua): Identify a user agent's browser/device category.
"""

import ipaddress
import socket

CIRED_SUBNETS = [
    ipaddress.ip_network("193.51.120.0/24"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
]

RENATER_PREFIXES = [
    "193.51.",
    "194.214.",
    "194.254.",
    "195.83.",
    "195.98.224.",
    "144.204.",
    "129.104.",  # École Polytechnique (RENATER-MNT)
    "134.157.",  # Sorbonne/UPMC (RENATER-MNT)
    "194.199.",  # Many edu nets via RENATER (incl. Mines networks)
]


def _is_cired(ip: str) -> bool:
    """
    Return True if the IP belongs to one of the CIRED subnets.

    Gracefully handles invalid IP strings by returning False.
    """
    try:
        ipobj = ipaddress.ip_address(ip)
        return any(ipobj in net for net in CIRED_SUBNETS)
    except ValueError:
        return False


def _quick_label_from_prefix(ip: str) -> str | None:
    """
    Fast classification using simple CIDR/prefix matches.

    Returns a label when a quick decision is possible, otherwise None.
    """
    if _is_cired(ip):
        return "CIRED (CIRAD)"
    if any(ip.startswith(prefix) for prefix in RENATER_PREFIXES):
        return "Recherche"
    if ip.startswith("66.249."):
        return "googlebot"
    if ip.startswith("40.77."):
        return "other bot"
    if ip.startswith("118.70."):
        return "Vietnam"
    return None


def _label_from_host(host: str, ip: str) -> str | None:
    """
    Classification based on reverse DNS hostname content.

    Expects that the PTR lookup already succeeded and `host` is available.
    """
    if host == "doudou":
        return "CIRED (CIRAD)"
    if "cirad" in host:
        return "CIRED (CIRAD)"
    if any(sub in host for sub in ("cnrs", "sorbonne", "agro", "enpc")):
        return "Recherche"
    if host.endswith(
        (
            ".bbox.fr",
            ".wanadoo.fr",
            ".orangecustomers.net",
            ".proxad.net",
            ".sfr.net",
            ".coucou-networks.fr",
        )
    ):
        return "French Residential"
    if host.endswith(".vn"):
        return "Vietnam"

    # Bots with forward-confirmation
    if host.endswith((".googlebot.com", ".google.com")):
        expected = socket.gethostbyname(host)
        return "googlebot" if expected == ip else None
    if host.endswith(
        (
            ".search.msn.com",
            "dataproviderbot.com",
            "amazonaws.com",
            "googleusercontent.com",
        )
    ):
        expected = socket.gethostbyname(host)
        return "other bot" if expected == ip else None

    return None


def classify_ip(ip: str) -> str:
    """
    Classify a client IP into an origin/bot category.

    Return values include: "CIRED (CIRAD)", "Recherche", "French Residential",
    "Vietnam", "googlebot", "other bot", "Unidentified" or None when unsure.
    """
    quick = _quick_label_from_prefix(ip)
    if quick is not None:
        return quick

    try:
        host, _, _ = socket.gethostbyaddr(ip)
    except Exception:
        print(f"PTR fail for {ip}")
        return "Unidentified"

    label = _label_from_host(host, ip)
    if label is not None:
        return label

    print(host)
    return "Unidentified"


def classify_ua(ua: str) -> str:
    """
    Classify a user agent string into browser/device categories.

    Args:
        ua (str): The user agent string to classify.

    Returns:
        str: A classification string indicating the browser/device type.
             Possible return values:
             - "edge": Microsoft Edge browser
             - "chrome-mobile": Chrome browser on mobile device
             - "chrome-desktop": Chrome browser on desktop
             - "firefox": Firefox browser
             - "safari-desktop": Safari browser on macOS
             - "iphone": iPhone device
             - "other": Any user agent that doesn't match the above patterns

    Note:
        Classification is based on string pattern matching in the user agent.
        The function checks patterns in order, so more specific patterns
        (like chrome-mobile) are checked before general ones (like chrome-desktop).

    """
    if "Edg/" in ua:
        return "edge"
    if "Chrome/" in ua and "Mobile" in ua:
        return "chrome-mobile"
    if "Chrome/" in ua:
        return "chrome-desktop"
    if "Firefox/" in ua:
        return "firefox"
    if "Safari/" in ua and "Mac OS X" in ua:
        return "safari-desktop"
    if "iPhone" in ua:
        return "iphone"
    return "other"
