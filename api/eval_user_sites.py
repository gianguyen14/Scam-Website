
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

print("--- EVALUATING USER SITES ---")

test_cases = [
    {"url": "https://33wins.icu/home", "title": "Game bài 33 Wins"},
    {"url": "https://apply-binance.hl.cn/auth", "title": "Binance Login"},
    {"url": "https://zaloweb.net/login", "title": "Đăng nhập Zalo"},
    {"url": "https://kiemtiennuoiem.click/join", "title": "Tuyển cộng tác viên chốt đơn hoa hồng cao"},
    {"url": "https://trungtambaohiemhanghoavietnampost.cc/tracking", "title": "Bảo hiểm hàng hóa Vietnampost"},
    {"url": "https://hust.edu.vn/", "title": "Bách Khoa Hà Nội"}
]

for tc in test_cases:
    payload = {"schema_version": 1, "url": tc["url"], "page": {"title": tc["title"]}}
    res = client.post("/api/v1/scan", json=payload).json()
    print(f"URL: {tc['url']}")
    print(f"  Score: {res.get('risk_score')} - Level: {res.get('level')}")
    print(f"  Reasons: {res.get('reasons')}")
    print("-" * 50)
