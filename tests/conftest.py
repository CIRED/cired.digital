"""Pytest configuration and fixtures for Docker-based integration tests."""

import pytest
from docker import from_env
from docker.models.containers import Container

pytest_plugins = ["tests.smoke.helpers"]


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
