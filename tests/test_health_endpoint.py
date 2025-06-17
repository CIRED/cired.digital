"""Tests for the /v3/health endpoint of the local service."""

import requests


def test_health_endpoint() -> None:
    """Test that the /v3/health endpoint returns status 200 and the expected JSON response."""
    response = requests.get("http://localhost:7272/v3/health")
    assert response.status_code == 200
    assert response.json() == {"results": {"message": "ok"}}
