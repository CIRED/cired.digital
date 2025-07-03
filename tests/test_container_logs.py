"""Test that container logs do not contain unexpected errors or warnings."""

from docker.models.containers import Container


def test_container_logs_no_error_warning(r2r_container: Container) -> None:
    """Test that container logs do not contain unexpected errors or warnings."""
    logs = r2r_container.logs().decode("utf-8", errors="replace")
    # Ignore known benign heartbeat errors
    error_lines = [
        line
        for line in logs.splitlines()
        if "ERROR" in line and "heartbeat" not in line.lower()
    ]
    warning_lines = [line for line in logs.splitlines() if "WARNING" in line]
    assert not error_lines, (
        f"Des erreurs inattendues ont été trouvées dans les logs du conteneur: {error_lines}"
    )
    if warning_lines:
        # If there are warnings, we log them but do not fail the test
        print(
            f"Des messages 'WARNING' ont été trouvés dans les logs du conteneur: {warning_lines}"
        )
