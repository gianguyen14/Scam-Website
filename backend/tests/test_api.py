from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_scan_api_safe():
    payload = {
        "schema_version": 1,
        "url": "https://example.com",
        "page": {}
    }
    res = client.post("/api/v1/scan", json=payload)
    assert res.status_code == 200
    assert res.json()["level"] == "safe"

def test_scan_api_dangerous_dom():
    payload = {
        "schema_version": 1,
        "url": "http://192.168.1.1/update",
        "page": {
            "has_password": True,
            "has_otp": True,
            "external_form_action": True
        }
    }
    res = client.post("/api/v1/scan", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["risk_score"] >= 70
    assert data["level"] == "dangerous"
    assert "Page requests password" in data["reasons"]
