import os
import joblib
from typing import Dict, Any
from src.api.domain_service import DomainService
from src.api.brand_detector import BrandDetector
from src.api.content_ai import ContentAI
from src.api.vision_heuristic import VisionHeuristic

class CoreRiskEngine:
    def __init__(self):
        self.brand_detector = BrandDetector()
        self.content_ai = ContentAI()
        self.vision_heuristic = VisionHeuristic()
        
        # Load URL AI Model
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        url_model_path = os.path.join(base_dir, "models/url_model.joblib")
        try:
            data = joblib.load(url_model_path)
            self.url_model = data["model"]
            self.url_features = data["features"]
            self.url_ai_loaded = True
        except:
            self.url_ai_loaded = False
        
    def evaluate(self, url: str, url_features: dict, page_features: dict) -> dict:
        score = 0.0
        reasons = []
        
        
        # 1. URL Analysis (AI Powered)
        url_score_val = 0.0
        if self.url_ai_loaded:
            # Pure python feature alignment instead of pandas
            row = []
            for col in self.url_features:
                row.append(url_features.get(col, 0))
            
            try:
                url_prob = self.url_model.predict_proba([row])[0][1]
                if url_prob > 0.5:
                    url_score_val = url_prob * 35
                    reasons.append(f"AI URL Pattern matches phishing ({int(url_prob*100)}% certainty)")
            except Exception as e:
                print("URL Model Error:", e)
            score += url_score_val

        
        # 2. Domain Analysis
        domain_svc = DomainService()
        domain = domain_svc.extract_domain(url)
        domain_result = domain_svc.evaluate(domain)
        
        domain_score = domain_result.get("score", 0.0)
        reasons.extend(domain_result.get("reasons", []))
        
        if domain_result.get("known_malicious"):
            score = 100
        else:
            score += domain_score
            

            
        # 3. DOM Metadata Rules (Privacy Safe)
        if page_features:
            dom_score = 0
            if page_features.get('has_password'): dom_score += 15; reasons.append("Page requests password")
            if page_features.get('has_otp'): dom_score += 20; reasons.append("Page requests OTP")
            if page_features.get('has_credit_card'): dom_score += 25; reasons.append("Page requests Credit Card")
            if page_features.get('external_form_action'): dom_score += 15; reasons.append("Form submits data to external domain")
            if page_features.get('hidden_iframe_count', 0) > 0: dom_score += 10; reasons.append("Contains hidden iframes")
            score += min(dom_score, 60.0)

        # 4. Brand Impersonation Analysis
        page_texts = str(page_features.get('title', '')) + " " + " ".join(page_features.get('button_labels', []))
        dom_sequence = page_features.get('dom_sequence', '')
        brand_result = self.brand_detector.detect(page_texts, domain, dom_sequence)
        detected_brand = brand_result["detected_brand"]
        
        if brand_result["mismatch"]:
            score += brand_result["score"]
            reasons.append(brand_result["reason"])
        elif brand_result["score"] < 0:
            score += brand_result["score"]

        # 5. Content NLP AI
        nlp_payload = page_texts + ' ' + page_features.get('visible_text', '')
        content_prob = self.content_ai.analyze(nlp_payload).get("scam_probability", 0.0)
        content_score = 0.0
        if content_prob >= 0.30:
            content_score = content_prob * 20
            score += content_score
            reasons.append(f"AI Content NLP detected scam language ({int(content_prob*100)}% certainty)")

        # 6. Vision AI (Deferred/Mock)
        vision_score = 0.0
        if 'screenshot' in page_features and page_features['screenshot']:
            vision_result = self.vision_heuristic.analyze(page_features['screenshot'])
            vision_score = vision_result["score"]
            if vision_score > 0:
                score += vision_score
                reasons.append(f"Visual identity impersonates {vision_result['brand_logo']}")


        # --- Behavioral Analysis ---
        behavior = page_features.get('behavior', {})
        if behavior.get('pasteInSensitiveField'):
            score += 20
            reasons.append("Behavior: Suspicious fast-paste in sensitive field")
        if behavior.get('rapidScroll'):
            score += 5
            

        # --- Web3/Crypto Wallet Scanning ---
        crypto_wallets = page_features.get('crypto_wallets', [])
        if len(crypto_wallets) > 0:
            score += 15
            reasons.append(f"Contains {len(crypto_wallets)} embedded web3 smart contracts/wallets (High risk element)")
            # In production, cross-reference these addresses with ScamSniffer contract database
        
        # --- Dynamic Risk Aggregation ---

        # 1. Amplification: If domain is extremely new/suspicious AND content NLP triggers urgency, multiply NLP score
        if domain_score > 20 and content_score > 10:
            amplified_penalty = content_score * 0.5 
            score += amplified_penalty
            reasons.append("Dynamic: Risk amplified due to combo of Suspicious Domain + Scam Content")

        
        # --- 6. Explicit Heuristics: Gambling, Betting & Task Scams (Nhiệm vụ đơn ảo) ---
        page_text_lower = nlp_payload.lower()
        input_context_lower = page_features.get('input_context', '').lower()
        
        # --- Đại tu hệ thống Content Heuristics (Song ngữ Anh - Việt) ---
        # 1. Bank/Enterprise Impersonation & Fake Urgency
        urgency_kws = ["khóa khẩn cấp", "tạm ngưng", "xác thực danh tính", "tài khoản bị khóa", 
                       "unusual login activity", "account suspended", "verify identity", "security alert"]
        matched_urgency = [kw for kw in urgency_kws if kw in page_text_lower]
        if len(matched_urgency) > 0:
            score += 20
            reasons.append(f"Ngôn ngữ thúc ép/đe dọa thường thấy ở Phishing: '{matched_urgency[0]}'")

        # 2. Fake Authorities (Giả danh cơ quan chức năng VN)
        authority_kws = ["bộ công an", "phạt nguội", "cục cảnh sát giao thông", "thanh tra chính phủ", "chống rửa tiền"]
        matched_auth = [kw for kw in authority_kws if kw in page_text_lower]
        if len(matched_auth) > 0 and not domain_result.get('known_safe'):
            score += 45
            reasons.append(f"Giả mạo cơ quan chức năng / Chính phủ: '{matched_auth[0]}'")

        # 3. Web3 / Crypto Drainers (Lừa đảo hốt ví tiền ảo)
        crypto_scam_kws = ["seed phrase", "secret recovery phrase", "12 words", "connect wallet to claim", 
                           "airdrop allocation", "validate your wallet", "keystore json"]
        matched_crypto = [kw for kw in crypto_scam_kws if kw in page_text_lower or kw in input_context_lower]
        if len(matched_crypto) > 0:
            score += 55
            reasons.append(f"Lừa đảo tiền mã hóa (Web3 Drainer): Đòi hỏi thông tin '{matched_crypto[0]}'")

        # 4. Identity Theft Input Context (Đánh hơi bối cảnh nhập liệu)
        sensitive_inputs = ["cccd", "cmnd", "số thẻ", "mã bảo mật cvv", "mã otp", "recovery phrase", "ssn", "social security"]
        matched_inputs = [kw for kw in sensitive_inputs if kw in input_context_lower]
        if len(matched_inputs) > 0 and not domain_result.get('known_safe'):
            score += 40
            reasons.append(f"Thu thập dữ liệu nhạy cảm trái phép: Bắt nhập '{matched_inputs[0]}' trên website lạ.")

        # --- 6. Explicit Heuristics: Gambling, Betting & Task Scams (Nhiệm vụ đơn ảo) ---
        gambling_kws = ["tài xỉu", "nổ hũ", "cá cược", "đá gà", "casino", "đánh bài", "nhà cái", "thể thao ảo", "lô đề"]
        matched_gambling = [kw for kw in gambling_kws if kw in page_text_lower]
        if len(matched_gambling) > 0:
            score += 45
            reasons.append(f"Chứa từ khóa cờ bạc/cá cược bất hợp pháp: {', '.join(matched_gambling)}")

        task_scam_kws = ["tuyển cộng tác viên", "chốt đơn", "nhiệm vụ hoàn tiền", "hoa hồng cao", "việc nhẹ lương cao", "thanh toán đơn hàng", "tuyển đại lý", "hoa hồng đại lý"]
        matched_tasks = [kw for kw in task_scam_kws if kw in page_text_lower]
        if len(matched_tasks) > 0:
            score += 40
            reasons.append(f"Dấu hiệu Lừa đảo làm nhiệm vụ/CTV ảo: {', '.join(matched_tasks)}")

        
        # --- 8. URL Threat Keywords Bumping ---
        url_lower = url.lower()
        betting_url_kws = ["bet", "win", "slot", "casino", "go88", "hitclub", "sunwin", "88"]
        if any(kw in url_lower for kw in betting_url_kws) and domain_score > 20: 
            # If it has a bad TLD AND betting keywords in URL, auto dangerous
            score += 40
            reasons.append("Tên miền chứa từ khóa cờ bạc kết hợp với TLD rủi ro cao.")
            
        
        # --- 9. TỐI ĐA HÓA ĐỘ CHÍNH XÁC (Accuracy Maximizer Combo) ---
        # Bắt triệt để: Tên miền lạ (domain_score > 0) + Yêu cầu thông tin nhạy cảm + Có gửi dữ liệu ra ngoài
        if not domain_result.get("known_safe"):
            if page_features.get('has_password') and page_features.get('external_form_action'):
                score += 35
                reasons.append("Hành vi nguy hiểm: Thu thập mật khẩu và gửi sang máy chủ bên ngoài (Cross-Origin Action).")
                
            # Đòi hỏi Credit Card trên web không uy tín -> Auto Dangerous
            if page_features.get('has_credit_card') and domain_score > 15:
                score += 50
                reasons.append("Gian lận tín dụng: Yêu cầu thẻ tín dụng trên tên miền không đủ độ tin cậy.")

        # Compile level
        risk_score = int(min(max(score, 0), 100))
        
        # --- 7. Global Whitelist Override ---
        # Áp dụng Whitelist ở bước CHÓT để xóa sạch án oan cho các trang chính thống (như ChatGPT có form đăng nhập)
        if domain_result.get("known_safe"):
            risk_score = 0
            level = "safe"
            reasons = ["Tên miền chính thống, được xác minh an toàn 100% (Global Whitelist)."]
        else:
            if risk_score >= 70:
                level = "dangerous"
            elif risk_score >= 30:
                level = "suspicious"
            else:
                level = "safe"
                
            if not reasons and risk_score < 30:
                reasons.append("No suspicious patterns detected")
        return {
            "score": risk_score,
            "level": level,
            "detected_brand": detected_brand,
            "reasons": reasons,
            "modules": {
                "url": url_score_val / 35.0 if url_score_val > 0 else 0.0,
                "domain": domain_score / 50.0 if not domain_result.get("known_safe") else 0.0,
                "content": content_score / 20.0 if content_score > 0 else 0.0,
                "vision": vision_score / 20.0 if 'screenshot' in page_features else None
            }
        }
