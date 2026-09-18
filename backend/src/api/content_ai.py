import os
import joblib
from typing import Dict, Any

class ContentAI:
    def __init__(self, model_path="models/content_nlp_model.joblib"):
        self.is_loaded = False
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        full_path = os.path.join(base_dir, model_path)
        
        try:
            self.model = joblib.load(full_path)
            self.is_loaded = True
        except Exception as e:
            self.model = None
            print(f"Content AI load error: {e}")

    def analyze(self, text: str) -> Dict[str, float]:
        if not text or not self.is_loaded:
            return {"scam_probability": 0.0}
            
        # Predict probability of being phishing (class 1)
        try:
            prob = self.model.predict_proba([text])[0][1]
            return {"scam_probability": float(prob)}
        except:
            return {"scam_probability": 0.0}
