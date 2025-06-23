"""
Collect and display user feedback and logging data.

A FastAPI application to collect Cirdi analytics.
"""

import json
import os
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
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


PRIVACY_VIEW_HTML = """
<html>
  <head>
    <title>CIRED.digital Analytics</title>
    <style>
      body { font-family: sans-serif; max-width: 700px; margin: 2em auto; }
      h1, h2 { color: #2c3e50; }
      ul { margin-bottom: 2em; }
      .event-type { font-weight: bold; color: #2980b9; }
      .payload { color: #555; font-size: 0.97em; }
      .privacy { background: #f6f8fa; border-left: 4px solid #2980b9; padding: 1em; margin: 2em 0; }
    </style>
  </head>
  <body>
    <h1>CIRED.digital – Données collectées</h1>
    <p>
      Pour améliorer la qualité du service, CIRED.digital collecte des événements d’utilisation.
      <b>Aucune donnée personnelle, identifiant civil ou contenu privé n’est enregistré.</b>
      Le système respecte le mode «&nbsp;confidentialité&nbsp;» si vous l’activez.
    </p>
    <div class="privacy">
      <b>Protection de la vie privée&nbsp;:</b><br>
      – Un identifiant de session anonyme est généré à chaque visite.<br>
      – Vous pouvez activer le mode confidentialité à tout moment, auquel cas aucune donnée n’est envoyée.<br>
      – Les données servent uniquement à l’amélioration du service et à la détection d’anomalies.
      – Les données ne sont pas transmises à des tiers et ne sont pas utilisées à des fins commerciales.
    </div>
    <h2>Types d’événements collectés</h2>
    <ul>
      <li>
        <span class="event-type">session</span> : ouverture d’une session utilisateur.<br>
        <span class="payload">Données&nbsp;: identifiant de session, date/heure, contexte technique.</span>
      </li>
      <li>
        <span class="event-type">request</span> : envoi d’une requête (question, recherche, etc.).<br>
        <span class="payload">Données&nbsp;: session, texte de la requête, paramètres choisis, date/heure.</span>
      </li>
      <li>
        <span class="event-type">response</span> : réponse générée par le système.<br>
        <span class="payload">Données&nbsp;: session, contenu de la réponse, temps de traitement, date/heure.</span>
      </li>
      <li>
        <span class="event-type">article</span> : affichage d’un article ou document.<br>
        <span class="payload">Données&nbsp;: session, identifiant de l’article, contexte d’affichage, date/heure.</span>
      </li>
      <li>
        <span class="event-type">feedback</span> : retour utilisateur (avis, commentaire).<br>
        <span class="payload">Données&nbsp;: session, type de retour (👍/👎), commentaire éventuel, date/heure.</span>
      </li>
      <li>
        <span class="event-type">userProfile</span> : modification de profil ou préférences.<br>
        <span class="payload">Données&nbsp;: session, préférences choisies, date/heure.</span>
      </li>
    </ul>
    <h2>Utilisation des données</h2>
    <ul>
      <li>Amélioration continue du service et de l’ergonomie</li>
      <li>Détection de bugs et d’anomalies</li>
      <li>Statistiques d’usage globales (jamais individuelles)</li>
    </ul>
    <p>
      Pour toute question sur la confidentialité ou la gestion des données, contactez l’équipe CIRED.digital à < minh.ha-duong@cnrs.fr >.
    </p>
  </body>
</html>
"""


@app.get("/v1/view/privacy", response_class=HTMLResponse)
async def view_privacy() -> str:
    """
    Serve the privacy statement.

    Returns
    -------
    str
        An HTML page.

    """
    return PRIVACY_VIEW_HTML


@app.get("/v1/view/analytics", response_class=HTMLResponse)
async def view_analytics() -> str:
    """
    Serve an overview of analytics -- WIP for now serve the privacy.

    Returns
    -------
    str
        An HTML page.

    """
    return PRIVACY_VIEW_HTML


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
    file_path = os.path.join(dir_path, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(event.model_dump(), f, ensure_ascii=False, indent=2)
    return {"message": "Monitor event saved"}
