"""
Collect and display user feedback and logging data.

A simple FastAPI application to collect and display user feedback
on chatbot answers. Feedback is stored in a local CSV file and
can be retrieved in HTML table format for review.

Endpoints:
- POST /v1/feedback: Accepts user feedback and appends it to a CSV file.
- GET /v1/feedback/view: Displays the collected feedback as an HTML table.
- POST /v1/log/session: Logs session start information.
- POST /v1/log/query: Logs user questions.
- POST /v1/log/response: Logs bot responses.
- POST /v1/log/request: Logs request details.
- GET /v1/analytics/view: Displays all collected data as HTML tables.
"""

import csv
import os
from datetime import datetime
from typing import Any, Literal

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI()

# CORS support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict this in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SessionLog(BaseModel):
    """Schema for session start logging."""

    session_id: str
    start_time: str
    privacy_mode: bool = False


class RequestLog(BaseModel):
    """Schema for request logging."""

    session_id: str
    query_id: str
    query: str
    config: dict[str, Any]
    request_body: dict[str, Any]
    timestamp: str
    privacy_mode: bool = False


class ArticleLog(BaseModel):
    """Schema for request logging."""

    session_id: str
    query_id: str
    article: str
    timestamp: str
    privacy_mode: bool = False


class ResponseLog(BaseModel):
    """Schema for response logging."""

    session_id: str
    query_id: str
    response: dict[str, Any]
    processing_time: float
    timestamp: str
    privacy_mode: bool = False


class Feedback(BaseModel):
    """Schema for incoming feedback data."""

    session_id: str
    query_id: str
    feedback: Literal["up", "down"]
    comment: str | None = None


def classify_network(ip_address: str) -> str:
    """
    Classify network type based on IP address.

    Parameters
    ----------
    ip_address : str
        The IP address to classify.

    Returns
    -------
    str
        Network type (CIRED, ENPC, or EXTERNE).

    """
    if ip_address.startswith("193.51.120."):
        return "CIRED"
    elif ip_address.startswith("192.168."):
        return "ENPC"
    else:
        return "EXTERNE"


def write_to_csv(filename: str, headers: list[str], data: list[Any]) -> None:
    """
    Write data to CSV file with headers if file doesn't exist.

    Parameters
    ----------
    filename : str
        Name of the CSV file.
    headers : list[str]
        Column headers for the CSV.
    data : list
        Row data to write.

    """
    file_exists = os.path.exists(filename)
    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(headers)
        writer.writerow(data)


# Data model headers for verification
DATA_MODEL_HEADERS = {
    "sessions.csv": ["session_id", "start_time", "ip", "network_type"],
    "requests.csv": [
        "session_id",
        "query_id",
        "query",
        "config",
        "request_body",
        "timestamp",
    ],
    "responses.csv": ["query_id", "response", "processing_time", "timestamp"],
    "feedback.csv": ["timestamp", "session_id", "query_id", "feedback", "comment"],
    "articles.csv": ["session_id", "query_id", "article", "timestamp"],
}


def read_csv_with_metadata(filename: str):
    """Reads a CSV file and returns header, data rows, and metadata dict."""
    if not os.path.exists(filename):
        return [], [], {}
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


def render_file_metadata(metadata: dict[str, Any], filename: str) -> str:
    return f"<div style='font-size:small;color:#888;'>Fichier: <b>{filename}</b> | Lignes: <b>{metadata.get('line_count', 0)}</b> | Taille: <b>{metadata.get('filesize', 0)} octets</b> | Premier timestamp: <b>{metadata.get('first_timestamp', '')}</b></div>"


def abbreviate_cell(cell: str, cell_id: str, max_length: int = 300) -> str:
    """Return HTML for abbreviated cell with expand/collapse if needed."""
    import html as html_lib

    safe_cell = html_lib.escape(cell)
    if len(cell) <= max_length:
        return safe_cell
    abbr = safe_cell[:max_length] + "…"
    return (
        f"<span id='abbr-{cell_id}'>{abbr} <span class='show-link' onclick=\"toggleCell('{cell_id}')\">[plus]</span></span>"
        f"<div id='full-{cell_id}' class='full-cell' style='display:none'>{safe_cell} <span class='show-link' onclick=\"toggleCell('{cell_id}')\">[moins]</span></div>"
    )


def html_wordwrap(cell: str, col: str) -> str:
    """
    Insert <wbr> for word wrapping on underscores for session_id/query_id,
    and on 'T' for timestamp.
    """
    import html as html_lib

    safe_cell = html_lib.escape(cell)
    if col in ("session_id", "query_id"):
        return safe_cell.replace("_", "_<wbr>")
    if col == "timestamp":
        return safe_cell.replace("T", "<wbr>T")
    return safe_cell


def render_table_rows(
    header: list[str], rows: list[list[str]], filename: str = ""
) -> str:
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
            # Wordwrap for session_id, query_id, timestamp
            if col_name in ("session_id", "query_id", "timestamp"):
                cell_content = html_wordwrap(cell, col_name)
            # Abbreviation logic
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
    Render a CSV file as an HTML table, showing only the last 3 entries.
    Also display file metadata: filename, line count, file size, first timestamp.
    Verifies if columns match the data model and if header matches the Pydantic declaration.
    """
    try:
        if not os.path.exists(filename):
            return [f"<h3>{title}</h3>", "<p>Aucune donnée enregistrée.</p>"]

        html = [f"<h3>{title}</h3>"]
        header, data_rows, metadata = read_csv_with_metadata(filename)
        html.append(render_file_metadata(metadata, filename))
        # Largeurs fixes pour certaines colonnes courantes (divisées par 2)
        col_widths = {
            "session_id": "140px",
            "query_id": "140px",
            "timestamp": "140px",
            "processing_time": "140px",
            "query": "280px",
        }
        # Génère le style pour les colonnes si possible
        col_styles = []
        if header:
            for col in header:
                width = col_widths.get(col, None)
                if width:
                    col_styles.append(f'<col style="width:{width};">')
                else:
                    col_styles.append("<col>")
        html.append(
            '<table border="1" cellpadding="5" style="width:100%;table-layout:fixed;">'
            + ("\n".join(col_styles) if col_styles else "")
        )
        if not header:
            html.append(
                "<tr><td colspan='99' style='color:red'>Aucun en-tête détecté dans ce fichier CSV.</td></tr></table><br/>"
            )
            return html
        last_rows = data_rows[-3:] if len(data_rows) > 3 else data_rows
        # Use new render_table_rows with abbreviation
        html.append(render_table_rows(header, last_rows, filename))
        html.append("</table><br/>")
        # Check if columns match the data model (header length vs row length)
        mismatch = False
        for idx, row in enumerate(data_rows):
            if len(row) != len(header):
                mismatch = True
                html.append(
                    f"<div style='color:red;font-size:small;'>Avertissement: La ligne {idx + 2} a {len(row)} colonnes, attendu {len(header)}.</div>"
                )
        if not mismatch:
            html.append(
                "<div style='color:green;font-size:small;'>Colonnes conformes au modèle de données.</div>"
            )
        # Check if header matches the Pydantic declaration
        expected = DATA_MODEL_HEADERS.get(filename)
        if expected:
            if header == expected:
                html.append(
                    "<div style='color:green;font-size:small;'>En-têtes conformes à la déclaration Pydantic.</div>"
                )
            else:
                html.append(
                    f"<div style='color:red;font-size:small;'>Avertissement: En-têtes CSV {header} différents du modèle Pydantic {expected}.</div>"
                )
        html.append(f"""
            <form method="post" action="/v1/rotate/{filename}" onsubmit="return rotateCSV(this, '{filename}');">
                <button type="submit">Archiver ce fichier</button>
            </form>
            <div id="rotate-result-{filename}" style="color:green"></div>
            <script>
            async function rotateCSV(form, filename) {{
                event.preventDefault();
                const resp = await fetch(form.action, {{method: "POST"}});
                const data = await resp.json();
                let div = document.getElementById("rotate-result-" + filename);
                if(data.status === "ok") {{
                    div.textContent = "Fichier archivé sous : " + data.archived_as;
                    setTimeout(()=>window.location.reload(), 1000);
                }} else {{
                    div.style.color = "red";
                    div.textContent = "Erreur : " + (data.error || "inconnue");
                }}
                return false;
            }}
            </script>
        """)
        # Add CSS/JS for abbreviation
        html.append("""
        <style>
        .abbr-cell { white-space: pre-wrap; max-width: 100vw; overflow-x: auto; word-break: break-word; }
        .full-cell { display: none; white-space: pre-wrap; background: #f9f9f9; border: 1px solid #ccc; padding: 8px; margin-top: 4px; word-break: break-word; width: 100%; }
        .show-link { color: #0074d9; cursor: pointer; text-decoration: underline; }
        </style>
        <script>
        function toggleCell(id) {
            var abbr = document.getElementById('abbr-'+id);
            var full = document.getElementById('full-'+id);
            if (abbr.style.display !== 'none') {
                abbr.style.display = 'none';
                full.style.display = 'block';
            } else {
                abbr.style.display = 'inline';
                full.style.display = 'none';
            }
        }
        </script>
        """)
        return html
    except Exception as e:
        return [
            f"<h3>{title}</h3>",
            f"<div style='color:red;'>Erreur lors de la lecture du fichier {filename}: {e}</div>",
        ]


@app.post("/v1/feedback")
async def receive_feedback(fb: Feedback) -> dict[str, str]:
    """
    Save user feedback to a CSV file.

    Parameters
    ----------
    fb : Feedback
       Feedback object containing session_id, query_id, feedback type, and comment.

    Returns
    -------
    dict
        A JSON response indicating successful storage.

    """
    file_exists = os.path.exists("feedback.csv")
    from datetime import datetime

    timestamp = datetime.now().isoformat()
    with open("feedback.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "timestamp",
                "session_id",
                "query_id",
                "feedback",
                "comment",
            ])
        writer.writerow([
            timestamp,
            fb.session_id,
            fb.query_id,
            fb.feedback,
            fb.comment or "",
        ])
    return {"message": "Feedback saved"}


@app.post("/v1/rotate/{filename}")
async def rotate_csv(filename: str):
    # Sécurise le nom de fichier
    if filename not in DATA_MODEL_HEADERS:
        return JSONResponse({"error": "Fichier non autorisé."}, status_code=400)
    base = filename.rsplit(".", 1)[0]
    ext = filename.rsplit(".", 1)[-1]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_name = f"{base}_{timestamp}.{ext}"
    try:
        os.rename(filename, new_name)
        return {"status": "ok", "archived_as": new_name}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/v1/feedback/view", response_class=HTMLResponse)
async def view_feedback() -> str:
    """
    Render stored feedback as an HTML table.

    Returns
    -------
    - An HTML page showing feedback in tabular format, or a message if no data exists.

    """
    if not os.path.exists("feedback.csv"):
        return "<h3>No feedback recorded yet.</h3>"

    html = ["<h2>Feedback Table</h2>", "<table border='1' cellpadding='5'>"]
    with open("feedback.csv", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    for i, row in enumerate(rows):
        tag = "th" if i == 0 else "td"
        html.append(
            "<tr>" + "".join(f"<{tag}>{cell}</{tag}>" for cell in row) + "</tr>"
        )
    html.append("</table>")
    return "\n".join(html)


@app.get("/v1/analytics/view", response_class=HTMLResponse)
async def view_analytics() -> str:
    """
    Render all collected data as HTML tables.

    Returns
    -------
    str
        An HTML page showing all data tables (sessions, queries, responses, feedback).

    """
    html = [
        "<html><head><title>CIRED.digital Analytics</title></head><body>",
        "<h1>CIRED.digital - Données Collectées</h1>",
        "<p>Voici un aperçu de toutes les données collectées par le système de journalisation.</p>",
    ]

    html.extend(render_csv_table("sessions.csv", "Sessions"))
    html.extend(render_csv_table("requests.csv", "Requêtes API"))
    html.extend(render_csv_table("responses.csv", "Réponses du RAG"))
    html.extend(render_csv_table("articles.csv", "Article montré à l'utilisateur"))
    html.extend(render_csv_table("feedback.csv", "Feedback Utilisateur"))

    html.extend(["</body></html>"])
    return "\n".join(html)


@app.post("/v1/log/session")
async def log_session(session_log: SessionLog, request: Request) -> dict[str, str]:
    """
    Log session start information.

    Parameters
    ----------
    session_log : SessionLog
        Session logging data.
    request : Request
        FastAPI request object to extract client IP.

    Returns
    -------
    dict
        Success message.

    """
    if session_log.privacy_mode:
        return {"message": "Session logged (privacy mode - not saved)"}

    client_ip = request.client.host if request.client else "unknown"
    network_type = classify_network(client_ip)

    write_to_csv(
        "sessions.csv",
        ["session_id", "start_time", "ip", "network_type"],
        [session_log.session_id, session_log.start_time, client_ip, network_type],
    )

    return {"message": "Session logged"}


@app.post("/v1/log/request")
async def log_request(request_log: RequestLog) -> dict[str, str]:
    """
    Log request information.

    Parameters
    ----------
    request_log : RequestLog
        Request logging data.

    Returns
    -------
    dict
        Success message.

    """
    if request_log.privacy_mode:
        return {"message": "Request logged (privacy mode - not saved)"}

    write_to_csv(
        "requests.csv",
        ["session_id", "query_id", "query", "config", "request_body", "timestamp"],
        [
            request_log.session_id,
            request_log.query_id,
            request_log.query,
            str(request_log.config),
            str(request_log.request_body),
            request_log.timestamp,
        ],
    )
    return {"message": "Request logged"}


@app.post("/v1/log/article")
async def log_article(article_log: ArticleLog) -> dict[str, str]:
    """Log article HTML content for a query/session."""
    if article_log.privacy_mode:
        return {"message": "Article logged (privacy mode - not saved)"}

    write_to_csv(
        "articles.csv",
        ["session_id", "query_id", "article", "timestamp"],
        [
            article_log.session_id,
            article_log.query_id,
            article_log.article,
            article_log.timestamp,
        ],
    )
    return {"message": "Article logged"}


@app.post("/v1/log/response")
async def log_response(response_log: ResponseLog) -> dict[str, str]:
    """
    Log bot response information.

    Parameters
    ----------
    response_log : ResponseLog
        Response logging data.

    Returns
    -------
    dict
        Success message.

    """
    if response_log.privacy_mode:
        return {"message": "Response logged (privacy mode - not saved)"}

    write_to_csv(
        "responses.csv",
        ["session_id", "query_id", "response", "processing_time", "timestamp"],
        [
            response_log.session_id,
            response_log.query_id,
            response_log.response,
            response_log.processing_time,
            response_log.timestamp,
        ],
    )

    return {"message": "Response logged"}


@app.get("/v1/csv/list", response_class=HTMLResponse)
async def list_csv_files():
    """
    List all CSV files in the current directory, with [View] and [Download] buttons after the filename.

    Returns
    -------
    str
        An HTML page with the list of CSV files and their actions.

    """
    import os

    files = [f for f in os.listdir(".") if f.endswith(".csv") and os.path.isfile(f)]
    html = ["<h2>CSV Files</h2>", "<ul style='list-style-type:none;padding:0;'>"]
    for f in files:
        html.append(
            f"<li style='margin-bottom:8px;'><b>{f}</b> "
            f"<a href='/v1/csv/view/{f}' style='margin-left:10px;'><button>[View]</button></a> "
            f"<a href='/v1/csv/download/{f}' style='margin-left:5px;'><button>[Download]</button></a>"
            f"</li>"
        )
    html.append("</ul>")
    return "\n".join(html)


@app.get("/v1/csv/view/{filename}", response_class=HTMLResponse)
async def view_csv_file(filename: str):
    """
    Render a CSV file as an HTML table.

    Parameters
    ----------
    filename : str
        Name of the CSV file.

    Returns
    -------
    str
        HTML table of the CSV file.

    """
    if not filename.endswith(".csv") or not os.path.isfile(filename):
        # Always show the archive button, even if file not found
        html = [f"<h2>{filename}</h2>"]
        html.append("<h3>Fichier non trouvé.</h3>")
        html.append(f"""
            <form method="post" action="/v1/rotate/{filename}" onsubmit="return rotateCSV(this, '{filename}');">
                <button type="submit">Archiver ce fichier</button>
            </form>
            <div id="rotate-result-{filename}" style="color:green"></div>
            <script>
            async function rotateCSV(form, filename) {{
                event.preventDefault();
                const resp = await fetch(form.action, {{method: "POST"}});
                const data = await resp.json();
                let div = document.getElementById("rotate-result-" + filename);
                if(data.status === "ok") {{
                    div.textContent = "Fichier archivé sous : " + data.archived_as;
                    setTimeout(()=>window.location.reload(), 1000);
                }} else {{
                    div.style.color = "red";
                    div.textContent = "Erreur : " + (data.error || "inconnue");
                }}
                return false;
            }}
            </script>
        """)
        return "\n".join(html)
    html = [f"<h2>{filename}</h2>", "<table border='1' cellpadding='5'>"]
    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            tag = "th" if i == 0 else "td"
            html.append(
                "<tr>" + "".join(f"<{tag}>{cell}</{tag}>" for cell in row) + "</tr>"
            )
    html.append("</table>")
    return "\n".join(html)


@app.get("/v1/csv/download/{filename}")
async def download_csv_file(filename: str):
    """
    Download a CSV file.

    Parameters
    ----------
    filename : str
        Name of the CSV file.

    Returns
    -------
    FileResponse
        The CSV file as an attachment.

    """
    if not filename.endswith(".csv") or not os.path.isfile(filename):
        return JSONResponse({"error": "Fichier non trouvé."}, status_code=404)
    return FileResponse(filename, media_type="text/csv", filename=filename)
