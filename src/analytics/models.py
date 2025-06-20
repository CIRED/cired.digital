"""
Pydantic models and data schema headers for analytics logging.

This module defines data models for session, request, article, response, and feedback logs,
as well as the expected CSV headers for each data type.
"""

from typing import Any, Literal

from pydantic import BaseModel


# Schémas Pydantic
class SessionLog(BaseModel):
    """Model for logging session information."""

    session_id: str
    start_time: str
    privacy_mode: bool = False


class RequestLog(BaseModel):
    """Model for logging user requests."""

    session_id: str
    query_id: str
    query: str
    config: dict[str, Any]
    request_body: dict[str, Any]
    timestamp: str
    privacy_mode: bool = False


class ArticleLog(BaseModel):
    """Model for logging articles shown to the user."""

    session_id: str
    query_id: str
    article: str
    timestamp: str
    privacy_mode: bool = False


class ResponseLog(BaseModel):
    """Model for logging responses to user queries."""

    session_id: str
    query_id: str
    response: dict[str, Any]
    processing_time: float
    timestamp: str
    privacy_mode: bool = False


class Feedback(BaseModel):
    """Model for logging user feedback on responses."""

    session_id: str
    query_id: str
    feedback: Literal["up", "down"]
    comment: str | None = None


# En-têtes attendus par fichier
DATA_MODEL_HEADERS: dict[str, list[str]] = {
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
