import os
import io
import base64
import torch
import torch.nn.functional as F
import torchvision.transforms as transforms
import torchvision.models as models
from PIL import Image
import json
from typing import Dict, Any

class AdvancedVisionAI:
    def __init__(self, registry_path="data/brand_registry"):
        self.device = torch.device("cpu")
        print("Loading MobileNetV3 CNN for Visual Similarity...")
        # Use MobileNetV3 Small as it is very lightweight
        # In production it downloads weights once and caches them.
        self.model = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
        self.model.eval() # Inference mode
        self.model.to(self.device)
        
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        
        # Load official brand visual embeddings
        self.brand_embeddings = {}
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        full_path = os.path.join(base_dir, registry_path)
        
        if os.path.exists(full_path):
            for file in os.listdir(full_path):
                if file.endswith('.json'):
                    with open(os.path.join(full_path, file), 'r') as f:
                        brand_data = json.load(f)
                        # Expecting {'brand': '...', 'cnn_embedding': [0.1, 0.2, ...]}
                        if 'cnn_embedding' in brand_data:
                            # Convert list to tensor
                            tensor_emb = torch.tensor(brand_data['cnn_embedding']).to(self.device)
                            self.brand_embeddings[brand_data['brand']] = {
                                'tensor': tensor_emb,
                                'domains': brand_data.get('official_domains', [])
                            }

    def decode_image(self, b64_str: str) -> Image.Image:
        if b64_str.startswith("data:image"):
            b64_str = b64_str.split(",")[1]
        img_bytes = base64.b64decode(b64_str)
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        return img

    def get_embedding(self, img: Image.Image) -> torch.Tensor:
        tensor_img = self.transform(img).unsqueeze(0).to(self.device)
        with torch.no_grad():
            emb = self.model(tensor_img)
        # Normalize the embedding vector for cosine similarity
        return F.normalize(emb, p=2, dim=1)

    def analyze(self, screenshot_b64: str, current_domain: str) -> Dict[str, Any]:
        if not screenshot_b64:
            return {"score": 0.0, "reason": None}

        try:
            img = self.decode_image(screenshot_b64)
            current_emb = self.get_embedding(img)
            
            # Compare with all registered brands
            max_sim = -1.0
            matched_brand = None
            official_domains = []
            
            for brand, data in self.brand_embeddings.items():
                ref_emb = data['tensor']
                # Cosine similarity
                sim = torch.mm(current_emb, ref_emb.T).item()
                if sim > max_sim:
                    max_sim = sim
                    matched_brand = brand
                    official_domains = data['domains']
                    
            # Threshold for deep visual clone
            if max_sim > 0.88: # 88% visual similarity
                # Check domain
                current_domain = current_domain.lower()
                is_official = False
                for off_domain in official_domains:
                    if current_domain == off_domain or current_domain.endswith("." + off_domain):
                        is_official = True
                        break
                        
                if not is_official:
                    return {
                        "score": 85.0, # Fatal Risk
                        "reason": f"[Deep Vision CNN] Xác định giao diện {matched_brand} (Độ giống {int(max_sim*100)}%) trên tên miền giả mạo!"
                    }
                else:
                    return {"score": -10.0, "reason": f"Giao diện chuẩn hãng."}
            
            return {"score": 0.0, "reason": None}
            
        except Exception as e:
            print("Vision Error:", e)
            return {"score": 0.0, "reason": f"Lỗi phân tích hình ảnh: {str(e)}"}
