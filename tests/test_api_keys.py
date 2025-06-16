
def test_api_key_env_var(r2r_container):
    exec_result = r2r_container.exec_run("env")
    env_vars = exec_result.output.decode()
    assert "API_KEY=" in env_vars, "La variable d'environnement API_KEY doit être définie dans le conteneur"
