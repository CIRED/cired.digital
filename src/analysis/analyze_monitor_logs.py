#!/usr/bin/env python3
"""
analyze_monitor_logs.py — In‑memory loader + normalizer for monitor JSON logs.

Usage:
  python analyze_monitor_logs.py ../../reports/monitor-logs/ \
      --schema ../monitor/models.py\
      --out monitor_analysis

What it does:
  - Recursively loads all *.json files (fits in memory for ~tens of thousands).
  - Optionally validates each JSON against your Pydantic MonitorEvent schema.
  - Normalizes into a flat table with common fields + event-specific columns.
  - Writes CSV + Parquet (fast to reload) and a quick markdown summary.
"""

import argparse
import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Regex pattern for parsing session log filenames
FILENAME_RE = re.compile(
    r"^session_(?P<key>[a-zA-Z0-9_-]+)-(?P<ts>\d{8}T\d{6}\d{3})Z-"
    r"(?P<type>[a-zA-Z]+)\.json$"
)


def parse_filename(name: str) -> tuple[str | None, str | None, str | None]:
    """
    Parse session filename to extract key, timestamp, and event type.

    Args:
    ----
        name: The filename to parse.

    Returns:
    -------
        A tuple of (session_key, iso_timestamp, event_type).
        Returns (None, None, None) if filename doesn't match expected pattern.

    """
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


def iso_norm(ts: str) -> str | None:
    """
    Normalize ISO timestamp to UTC format.

    Args:
    ----
        ts: ISO format timestamp string.

    Returns:
    -------
        Normalized UTC timestamp string, or None if parsing fails.

    """
    try:
        if ts.endswith("Z"):
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(ts)
        dt = dt.astimezone(UTC)
        return dt.replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")
    except Exception:
        return None


def load_monitor_schema(module_path: Path | None) -> tuple[Any, Any]:
    """
    Load MonitorEvent and MonitorEventType from schema module.

    Args:
    ----
        module_path: Path to the Python module containing schema definitions.

    Returns:
    -------
        A tuple of (MonitorEvent, MonitorEventType) classes.
        Returns (None, None) if import fails.

    """
    if not module_path:
        return None, None
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "monitor_schema_mod", str(module_path)
        )
        if spec is None or spec.loader is None:
            return None, None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        MonitorEvent = getattr(mod, "MonitorEvent", None)
        MonitorEventType = getattr(mod, "MonitorEventType", None)
        return MonitorEvent, MonitorEventType
    except Exception as e:
        logger.warning("Could not import schema from %s: %s", module_path, e)
        return None, None


# Known payload fields for each event type
KNOWN_KEYS_BY_EVENT = {
    "request": {"queryId", "query", "settings", "requestBody"},
    "response": {
        "queryId",
        "timestamp",
        "retrievalTime",
        "generationTime",
        "response",
    },
    "feedback": {"comment"},
    "userInput": {"action", "element", "elementText"},
    "visibilityChange": {"visibilityState", "sessionDuration"},
    "sessionStart": set(),
    "article": set(),
    "userProfile": set(),
}


def split_known_unknown(
    event_type: str, payload: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Split payload into known and unknown fields based on event type.

    Args:
    ----
        event_type: The type of event being processed.
        payload: The event payload dictionary.

    Returns:
    -------
        A tuple of (known_fields, unknown_fields) dictionaries.

    """
    known = {}
    unknown = {}
    allowed = KNOWN_KEYS_BY_EVENT.get(event_type, set())
    for k, v in (payload or {}).items():
        if k in allowed:
            known[k] = v
        else:
            unknown[k] = v
    return known, unknown


def safe_json_dump(x: Any) -> str:
    """
    Safely serialize object to JSON string.

    Args:
    ----
        x: Object to serialize.

    Returns:
    -------
        JSON string representation, or repr() fallback if serialization fails.

    """
    try:
        return json.dumps(x, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        return repr(x)


def walk_and_collect(root: Path, MonitorEvent: Any = None) -> list[dict[str, Any]]:
    """
    Walk directory tree and collect all monitor events.

    Args:
    ----
        root: Root directory to search for JSON files.
        MonitorEvent: Optional Pydantic model for validation.

    Returns:
    -------
        List of dictionaries containing normalized event data.

    """
    rows: list[dict[str, Any]] = []
    for p in root.rglob("*.json"):
        st = p.stat()
        key_f, ts_f, type_f = parse_filename(p.name)
        type_f = type_f or "other"
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            rows.append(
                {
                    "source_file": str(p),
                    "size_bytes": st.st_size,
                    "mtime_utc": datetime.fromtimestamp(st.st_mtime, UTC).isoformat(),
                    "sessionId": key_f or f"unknown-{p.parent.name}",
                    "timestamp": (
                        ts_f or datetime.fromtimestamp(st.st_mtime, UTC).isoformat()
                    ),
                    "eventType": type_f,
                    "canonical_event_type": None,
                    "valid": False,
                    "validation_error": f"JSON parse error: {e!r}",
                    "payload_json": None,
                    "payload_unknown_json": None,
                }
            )
            continue

        sessionId = key_f or f"unknown-{p.parent.name}"
        timestamp = ts_f or datetime.fromtimestamp(st.st_mtime, UTC).isoformat()
        eventType = type_f
        canonical_event_type = None
        valid = True
        validation_error = None

        if MonitorEvent is not None:
            try:
                ev = MonitorEvent.model_validate(doc)
                sessionId = ev.sessionId or sessionId
                eventType = type_f  # keep filename type as reference
                canonical_event_type = str(ev.eventType)
                # normalize timestamp from payload
                ts_norm = (
                    iso_norm(ev.timestamp) if getattr(ev, "timestamp", None) else None
                )
                if ts_norm:
                    timestamp = ts_norm
            except Exception as e:
                valid = False
                validation_error = f"Pydantic validation error: {e!r}"

        # Extract payload
        payload = doc.get("payload") if isinstance(doc, dict) else None
        known, unknown = split_known_unknown(
            (canonical_event_type or eventType), payload or {}
        )

        row = {
            "source_file": str(p),
            "size_bytes": st.st_size,
            "mtime_utc": datetime.fromtimestamp(st.st_mtime, UTC).isoformat(),
            "sessionId": sessionId,
            "timestamp": timestamp,
            "eventType": eventType,
            "canonical_event_type": canonical_event_type,
            "valid": valid,
            "validation_error": validation_error,
            "payload_json": (safe_json_dump(payload) if payload is not None else None),
            "payload_unknown_json": safe_json_dump(unknown) if unknown else None,
        }
        # add known fields as top-level columns
        for k, v in known.items():
            # string-ify complex values to keep the table rectangular
            row[k] = (
                v
                if isinstance(v, str | int | float | bool) or v is None
                else safe_json_dump(v)
            )
        rows.append(row)
    return rows


# The function is too complex, we have to break it down someday
def write_outputs(rows: list[dict[str, Any]], out_prefix: Path) -> None:  # noqa: C901
    """
    Write collected rows to CSV, Parquet, and Markdown summary.

    Args:
    ----
        rows: List of event dictionaries to write.
        out_prefix: Output file path prefix (without extension).

    """
    if not rows:
        logger.info("No JSON files found.")
        return

    df = pd.DataFrame(rows)

    # Ensure stable column order: essentials first
    base_cols = [
        "sessionId",
        "timestamp",
        "eventType",
        "canonical_event_type",
        "valid",
        "validation_error",
        "queryId",
        "query",
        "settings",
        "requestBody",
        "retrievalTime",
        "generationTime",
        "response",
        "comment",
        "action",
        "element",
        "elementText",
        "visibilityState",
        "sessionDuration",
        "payload_unknown_json",
        "payload_json",
        "source_file",
        "size_bytes",
        "mtime_utc",
    ]
    cols = [c for c in base_cols if c in df.columns] + [
        c for c in df.columns if c not in base_cols
    ]
    df = df.reindex(columns=cols)

    csv_path = out_prefix.with_suffix(".csv")
    pq_path = out_prefix.with_suffix(".parquet")
    md_path = out_prefix.with_suffix(".md")

    df.to_csv(csv_path, index=False)
    try:
        df.to_parquet(pq_path, index=False)
        parquet_note = f"Wrote Parquet to {pq_path}"
    except Exception as e:
        parquet_note = f"Parquet not written (missing pyarrow/fastparquet?): {e}"

    # Quick markdown summary
    lines = []
    lines.append("# Monitor logs summary\n")
    lines.append(f"- Rows: {len(df)}")
    has_validation = (
        "canonical_event_type" in df.columns
        and df["canonical_event_type"].notna().any()
    )
    lines.append(f"- Validated with schema: {has_validation}")
    lines.append("")

    # Check if tabulate is available for markdown tables
    try:
        import tabulate  # type: ignore[import-untyped]  # noqa: F401

        use_markdown = True
    except ImportError:
        use_markdown = False
        logger.warning(
            "tabulate not installed - writing plain text tables instead of markdown"
        )

    if "canonical_event_type" in df.columns:
        lines.append("## Events by canonical_event_type")
        counts = df["canonical_event_type"].fillna("(none)").value_counts()
        if use_markdown:
            lines.append(counts.to_markdown())
        else:
            lines.append(counts.to_string())
        lines.append("")

    if "eventType" in df.columns:
        lines.append("## Events by filename eventType")
        counts = df["eventType"].fillna("(none)").value_counts()
        if use_markdown:
            lines.append(counts.to_markdown())
        else:
            lines.append(counts.to_string())
        lines.append("")

    if "query" in df.columns:
        top_q = df["query"].dropna().value_counts().head(20)
        if not top_q.empty:
            lines.append("## Top queries")
            if use_markdown:
                lines.append(top_q.to_markdown())
            else:
                lines.append(top_q.to_string())
            lines.append("")

    if "validation_error" in df.columns:
        err_counts = df["validation_error"].dropna().value_counts().head(10)
        if not err_counts.empty:
            lines.append("## Validation errors (top 10)")
            if use_markdown:
                lines.append(err_counts.to_markdown())
            else:
                lines.append(err_counts.to_string())
            lines.append("")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info("Wrote CSV to %s", csv_path)
    logger.info("%s", parquet_note)
    logger.info("Wrote markdown summary to %s", md_path)


def main() -> None:
    """Load monitor logs, validate, normalize, and export to CSV/Parquet/Markdown."""
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path, help="Path to the monitor-logs root directory")
    ap.add_argument(
        "--schema",
        type=Path,
        default=None,
        help="Path to the Pydantic schema file (with MonitorEvent)",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("monitor_analysis"),
        help="Output file prefix (no extension)",
    )
    args = ap.parse_args()

    MonitorEvent = None
    if args.schema:
        MonitorEvent, _ = load_monitor_schema(args.schema)
        if MonitorEvent is None:
            logger.warning("Proceeding without validation (schema import failed).")

    rows = walk_and_collect(args.root, MonitorEvent=MonitorEvent)
    write_outputs(rows, args.out)


if __name__ == "__main__":
    main()
