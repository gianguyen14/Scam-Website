from typing import Dict, Any

# Mock model representation that uses heuristic based on features extracted
class URLRiskModel:
    def __init__(self):
        self.is_loaded = False
        
    def load(self, model_path: str):
        # We would load LightGBM/XGBoost here. 
        self.is_loaded = True
        return self
        
    def predict(self, features: dict) -> float:
        # Heuristic scoring to simulate model behavior
        score = 0.0
        
        # Base penalties
        if features.get('is_ip_address'): score += 40
        if features.get('has_punycode'): score += 30
        if features.get('suspicious_tld'): score += 20
        if features.get('has_shortener'): score += 15
        if not features.get('has_https'): score += 10
        
        # Length & complexity
        if features.get('url_length', 0) > 80: score += 5
        if features.get('num_subdomains', 0) > 2: score += 10
        if features.get('num_dots', 0) > 4: score += 10
        if features.get('digit_ratio', 0) > 0.2: score += 10
        
        # Keywords
        kw_hits = sum(1 for k, v in features.items() if k.startswith('has_kw_') and v)
        score += (kw_hits * 15)
        
        return min(max(score, 0.0), 100.0) / 100.0
