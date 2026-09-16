
from src.api.domain_service import DomainService
from src.api.brand_detector import BrandDetector

class CoreRiskEngine:
    def __init__(self):
        self.brand_detector = BrandDetector()
        
    def evaluate(self, url: str, url_features: dict, page_features: dict) -> dict:
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
        
        
        # Domain Analysis
        domain_svc = DomainService()
        domain = domain_svc.extract_domain(url)
        domain_result = domain_svc.evaluate(domain)
        
        domain_score = domain_result.get("score", 0.0)
        reasons.extend(domain_result.get("reasons", []))
        
        if domain_result.get("known_malicious"):
            score = 100
        else:
            score += domain_score
            
        if domain_result.get("known_safe"):
            # Hardcap at 20 if domain is globally whitelisted
            score = min(score, 20)
            reasons.append("Domain is verified safe")


        # Brand Impersonation Analysis
        page_texts = str(page_features.get('title', '')) + " " + " ".join(page_features.get('button_labels', []))
        brand_result = self.brand_detector.detect(page_texts, domain)
        detected_brand = brand_result["detected_brand"]
        
        if brand_result["mismatch"]:
            score += brand_result["score"]
            reasons.append(brand_result["reason"])
        elif brand_result["score"] < 0:
            score += brand_result["score"] # reward
            reasons.append(brand_result["reason"])

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
            "detected_brand": detected_brand,
            "reasons": reasons,
            "modules": {
                "url": url_score / 40.0, # normalized 0-1
                "domain": domain_score / 50.0 if not domain_result.get("known_safe") else 0.0,
                "content": None,
                "vision": None
            }
        }
