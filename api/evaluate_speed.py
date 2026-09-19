
import time
t0 = time.time()
def p(msg): print(f"{time.time()-t0:.2f}s - {msg}")

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))
os.environ["VERCEL_BUILD"] = "1"
os.environ["VERCEL"] = "1"

p("Importing CoreRiskEngine requirements")
import joblib
import pandas as pd
from src.api.domain_service import DomainService
from src.api.brand_detector import BrandDetector
from src.api.content_ai import ContentAI

p("Init DomainService")
domain_svc = DomainService()

p("Init BrandDetector")
brand_detector = BrandDetector()

p("Init ContentAI")
content_ai = ContentAI()

p("Load URL model joblib")
try:
    base_dir = os.path.dirname(os.path.dirname(__file__))
    url_model_path = os.path.join(base_dir, "backend/models/url_model.joblib")
    data = joblib.load(url_model_path)
except Exception as e:
    p(f"Joblib load error: {e}")

p("Done")
