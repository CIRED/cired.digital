"""
Pydantic models and data schema headers for analytics logging.

This module defines data models for session, request, article, response, and feedback logs,
as well as the expected CSV headers for each data type.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel

# Schémas Pydantic


class MonitorEventType(str, Enum):
    """Enumeration of allowed event types for monitoring/logging analytics events."""

    SESSION_START = "sessionStart"
    REQUEST = "request"
    RESPONSE = "response"
    ARTICLE = "article"
    FEEDBACK = "feedback"
    USER_PROFILE = "userProfile"
    USER_INPUT = "userInput"
    VISIBILITY_CHANGE = "visibilityChange"


class MonitorEvent(BaseModel):
    """
    Pydantic model for a unified monitoring event sent from the frontend.

    Attributes
    ----------
    sessionId : str
        Sanitized session identifier.
    timestamp : str
        ISO-formatted timestamp (sanitized for filenames).
    data_type : MonitorEventType
        Type of event (enum).
    payload : dict[str, Any]
        Event-specific data.

    """

    sessionId: str
    timestamp: str
    eventType: MonitorEventType
    payload: dict[str, Any]
