from fastapi.testclient import TestClient

from porra_api.main import app


def test_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version_default():
    client = TestClient(app)
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "0.1.0"
    assert data["environment"] == "development"


def test_version_from_env(monkeypatch):

    monkeypatch.setenv("PORRA_ENVIRONMENT", "test")

    client = TestClient(app)
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "0.1.0"
    assert data["environment"] == "test"
