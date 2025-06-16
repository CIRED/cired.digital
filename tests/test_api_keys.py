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

def test_api_key_env_var(r2r_container):
    exec_result = r2r_container.exec_run("env")
    env_vars = exec_result.output.decode()
    assert "API_KEY=" in env_vars, "La variable d'environnement API_KEY doit être définie dans le conteneur"
