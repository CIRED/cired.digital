import requests

def test_health_endpoint():
    response = requests.get("http://localhost:7272/v3/health")
    assert response.status_code == 200
    assert response.json() == {"results": {"message": "ok"}}
