import csv
import os
from datetime import datetime
from typing import Any

def classify_network(ip_address: str) -> str:
    if ip_address.startswith("193.51.120."):
        return "CIRED"
    elif ip_address.startswith("192.168."):
        return "ENPC"
    else:
        return "EXTERNE"

def write_to_csv(filename: str, headers: list[str], data: list[Any]) -> None:
    file_exists = os.path.exists(filename)
    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(headers)
        writer.writerow(data)
