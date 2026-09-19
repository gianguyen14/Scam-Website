import os
import joblib
import pandas as pd
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
            df = pd.DataFrame([url_features])
            # align columns
            df = df.reindex(columns=self.url_features, fill_value=0)
            url_prob = self.url_model.predict_proba(df)[0][1]
            if url_prob > 0.5:
                # Add up to 35 points based on AI certainty
                url_score_val = url_prob * 35
                reasons.append(f"AI URL Pattern matches phishing ({int(url_prob*100)}% certainty)")
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
            
        if domain_result.get("known_safe"):
            score = min(score, 20)
            reasons.append("Domain is verified safe")
            
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
        dom_hash = page_features.get('dom_hash', '')
        brand_result = self.brand_detector.detect(page_texts, domain, dom_hash)
        detected_brand = brand_result["detected_brand"]
        
        if brand_result["mismatch"]:
            score += brand_result["score"]
            reasons.append(brand_result["reason"])
        elif brand_result["score"] < 0:
            score += brand_result["score"]

        # 5. Content NLP AI
        content_prob = self.content_ai.analyze(page_texts).get("scam_probability", 0.0)
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
            
        # --- Dynamic Risk Aggregation ---
        # 1. Amplification: If domain is extremely new/suspicious AND content NLP triggers urgency, multiply NLP score
        if domain_score > 20 and content_score > 10:
            amplified_penalty = content_score * 0.5 
            score += amplified_penalty
            reasons.append("Dynamic: Risk amplified due to combo of Suspicious Domain + Scam Content")

        # Compile level

        risk_score = int(min(max(score, 0), 100))
        
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
