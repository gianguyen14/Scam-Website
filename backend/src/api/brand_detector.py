import os
import json
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
                        
    def detect(self, text_signals: str, current_domain: str, dom_hash: str = None) -> Dict[str, Any]:
        text_signals = text_signals.lower()
        current_domain = current_domain.lower()
        
        for brand in self.brands:
            # Match via Advanced Vision (DOM Hash Clones)
            dom_hash_matched = False
            brand_dom_hashes = brand.get('known_dom_hashes', [])
            if dom_hash and dom_hash in brand_dom_hashes:
                dom_hash_matched = True

            # Match via Keywords
            keyword_matched = any(kw.lower() in text_signals for kw in brand.get('keywords', []))
            
            if keyword_matched or dom_hash_matched:
                official_domains = [d.lower() for d in brand.get('official_domains', [])]
                is_official = False
                for off_domain in official_domains:
                    if current_domain == off_domain or current_domain.endswith("." + off_domain):
                        is_official = True
                        break
                        
                if not is_official:
                    base_reason = f"Impersonating {brand['brand']} on unofficial domain."
                    if dom_hash_matched:
                        return {
                            "detected_brand": brand["brand"],
                            "mismatch": True,
                            "score": 60.0, # DOM Clones get FATAL penalty
                            "reason": f"[Advanced Vision] DOM Structure exact clone of {brand['brand']} detected on fake domain!"
                        }
                    else:
                        return {
                            "detected_brand": brand["brand"],
                            "mismatch": True,
                            "score": 40.0,
                            "reason": base_reason
                        }
                else:
                    return {
                        "detected_brand": brand["brand"],
                        "mismatch": False,
                        "score": -15.0, # Bonus for being official
                        "reason": f"Official {brand['brand']} domain"
                    }
                    
        return {"detected_brand": None, "mismatch": False, "score": 0.0, "reason": None}
