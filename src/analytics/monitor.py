"""
Monitor Cirdi app.

A FastAPI application to collect Cirdi analytics.
"""

import json
import os
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from models import MonitorEvent
from utils import sanitize

app = FastAPI()

# CORS support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict this in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_class=JSONResponse)
async def health() -> dict[str, str]:
    """Return a simple health check response."""
    return {"status": "ok"}


@app.get("/v1/view/privacy", response_class=HTMLResponse)
async def view_privacy() -> FileResponse:
    """
    Serve the privacy statement with a description of data collected and the user's rights.

    Returns
    -------
    FileResponse
        The privacy HTML page.

    """
    return FileResponse(os.path.join("templates", "privacy.html"), media_type="text/html")


@app.post("/v1/monitor")
async def monitor_event(event: MonitorEvent) -> dict[str, str]:
    """
    Log monitoring events.

    Parameters
    ----------
    event : MonitorEvent
        Monitoring event data.

    Returns
    -------
    dict
        Success message.

    """
    # Validate event type
    #     (already handled by Pydantic/Enum)
    # Sanitize sessionId, timestamp, eventType for filename
    #     (also handled frontside, redone as defensive programming)
    safe_session = sanitize(event.sessionId)
    safe_timestamp = sanitize(event.timestamp)
    safe_type = sanitize(event.eventType)
    # Directory: /data/logs/YYYY/MM/DD/
    now = datetime.now(UTC)
    dir_path = os.path.join(
        "data", "logs", f"{now.year:04d}", f"{now.month:02d}", f"{now.day:02d}"
    )
    os.makedirs(dir_path, exist_ok=True)
    # Now save the event as a JSON file
    filename = f"{safe_session}-{safe_timestamp}-{safe_type}.json"
    file_path = os.path.normpath(os.path.join(dir_path, filename))
    abs_dir_path = os.path.abspath(dir_path)
    abs_file_path = os.path.abspath(file_path)
    # Ensure the file_path is within the intended directory
    if not abs_file_path.startswith(abs_dir_path + os.sep):
        raise ValueError("Invalid file path: potential path traversal detected")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(event.model_dump(), f, ensure_ascii=False, indent=2)
    return {"message": "Monitor event saved"}
