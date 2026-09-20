
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

print("--- KIỂM TRA CÁC KỊCH BẢN TẤN CÔNG DỊ BIỆT (KHÁC TRUYỀN THỐNG) ---")

scenarios = [
    {
        "name": "Kịch bản 4: Homoglyph Attack (Ký tự giả lập Punycode)",
        "url": "https://xn--viettm-b4a.tech/login", # Domain thực ra là việttm.tech nhưng dùng ký tự unicode để đánh lừa mắt
        "page": {
            "visible_text": "Cổng đăng nhập an toàn.",
            "has_password": True
        }
    },
    {
        "name": "Kịch bản 5: Lùa Gà Đầu Tư Thời Đại Mới (Sàn BO/Trade/Chứng Khoán Ảo)",
        "url": "https://trade-x2-profit.finance/",
        "page": {
            "visible_text": "Sàn giao dịch nhị phân lớn nhất. Cam kết lợi nhuận 30%/tháng. Có chuyên gia đọc lệnh và chính sách bảo hiểm vốn 100%.",
            "has_password": False
        }
    },
    {
        "name": "Kịch bản 6: Tặng quà Tri ân giả mạo Shopee/Tiki",
        "url": "https://quatang-shopee-vn.vercel.app/nhan-thuong",
        "page": {
            "visible_text": "Chúc mừng bạn đã trúng thưởng chương trình tri ân khách hàng Shopee.",
            "input_context": "Vui lòng nhập tên và Số tài khoản ATM để nhận tiền thưởng"
        }
    }
]

for s in scenarios:
    res = client.post("/api/v1/scan", json={"schema_version": 1, "url": s["url"], "page": s["page"]}).json()
    print(f"\n> {s['name']}")
    print(f"  URL: {s['url']}")
    print(f"  Điểm rủi ro: {res['risk_score']}/100 - Cấp độ: {res['level'].upper()}")
    print("  Các lý do phát hiện:")
    for r in res['reasons']:
        print(f"   - {r}")
