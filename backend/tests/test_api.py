from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}

def test_scan_api_safe():
    payload = {
        "schema_version": 1,
        "url": "https://example.com/login",
        "page": {}
    }
    res = client.post("/api/v1/scan", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["schema_version"] == 1
    assert data["level"] in ["safe", "suspicious"]

def test_scan_api_dangerous():
    payload = {
        "schema_version": 1,
        "url": "http://192.168.1.1/login/verify/update",
        "page": {}
    }
    res = client.post("/api/v1/scan", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["risk_score"] >= 70
    assert data["level"] == "dangerous"
    assert "Uses IP address instead of domain name" in data["reasons"]
