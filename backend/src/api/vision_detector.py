from typing import Dict, Any

class VisionDetector:
    def __init__(self):
        pass
        
    def analyze(self, image_data: str) -> Dict[str, Any]:
        if not image_data:
            return {"brand_logo": None, "score": 0.0}
            
        # In a real model, run image processing here.
        # Mock logic: if we see 'vietcombank_logo' in base64 string...
        if 'vietcombank' in image_data.lower():
            return {"brand_logo": "Vietcombank", "score": 20.0}
            
        return {"brand_logo": None, "score": 0.0}
