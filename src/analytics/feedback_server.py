"""
Collect and display user feedback.

A simple FastAPI application to collect and display user feedback
on chatbot answers. Feedback is stored in a local CSV file and
can be retrieved in HTML table format for review.

Endpoints:
- POST /v1/feedback: Accepts user feedback and appends it to a CSV file.
- GET /v1/feedback/view: Displays the collected feedback as an HTML table.
"""

import csv
import os
from typing import Literal

from fastapi import FastAPI
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

@app.post("/v1/feedback")
async def receive_feedback(fb: Feedback):
    """
    Save user feedback to a CSV file.

    Parameters
    ----------
    - fb: Feedback object containing question, answer, feedback type, and timestamp.

    Returns
    -------
    - A JSON response indicating successful storage.

    """
    file_exists = os.path.exists("feedback.csv")
    with open("feedback.csv", "a", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "feedback", "question", "answer"])
        writer.writerow([fb.timestamp, fb.feedback, fb.question, fb.answer])
    return {"message": "Feedback saved"}

@app.get("/v1/feedback/view", response_class=HTMLResponse)
async def view_feedback():
    """
    Render stored feedback as an HTML table.

    Returns:
    - An HTML page showing feedback in tabular format, or a message if no data exists.

    """
    if not os.path.exists("feedback.csv"):
        return "<h3>No feedback recorded yet.</h3>"

    html = ["<h2>Feedback Table</h2>", "<table border='1' cellpadding='5'>"]
    with open("feedback.csv", newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    for i, row in enumerate(rows):
        tag = "th" if i == 0 else "td"
        html.append("<tr>" + "".join(f"<{tag}>{cell}</{tag}>" for cell in row) + "</tr>")
    html.append("</table>")
    return "\n".join(html)

