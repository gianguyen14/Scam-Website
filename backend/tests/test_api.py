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

def test_scan_api_domain_impersonation():
    payload = {
        "schema_version": 1,
        "url": "http://vietcombank-login.xyz/auth",
        "page": {
            "title": "Vietcombank Portal",
            "has_password": True
        }
    }
    res = client.post("/api/v1/scan", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["level"] == "dangerous"
    assert data["detected_brand"] == "Vietcombank"
    assert "Impersonating Vietcombank on unofficial domain" in data["reasons"]

def test_scan_api_content_urgency():
    payload = {
        "schema_version": 1,
        "url": "https://unknown-domain.com",
        "page": {
            "title": "Tài khoản của bạn sẽ bị tạm ngưng khẩn cấp trong 24h",
            "has_password": True
        }
    }
    res = client.post("/api/v1/scan", json=payload)
    assert res.status_code == 200
    data = res.json()
    # High urgency keyword + password request on unknown domain -> likely dangerous or suspicious
    assert data["risk_score"] >= 25
    assert any("AI Content NLP" in r or "High urgency" in r for r in data["reasons"])
