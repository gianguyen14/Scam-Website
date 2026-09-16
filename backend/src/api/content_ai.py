from typing import Dict, Any

class ContentAI:
    def __init__(self):
        # Heuristic keywords for mock classification
        self.urgency_kws = ["khẩn cấp", "ngay lập tức", "khóa tài khoản", "tạm ngưng", "urgent", "suspend", "immediately", "24h"]
        self.financial_kws = ["nhận thưởng", "chuyển khoản", "trúng giải", "nạp tiền", "rút tiền", "crypto", "bitcoin", "investment"]
        self.credential_kws = ["mật khẩu", "đăng nhập", "xác thực", "otp", "password", "verify", "login"]
        
    def analyze(self, text: str) -> Dict[str, float]:
        text = text.lower()
        
        def calculate_score(kws):
            matches = sum(1 for k in kws if k in text)
            return min(matches * 0.35, 1.0)
            
        return {
            "urgency": calculate_score(self.urgency_kws),
            "financial_scam": calculate_score(self.financial_kws),
            "credential_request": calculate_score(self.credential_kws)
        }
