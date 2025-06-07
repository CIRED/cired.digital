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
- GET /v1/analytics/view: Displays all collected data as HTML tables.
"""

import csv
import os
from typing import Any, Literal

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
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


class Feedback(BaseModel):
    """Schema for incoming feedback data."""

    question: str
    answer: str
    feedback: Literal["up", "down"]
    timestamp: str


class SessionLog(BaseModel):
    """Schema for session start logging."""

    session_id: str
    start_time: str
    privacy_mode: bool = False


class QueryLog(BaseModel):
    """Schema for query logging."""

    session_id: str
    query_id: str
    question: str
    query_parameters: dict[str, Any]
    timestamp: str
    privacy_mode: bool = False


class ResponseLog(BaseModel):
    """Schema for response logging."""

    query_id: str
    response: str
    processing_time: float
    timestamp: str
    privacy_mode: bool = False


class UserProfile(BaseModel):
    """Schema for user profile data."""

    session_id: str
    profession: Literal[
        "étudiant/stagiaire",
        "doctorant",
        "ITA",
        "enseignant/chercheur",
        "journaliste/écrivain",
        "autre",
    ]
    domaine: Literal[
        "environnement/développement",
        "communication/médiation",
        "informatique",
        "autre",
    ]
    affiliation: Literal[
        "CIRED",
        "ParisTech",
        "CNRS",
        "établissement d'enseignement supérieur ou de recherche",
        "entreprise",
        "média",
        "indépendant",
    ]
    anciennete: Literal["des semaines", "des mois", "des années"]
    timestamp: str
    consent_given: bool = True


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


def render_csv_table(filename: str, title: str) -> list[str]:
    """
    Render a CSV file as an HTML table.

    Parameters
    ----------
    filename : str
        Name of the CSV file to render.
    title : str
        Title for the table section.

    Returns
    -------
    list[str]
        HTML lines for the table.

    """
    if not os.path.exists(filename):
        return [f"<h3>{title}</h3>", "<p>Aucune donnée enregistrée.</p>"]

    html = [f"<h3>{title}</h3>", "<table border='1' cellpadding='5'>"]
    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    for i, row in enumerate(rows):
        tag = "th" if i == 0 else "td"
        html.append(
            "<tr>" + "".join(f"<{tag}>{cell}</{tag}>" for cell in row) + "</tr>"
        )
    html.append("</table><br/>")
    return html


@app.post("/v1/feedback")
async def receive_feedback(fb: Feedback) -> dict[str, str]:
    """
    Save user feedback to a CSV file.

    Parameters
    ----------
    fb : Feedback
       Feedback object containing question, answer, feedback type, and timestamp.

    Returns
    -------
    dict
        A JSON response indicating successful storage.

    """
    file_exists = os.path.exists("feedback.csv")
    with open("feedback.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "feedback", "question", "answer"])
        writer.writerow([fb.timestamp, fb.feedback, fb.question, fb.answer])
    return {"message": "Feedback saved"}


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
    html.extend(render_csv_table("queries.csv", "Requêtes Utilisateur"))
    html.extend(render_csv_table("responses.csv", "Réponses du Bot"))
    html.extend(render_csv_table("feedback.csv", "Feedback Utilisateur"))
    html.extend(render_csv_table("profiles.csv", "Profils Utilisateur"))

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


@app.post("/v1/log/query")
async def log_query(query_log: QueryLog) -> dict[str, str]:
    """
    Log user query information.

    Parameters
    ----------
    query_log : QueryLog
        Query logging data.

    Returns
    -------
    dict
        Success message.

    """
    if query_log.privacy_mode:
        return {"message": "Query logged (privacy mode - not saved)"}

    write_to_csv(
        "queries.csv",
        ["session_id", "query_id", "question", "query_parameters", "timestamp"],
        [
            query_log.session_id,
            query_log.query_id,
            query_log.question,
            str(query_log.query_parameters),
            query_log.timestamp,
        ],
    )

    return {"message": "Query logged"}


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
        ["query_id", "response", "processing_time", "timestamp"],
        [
            response_log.query_id,
            response_log.response,
            response_log.processing_time,
            response_log.timestamp,
        ],
    )

    return {"message": "Response logged"}


@app.post("/v1/profile")
async def store_profile(profile: UserProfile) -> dict[str, str]:
    """Store user profile data."""
    write_to_csv(
        "profiles.csv",
        [
            "session_id",
            "profession",
            "domaine",
            "affiliation",
            "anciennete",
            "timestamp",
            "consent_given",
        ],
        [
            profile.session_id,
            profile.profession,
            profile.domaine,
            profile.affiliation,
            profile.anciennete,
            profile.timestamp,
            profile.consent_given,
        ],
    )
    return {"message": "Profile saved"}
