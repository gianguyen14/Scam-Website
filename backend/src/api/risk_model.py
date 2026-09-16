
class CoreRiskEngine:
    def __init__(self):
        pass
        
    def evaluate(self, url_features: dict, page_features: dict) -> dict:
        score = 0.0
        reasons = []
        
        # 1. URL Analysis (Base 34 points max)
        url_score = 0.0
        if url_features.get('is_ip_address'): url_score += 34; reasons.append("Uses IP address instead of domain name")
        if url_features.get('has_punycode'): url_score += 20; reasons.append("Uses IDN/Punycode evasion")
        if url_features.get('suspicious_tld'): url_score += 15; reasons.append("Suspicious TLD")
        if url_features.get('has_shortener'): url_score += 15; reasons.append("URL shortener used")
        kw_hits = [k.replace('has_kw_', '') for k, v in url_features.items() if k.startswith('has_kw_') and v]
        if kw_hits: url_score += 10; reasons.append(f"Suspicious URL keywords: {','.join(kw_hits)}")
        
        if not url_features.get('has_https') and not url_features.get('is_ip_address'): 
            url_score += 10
            reasons.append("No HTTPS")
            
        url_score = min(url_score, 40.0)
        score += url_score
        
        # 2. DOM Analysis
        if page_features:
            dom_score = 0
            if page_features.get('has_password'):
                dom_score += 15
                reasons.append("Page requests password")
            if page_features.get('has_otp'):
                dom_score += 20
                reasons.append("Page requests OTP")
            if page_features.get('has_credit_card'):
                dom_score += 25
                reasons.append("Page requests Credit Card")
            if page_features.get('external_form_action'):
                dom_score += 15
                reasons.append("Form submits data to external domain")
            if page_features.get('hidden_iframe_count', 0) > 0:
                dom_score += 10
                reasons.append("Contains hidden iframes")
            
            score += min(dom_score, 60.0)

        # Level assignment
        risk_score = int(min(score, 100))
        
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
            "reasons": reasons,
            "modules": {
                "url": url_score / 40.0, # normalized 0-1
                "domain": None,
                "content": None,
                "vision": None
            }
        }
