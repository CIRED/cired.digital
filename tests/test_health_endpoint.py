"""Tests for the /v3/health endpoint of the service."""

import requests


def test_health_endpoint(health_endpoint: str) -> None:
    """Test that the /v3/health endpoint returns status 200 and the expected JSON response."""
    response = requests.get(health_endpoint)
    assert response.status_code == 200
    assert response.json() == {"results": {"message": "ok"}}
