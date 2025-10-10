#!/usr/bin/env python3
"""
analyze_monitor_logs.py — In‑memory loader + normalizer for monitor JSON logs (no DB).

Usage:
  python analyze_monitor_logs.py /path/to/reports/monitor-logs \
      --schema /path/to/af15c2a9-0d25-43f3-aa11-21597abea51b.py \
      --out monitor_analysis

What it does:
  - Recursively loads all *.json files (fits in memory for ~tens of thousands).
  - Optionally validates each JSON against your Pydantic MonitorEvent schema.
  - Normalizes into a flat table with common fields + event-specific columns.
  - Writes CSV + Parquet (fast to reload) and a quick markdown summary.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Optional pandas dependency is standard; parquet uses pyarrow if present
import pandas as pd

FILENAME_RE = re.compile(
    r"^session_(?P<key>[a-zA-Z0-9_-]+)-(?P<ts>\d{8}T\d{6}\d{3})Z-(?P<type>[a-zA-Z]+)\.json$"
)

def parse_filename(name: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    m = FILENAME_RE.match(name)
    if not m:
        return None, None, None
    key = m.group("key")
    ts_compact = m.group("ts")
    ts_iso = f"{ts_compact[0:4]}-{ts_compact[4:6]}-{ts_compact[6:8]}T{ts_compact[9:11]}:{ts_compact[11:13]}:{ts_compact[13:15]}.{ts_compact[15:18]}Z"
    typ = m.group("type")
    return key, ts_iso, typ

def iso_norm(ts: str) -> Optional[str]:
    try:
        if ts.endswith("Z"):
            dt = datetime.fromisoformat(ts.replace("Z","+00:00"))
        else:
            dt = datetime.fromisoformat(ts)
        dt = dt.astimezone(timezone.utc)
        return dt.replace(tzinfo=timezone.utc).isoformat().replace("+00:00","Z")
    except Exception:
        return None

def load_monitor_schema(module_path: Optional[Path]):
    if not module_path:
        return None, None
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("monitor_schema_mod", str(module_path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore
        MonitorEvent = getattr(mod, "MonitorEvent", None)
        MonitorEventType = getattr(mod, "MonitorEventType", None)
        return MonitorEvent, MonitorEventType
    except Exception as e:
        print(f"[WARN] Could not import schema from {module_path}: {e}", file=sys.stderr)
        return None, None

KNOWN_KEYS_BY_EVENT = {
    "request": {"queryId","query","settings","requestBody"},
    "response": {"queryId","timestamp","retrievalTime","generationTime","response"},
    "feedback": {"comment"},
    "userInput": {"action","element","elementText"},
    "visibilityChange": {"visibilityState","sessionDuration"},
    "sessionStart": set(),
    "article": set(),
    "userProfile": set(),
}

def split_known_unknown(event_type: str, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    known = {}
    unknown = {}
    allowed = KNOWN_KEYS_BY_EVENT.get(event_type, set())
    for k,v in (payload or {}).items():
        if k in allowed:
            known[k] = v
        else:
            unknown[k] = v
    return known, unknown

def safe_json_dump(x: Any) -> str:
    try:
        return json.dumps(x, ensure_ascii=False, separators=(",",":"))
    except Exception:
        return repr(x)

def walk_and_collect(root: Path, MonitorEvent=None) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for p in root.rglob("*.json"):
        st = p.stat()
        key_f, ts_f, type_f = parse_filename(p.name)
        type_f = (type_f or "other")
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            rows.append({
                "source_file": str(p),
                "size_bytes": st.st_size,
                "mtime_utc": datetime.utcfromtimestamp(st.st_mtime).isoformat() + "Z",
                "sessionId": key_f or f"unknown-{p.parent.name}",
                "timestamp": ts_f or datetime.utcfromtimestamp(st.st_mtime).isoformat() + "Z",
                "eventType": type_f,
                "canonical_event_type": None,
                "valid": False,
                "validation_error": f"JSON parse error: {e!r}",
                "payload_json": None,
                "payload_unknown_json": None,
            })
            continue

        sessionId = key_f or f"unknown-{p.parent.name}"
        timestamp = ts_f or datetime.utcfromtimestamp(st.st_mtime).isoformat() + "Z"
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
                ts_norm = iso_norm(ev.timestamp) if getattr(ev, "timestamp", None) else None
                if ts_norm:
                    timestamp = ts_norm
            except Exception as e:
                valid = False
                validation_error = f"Pydantic validation error: {e!r}"

        # Extract payload
        payload = doc.get("payload") if isinstance(doc, dict) else None
        known, unknown = split_known_unknown((canonical_event_type or eventType), payload or {})

        row = {
            "source_file": str(p),
            "size_bytes": st.st_size,
            "mtime_utc": datetime.utcfromtimestamp(st.st_mtime).isoformat() + "Z",
            "sessionId": sessionId,
            "timestamp": timestamp,
            "eventType": eventType,
            "canonical_event_type": canonical_event_type,
            "valid": valid,
            "validation_error": validation_error,
            "payload_json": safe_json_dump(payload) if payload is not None else None,
            "payload_unknown_json": safe_json_dump(unknown) if unknown else None,
        }
        # add known fields as top-level columns
        for k,v in known.items():
            # string-ify complex values to keep the table rectangular
            row[k] = v if isinstance(v, (str, int, float, bool)) or v is None else safe_json_dump(v)
        rows.append(row)
    return rows

def write_outputs(rows: List[Dict[str, Any]], out_prefix: Path):
    if not rows:
        print("No JSON files found.")
        return
    df = pd.DataFrame(rows)
    # Ensure stable column order: essentials first
    base_cols = ["sessionId","timestamp","eventType","canonical_event_type","valid","validation_error",
                 "queryId","query","settings","requestBody","timestamp", "retrievalTime","generationTime","response",
                 "comment","action","element","elementText","visibilityState","sessionDuration",
                 "payload_unknown_json","payload_json",
                 "source_file","size_bytes","mtime_utc"]
    cols = [c for c in base_cols if c in df.columns] + [c for c in df.columns if c not in base_cols]
    df = df.reindex(columns=cols)

    csv_path = out_prefix.with_suffix(".csv")
    pq_path  = out_prefix.with_suffix(".parquet")
    md_path  = out_prefix.with_suffix(".md")

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
    lines.append(f"- Validated with schema: {'canonical_event_type' in df.columns and df['canonical_event_type'].notna().any()}")
    lines.append("")
    if "canonical_event_type" in df.columns:
        lines.append("## Events by canonical_event_type")
        lines.append(df["canonical_event_type"].fillna("(none)").value_counts().to_markdown())
        lines.append("")
    if "eventType" in df.columns:
        lines.append("## Events by filename eventType")
        lines.append(df["eventType"].fillna("(none)").value_counts().to_markdown())
        lines.append("")
    if "query" in df.columns:
        top_q = df["query"].dropna().value_counts().head(20)
        if not top_q.empty:
            lines.append("## Top queries")
            lines.append(top_q.to_markdown())
            lines.append("")
    if "validation_error" in df.columns:
        err_counts = df["validation_error"].dropna().value_counts().head(10)
        if not err_counts.empty:
            lines.append("## Validation errors (top 10)")
            lines.append(err_counts.to_markdown())
            lines.append("")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Wrote CSV to {csv_path}")
    print(parquet_note)
    print(f"Wrote markdown summary to {md_path}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path, help="Path to the monitor-logs root directory")
    ap.add_argument("--schema", type=Path, default=None, help="Path to the Pydantic schema file (with MonitorEvent)")
    ap.add_argument("--out", type=Path, default=Path("monitor_analysis"), help="Output file prefix (no extension)")
    args = ap.parse_args()

    MonitorEvent = None
    if args.schema:
        MonitorEvent, _ = load_monitor_schema(args.schema)
        if MonitorEvent is None:
            print("[WARN] Proceeding without validation (schema import failed).", file=sys.stderr)

    rows = walk_and_collect(args.root, MonitorEvent=MonitorEvent)
    write_outputs(rows, args.out)

if __name__ == "__main__":
    main()
