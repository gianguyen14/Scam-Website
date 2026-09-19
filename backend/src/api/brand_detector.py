import os
import json
from difflib import SequenceMatcher
from typing import Dict, Any

class BrandDetector:
    def __init__(self, registry_path="data/brand_registry"):
        self.brands = []
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        full_path = os.path.join(base_dir, registry_path)
        
        if os.path.exists(full_path):
            for file in os.listdir(full_path):
                if file.endswith('.json'):
                    with open(os.path.join(full_path, file), 'r') as f:
                        self.brands.append(json.load(f))
                        
    def detect(self, text_signals: str, current_domain: str, dom_sequence: str = None) -> Dict[str, Any]:
        text_signals = text_signals.lower()
        current_domain = current_domain.lower()
        
        for brand in self.brands:
            # 1. FUZZY DOM STRUCTURAL MATCHING (Advanced Vision)
            # Thay vì hash cứng bằng FNV-1a (dễ bị bypass nếu hacker thêm 1 thẻ <div>),
            # chúng ta so sánh độ tương đồng chuỗi cấu trúc HTML (Levenshtein Distance)
            dom_hash_matched = False
            sim_score = 0.0
            if dom_sequence:
                for known_seq in brand.get('known_dom_sequences', []):
                    # So sánh độ giống nhau của cấu trúc UI
                    sim_score = SequenceMatcher(None, dom_sequence, known_seq).ratio()
                    if sim_score > 0.85: # Chỉ cần giống 85% cấu trúc
                        dom_hash_matched = True
                        break

            # 2. KEYWORD MATCHING
            keyword_matched = any(kw.lower() in text_signals for kw in brand.get('keywords', []))
            
            if keyword_matched or dom_hash_matched:
                official_domains = [d.lower() for d in brand.get('official_domains', [])]
                is_official = False
                for off_domain in official_domains:
                    if current_domain == off_domain or current_domain.endswith("." + off_domain):
                        is_official = True
                        break
                        
                if not is_official:
                    if dom_hash_matched:
                        return {
                            "detected_brand": brand["brand"],
                            "mismatch": True,
                            "score": 75.0, # Clone giao diện => Trực tiếp kết án tử hình
                            "reason": f"[Advanced Vision] Giao diện giống {brand['brand']} đến {int(sim_score*100)}% nhưng khác tên miền gốc!"
                        }
                    else:
                        return {
                            "detected_brand": brand["brand"],
                            "mismatch": True,
                            "score": 75.0, # Nâng mức phạt cho giả mạo thương hiệu lên tử hình
                            "reason": f"Dùng nội dung/tên thương hiệu {brand['brand']} trên tên miền lạ."
                        }
                else:
                    return {
                        "detected_brand": brand["brand"],
                        "mismatch": False,
                        "score": -15.0, # Điểm cộng an toàn cho Doamin chính hãng
                        "reason": f"Tên miền gốc chuẩn của {brand['brand']}."
                    }
                    
        return {"detected_brand": None, "mismatch": False, "score": 0.0, "reason": None}
