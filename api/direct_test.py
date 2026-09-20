
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

print("--- KIỂM TRA THỰC TẾ LUỒNG XỬ LÝ NỘI DUNG MỚI (CONTENT OVERHAUL) ---")

scenarios = [
    {
        "name": "Kịch bản 1: Lừa đảo Ví điện tử Crypto (Zero-Day Domain)",
        "url": "https://random-unknown-site.xyz/mint",
        "page": {
            "input_context": "Enter your 12 words secret recovery phrase",
            "visible_text": "Connect wallet to claim airdrop allocation",
            "has_password": False,
            "external_form_action": True
        }
    },
    {
        "name": "Kịch bản 2: Giả mạo Phạt Nguội Cơ Quan Nhà Nước",
        "url": "https://vnpay-thue.top/check",
        "page": {
            "visible_text": "Cổng thông tin Bộ Công An. Tra cứu phạt nguội vi phạm giao thông.",
            "input_context": "Nhập Biển số xe",
            "has_password": False
        }
    },
    {
        "name": "Kịch bản 3: Ăn cắp danh tính / Mã thẻ Ngân hàng",
        "url": "https://xacthuc-taikhoan.info/",
        "page": {
            "input_context": "Mã bảo mật CVV | Số thẻ",
            "visible_text": "Tài khoản bị khóa khẩn cấp do nghi ngờ. Vui lòng xác thực",
            "has_password": True
        }
    }
]

for s in scenarios:
    res = client.post("/api/v1/scan", json={"schema_version": 1, "url": s["url"], "page": s["page"]}).json()
    print(f"\n> {s['name']}")
    print(f"  Điểm rủi ro: {res['risk_score']}/100 - Cấp độ: {res['level'].upper()}")
    print("  Các lý do phát hiện:")
    for r in res['reasons']:
        print(f"   - {r}")
