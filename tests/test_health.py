from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)

def test_health_check_returns_healthy_status():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "zypharion-api"
    assert response.json()["version"] == "0.1.0"

def test_root_returns_welcome_message():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "running"
    assert "Zypharion" in response.json()["message"]