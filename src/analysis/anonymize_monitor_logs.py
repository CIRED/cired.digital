#!/usr/bin/env python3
"""
anonymize_monitor_logs.py — Create an anonymized, redistributable copy of monitor logs.

What it does:
- Recursively walks an input monitor-logs tree (default: reports/monitor-logs/)
- Drops PII and identifiers: removes server_context, sessionId, userAgent, headers, profile
- Skips userProfile events entirely
- Preserves analysis value: keeps eventType, timestamp, payload.query/response and other non-PII fields
- Writes sanitized JSON files to an output tree mirroring YYYY/MM/DD
- Renames files to exclude identifiers: <timestamp>-<eventType>-<seq>.json
- Emits METADATA.json and CHECKSUMS.sha256; can optionally zip the result

Usage:
  python src/analysis/anonymize_monitor_logs.py \
      --input reports/monitor-logs \
      --output data/prepared/monitor-logs-anon \
      --limit 0 \
      --zip

Notes:
- This tool is intentionally dependency-light (stdlib only).
- Timestamps are preserved as-is when present; otherwise, fallback to filename or file mtime.
- Filenames in the anonymized dataset do not carry session identifiers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable


# Matches original filenames like:
#   session_<key>-20250708T131401123Z-request.json
FILENAME_RE = re.compile(
    r"^session_(?P<key>[a-zA-Z0-9_-]+)-(?P<ts>\d{8}T\d{6}\d{3})Z-(?P<type>[a-zA-Z]+)\.json$"
)


@dataclass
class RedactionStats:
    """Statistics from anonymization run: files seen, processed, skipped, errors."""

    total_files: int = 0
    processed: int = 0
    skipped_user_profile: int = 0
    parse_errors: int = 0
    wrote_files: int = 0


def parse_filename(name: str) -> tuple[str | None, str | None, str | None]:
    """Parse original session log filename to extract key, timestamp, event type."""
    m = FILENAME_RE.match(name)
    if not m:
        return None, None, None
    key = m.group("key")
    ts_compact = m.group("ts")
    ts_iso = (
        f"{ts_compact[0:4]}-{ts_compact[4:6]}-{ts_compact[6:8]}T"
        f"{ts_compact[9:11]}:{ts_compact[11:13]}:{ts_compact[13:15]}."
        f"{ts_compact[15:18]}Z"
    )
    typ = m.group("type")
    return key, ts_iso, typ


def iso_norm(ts: str | None) -> str | None:
    """Normalize timestamp to ISO 8601 Z format; return None if parsing fails."""
    if not ts:
        return None
    # Accept already-ISO; otherwise try to coerce; fall back to None on failure
    try:
        if ts.endswith("Z"):
            # Best-effort validation
            return ts
        dt = datetime.fromisoformat(ts)
        return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")
    except Exception:
        return None


def iter_json_files(root: Path) -> Iterable[Path]:
    """Recursively yield all JSON files under root directory."""
    for p in root.rglob("*.json"):
        if p.is_file():
            yield p


def guess_event_type(doc: dict[str, Any], fallback_from_name: str | None) -> str:
    """Extract eventType from doc JSON; fallback to parsed filename type."""
    et = doc.get("eventType")
    if isinstance(et, str) and et:
        return et
    return fallback_from_name or "other"


def is_user_profile_event(event_type: str) -> bool:
    """Check if event should be skipped (userProfile events are omitted)."""
    return event_type == "userProfile"


REDACT_PAYLOAD_KEYS = {"userAgent", "headers", "profile"}


def redact_document(doc: dict[str, Any]) -> dict[str, Any]:
    """Remove PII from document: server_context, sessionId, and sensitive payload keys."""
    # Copy shallowly to avoid mutating input
    red: dict[str, Any] = {k: v for k, v in doc.items() if k not in {"server_context", "sessionId"}}
    payload = red.get("payload")
    if isinstance(payload, dict):
        for k in list(payload.keys()):
            if k in REDACT_PAYLOAD_KEYS:
                payload.pop(k, None)
    return red


def ensure_date_dir(out_root: Path, src_path: Path, doc_ts: str | None) -> Path:
    """Ensure output directory exists, mirroring source YYYY/MM/DD structure."""
    # Try to re-use the same YYYY/MM/DD path from source
    parts = src_path.parts
    # Look for pattern .../YYYY/MM/DD/<file>
    yyyy = mm = dd = None
    for i in range(len(parts) - 3):
        if parts[i].isdigit() and len(parts[i]) == 4 and parts[i + 1].isdigit() and len(parts[i + 1]) == 2 and parts[i + 2].isdigit() and len(parts[i + 2]) == 2:
            yyyy, mm, dd = parts[i], parts[i + 1], parts[i + 2]
    if yyyy and mm and dd:
        out_dir = out_root / yyyy / mm / dd
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir
    # Otherwise derive from timestamp
    if doc_ts:
        try:
            dt = datetime.fromisoformat(doc_ts.replace("Z", "+00:00"))
            out_dir = out_root / f"{dt.year:04d}" / f"{dt.month:02d}" / f"{dt.day:02d}"
            out_dir.mkdir(parents=True, exist_ok=True)
            return out_dir
        except Exception:
            pass
    # Fallback: put at root
    out_root.mkdir(parents=True, exist_ok=True)
    return out_root


def compute_sha256(path: Path) -> str:
    """Compute SHA256 checksum of file for integrity verification."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_metadata(out_root: Path, stats: RedactionStats, started_at: str, finished_at: str) -> None:
    """Write METADATA.json with dataset info, stats, schema, and license."""
    meta = {
        "dataset": "monitor-logs-anonymized",
        "created_at": finished_at,
        "started_at": started_at,
        "version": 1,
        "notes": "Anonymized dataset with PII removed: server_context, sessionId, userAgent, headers, profile. userProfile events omitted.",
        "stats": {
            "total_files_seen": stats.total_files,
            "processed_files": stats.processed,
            "skipped_user_profile": stats.skipped_user_profile,
            "parse_errors": stats.parse_errors,
            "wrote_files": stats.wrote_files,
        },
        "schema": {
            "root_keys": ["timestamp", "eventType", "payload"],
            "dropped_root_keys": ["server_context", "sessionId"],
            "dropped_payload_keys": sorted(REDACT_PAYLOAD_KEYS),
        },
        "license": {
            "spdx": "CC-BY-4.0",
            "url": "https://creativecommons.org/licenses/by/4.0/",
        },
    }
    (out_root / "METADATA.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def write_license(out_root: Path) -> None:
    """Write LICENSE-DATASET.txt with CC BY 4.0 terms."""
    text = (
        "Dataset License: Creative Commons Attribution 4.0 International (CC BY 4.0)\n\n"
        "You are free to share and adapt the material for any purpose, even commercially,\n"
        "under the terms of attribution.\n\n"
        "Full text: https://creativecommons.org/licenses/by/4.0/\n"
    )
    (out_root / "LICENSE-DATASET.txt").write_text(text, encoding="utf-8")


def write_schema_doc(out_root: Path) -> None:
    """Write SCHEMA.md describing anonymized dataset structure."""
    lines = [
        "# Monitor Logs (Anonymized) Schema\n",
        "\n",
        "Each JSON file contains:\n",
        "- `timestamp` (string, ISO 8601, Z)\n",
        "- `eventType` (string)\n",
        "- `payload` (object; userAgent/headers/profile omitted if originally present)\n",
        "\n",
        "Removed fields: `server_context`, `sessionId`.\n",
        "Omitted events: `userProfile`.\n",
        "\n",
        "Filenames: `<timestamp>-<eventType>-<seq>.json` grouped under `YYYY/MM/DD/`.\n",
    ]
    (out_root / "SCHEMA.md").write_text("".join(lines), encoding="utf-8")


def generate_checksums(out_root: Path) -> None:
    """Generate CHECKSUMS.sha256 file for all JSON outputs."""
    entries: list[tuple[str, str]] = []
    for p in out_root.rglob("*.json"):
        digest = compute_sha256(p)
        rel = p.relative_to(out_root).as_posix()
        entries.append((digest, rel))
    entries.sort(key=lambda x: x[1])
    with (out_root / "CHECKSUMS.sha256").open("w", encoding="utf-8") as f:
        for d, rel in entries:
            f.write(f"{d}  {rel}\n")


def zip_output(out_root: Path, zip_name: Path) -> Path:
    """Create zip archive of anonymized dataset."""
    # Create zip archive without compressing metadata files differently
    base_name = zip_name.with_suffix("")
    shutil.make_archive(str(base_name), "zip", root_dir=str(out_root))
    return zip_name


def anonymize_tree(in_root: Path, out_root: Path, limit: int = 0, dry_run: bool = False) -> RedactionStats:
    """Walk input tree, redact and output anonymized events; return stats."""
    stats = RedactionStats()
    seq_by_dir: dict[Path, int] = {}

    for src in iter_json_files(in_root):
        stats.total_files += 1
        # Hard cap if limit is set
        if limit and stats.processed >= limit:
            break

        try:
            doc = json.loads(src.read_text(encoding="utf-8"))
        except Exception:
            stats.parse_errors += 1
            continue

        key_f, ts_f, type_f = parse_filename(src.name)
        event_type = guess_event_type(doc, type_f)
        if is_user_profile_event(event_type):
            stats.skipped_user_profile += 1
            stats.processed += 1
            continue

        ts = iso_norm(doc.get("timestamp")) or ts_f
        if not ts:
            # fallback to mtime
            st = src.stat()
            ts = datetime.fromtimestamp(st.st_mtime, UTC).isoformat().replace("+00:00", "Z")

        red = redact_document(doc)
        red["eventType"] = event_type  # ensure consistent typing
        red["timestamp"] = ts  # ensure normalized

        out_dir = ensure_date_dir(out_root, src, ts)
        seq = seq_by_dir.setdefault(out_dir, 0) + 1
        seq_by_dir[out_dir] = seq
        out_name = f"{ts}-{event_type}-{seq:06d}.json"
        out_path = out_dir / out_name

        if not dry_run:
            out_path.write_text(json.dumps(red, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            stats.wrote_files += 1

        stats.processed += 1

    return stats


def main() -> None:
    """CLI entry point: parse arguments and run anonymization pipeline."""
    ap = argparse.ArgumentParser(description="Anonymize monitor logs for redistribution")
    ap.add_argument("--input", type=Path, default=Path("reports/monitor-logs"), help="Input logs root")
    ap.add_argument("--output", type=Path, default=Path("reports/monitor-logs-anon"), help="Output root directory")
    ap.add_argument("--limit", type=int, default=0, help="Process at most N files (0 = no limit)")
    ap.add_argument("--zip", action="store_true", help="Zip the output directory after generation")
    ap.add_argument("--dry-run", action="store_true", help="Do not write files, just report what would change")
    args = ap.parse_args()

    in_root = args.input
    out_root = args.output
    if not in_root.exists():
        print(f"Input path not found: {in_root}", file=sys.stderr)
        sys.exit(2)

    started_at = datetime.now(UTC).isoformat()
    stats = anonymize_tree(in_root, out_root, limit=args.limit, dry_run=args.dry_run)

    if args.dry_run:
        print(f"[DRY-RUN] Seen: {stats.total_files}, to write: {stats.processed - stats.skipped_user_profile - stats.parse_errors}")
        print(f"[DRY-RUN] Skipped userProfile: {stats.skipped_user_profile}, parse errors: {stats.parse_errors}")
        return

    write_schema_doc(out_root)
    write_license(out_root)
    write_metadata(out_root, stats, started_at=started_at, finished_at=datetime.now(UTC).isoformat())
    generate_checksums(out_root)

    if args.zip:
        zip_name = out_root.with_name(out_root.name + "_" + datetime.now(UTC).strftime("%Y%m%d") + ".zip")
        zip_output(out_root, zip_name)
        print(f"Wrote zip: {zip_name}")

    print(
        f"Done. Seen={stats.total_files}, processed={stats.processed}, wrote={stats.wrote_files}, "
        f"skipped_userProfile={stats.skipped_user_profile}, parse_errors={stats.parse_errors}"
    )


if __name__ == "__main__":
    main()
