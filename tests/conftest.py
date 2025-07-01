"""Pytest configuration and fixtures for Docker-based integration tests."""

import os

import pytest
from docker import from_env
from docker.models.containers import Container

pytest_plugins = ["tests.smoke.helpers"]


@pytest.fixture(scope="session")
def server_url() -> str:
    """
    Provide the server URL based on the ENVIRONMENT variable.

    Returns:
        str: The base server URL for API calls.

    """
    environment = os.environ.get("ENVIRONMENT", "dev")

    if environment == "production":
        return "http://r2r-api.cired.digital"
    else:
        # dev or any other environment defaults to localhost
        return os.environ.get("SERVER_URL", "http://localhost:7272")


@pytest.fixture(scope="session")
def health_endpoint(server_url: str) -> str:
    """
    Provide the health endpoint URL.

    Args:
        server_url: The base server URL fixture.

    Returns:
        str: The complete health endpoint URL.

    """
    return f"{server_url}/v3/health"


@pytest.fixture(scope="session")
def r2r_container() -> Container:
    """
    Provide the R2R Docker container for testing.

    Returns:
        Container: The R2R Docker container instance.

    Skips the test if the container is not found or not running.

    """
    container_name = "cidir2r-r2r-1"
    try:
        return from_env().containers.get(container_name)
    except Exception:
        pytest.skip(f"Container {container_name} non trouvé ou non démarré")
