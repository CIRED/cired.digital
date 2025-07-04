"""
Monitor Cirdi app.

A FastAPI application to collect Cirdi analytics.
"""

import json
import os
from datetime import UTC, datetime

from fastapi import FastAPI, Request
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
    return FileResponse(
        os.path.join("templates", "privacy.html"), media_type="text/html"
    )


@app.post("/v1/monitor")
async def monitor_event(request: Request) -> dict[str, str]:
    """
    Log monitoring events.

    Parameters
    ----------
    request : Request
        The incoming request containing the event data.
        Can be sent as JSON (from fetch()) or text/plain (from sendBeacon()).

    Returns
    -------
    dict[str, str]
        Success message.

    """
    # Handle both JSON and text/plain (from sendBeacon)
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        # From fetch()
        event_data = await request.json()
    else:
        # From sendBeacon() - comes as text/plain
        raw_data = await request.body()
        event_data = json.loads(raw_data.decode("utf-8"))

    # Validate with Pydantic
    event = MonitorEvent(**event_data)

    # Get real client IP from proxy headers
    # NPM sets X-Forwarded-For with the original client IP
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs: "client, proxy1, proxy2"
        # The first one is the original client
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        # Fallback to direct connection IP (shouldn't happen with NPM)
        client_ip = request.client.host if request.client else "unknown"

    enriched_event = {
        **event.model_dump(),  # Original client data
        "server_context": {  # Server-added context
            "client_ip": client_ip,
            "forwarded_for": forwarded_for,
            "received_at": datetime.now(UTC).isoformat(),
            "server_version": "1.0.0",
        },
    }

    # Sanitize sessionId, timestamp, eventType for filename:
    #  allow only alphanumeric characters and underscores.
    # Specially necessary for event.sessionId, which is user-provided
    # and could contain characters that are not safe for filenames.
    # This is a security measure to prevent path traversal attacks.
    # Tell CodeQL that we trust our sanitize()
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
    file_path = os.path.normpath(os.path.realpath(os.path.join(dir_path, filename)))
    abs_dir_path = os.path.normpath(os.path.realpath(dir_path))
    # Ensure the resolved file_path is strictly within the intended directory
    if os.path.commonpath([abs_dir_path, file_path]) != abs_dir_path:
        raise ValueError("Invalid file path: potential path traversal detected")

    # CodeQL alert on next line suppressed because we trust sanitize()
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(enriched_event, f, ensure_ascii=False, indent=2)
    return {"message": "Monitor event saved"}
