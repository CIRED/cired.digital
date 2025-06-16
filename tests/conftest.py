import pytest
import docker

@pytest.fixture(scope="session")
def docker_client():
    return docker.from_env()

@pytest.fixture(scope="session")
def r2r_container(docker_client):
    container_name = "cidir2r-r2r-1"
    try:
        return docker_client.containers.get(container_name)
    except Exception:
        pytest.skip(f"Container {container_name} non trouvé ou non démarré")
