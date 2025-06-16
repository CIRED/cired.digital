
def test_container_logs_no_error_warning(r2r_container):
    logs = r2r_container.logs().decode('utf-8', errors='replace')
    # Ignore known benign heartbeat errors
    error_lines = [
        line for line in logs.splitlines()
        if "ERROR" in line and "heartbeat" not in line.lower()
    ]
    warning_lines = [line for line in logs.splitlines() if "WARNING" in line]
    assert not error_lines, f"Des erreurs inattendues ont été trouvées dans les logs du conteneur: {error_lines}"
    assert not warning_lines, f"Des messages 'WARNING' ont été trouvés dans les logs du conteneur: {warning_lines}"
