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

def test_container_logs_no_error_warning(r2r_container):
    logs = r2r_container.logs().decode('utf-8', errors='replace')
    assert "ERROR" not in logs, "Des messages 'ERROR' ont été trouvés dans les logs du conteneur"
    assert "WARNING" not in logs, "Des messages 'WARNING' ont été trouvés dans les logs du conteneur"
