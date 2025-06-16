"""Tests for presence, non-emptiness, masking, and case sensitivity of API environment variables in the container."""

from typing import Any

API_ENV_VARS = [
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "MISTRAL_API_KEY",
    "DEEPSEEK_API_KEY",
    "OLLAMA_API_BASE",
]


def test_api_env_vars_present(r2r_container: Any) -> None:
    """Test that all required API environment variables are present in the container."""
    exec_result = r2r_container.exec_run("env")
    env_vars = exec_result.output.decode()
    for var in API_ENV_VARS:
        assert f"{var}=" in env_vars, (
            f"La variable d'environnement {var} doit être définie dans le conteneur"
        )


def test_api_env_vars_not_empty(r2r_container: Any) -> None:
    """Test that API environment variables are not empty."""
    exec_result = r2r_container.exec_run("env")
    env_vars = exec_result.output.decode()
    for var in API_ENV_VARS:
        line = next(
            (line for line in env_vars.splitlines() if line.startswith(f"{var}=")), None
        )
        assert line is not None, (
            f"{var} doit être présent dans les variables d'environnement"
        )
        value = line.split("=", 1)[1]
        assert value.strip() != "", f"{var} ne doit pas être vide"


def test_api_env_vars_masked_in_logs(r2r_container: Any) -> None:
    """Test that API environment variables do not appear in logs."""
    # Suppose logs are available at /var/log/app.log in the container
    exec_result = r2r_container.exec_run("cat /var/log/app.log")
    logs = exec_result.output.decode()
    for var in API_ENV_VARS:
        assert f"{var}=" not in logs, (
            f"{var} ne doit pas apparaître en clair dans les logs"
        )


def test_api_env_vars_case_sensitive(r2r_container: Any) -> None:
    """Test that API environment variables are case sensitive."""
    exec_result = r2r_container.exec_run("env")
    env_vars = exec_result.output.decode()
    for var in API_ENV_VARS:
        lower_var = var.lower()
        assert f"{lower_var}=" not in env_vars, (
            f"La variable d'environnement doit être sensible à la casse ({var})"
        )
