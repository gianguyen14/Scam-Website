import os
import sqlite3
from src.schemas.models import ScamReport
from fastapi import APIRouter
from src.schemas.models import ScanRequest, ScanResponse, ModulesResult, ScamReport, VisionRequest
from src.api.vision_ai import AdvancedVisionAI

from src.api.risk_model import CoreRiskEngine
from src.api.url_detector import extract_url_features
from src.schemas.models import ModulesResult, ScanRequest, ScanResponse

router = APIRouter()
vision_agent = AdvancedVisionAI()
engine = CoreRiskEngine()

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.post("/api/v1/scan", response_model=ScanResponse)
def scan_url(request: ScanRequest):
    url_features = extract_url_features(request.url)
    page_features = request.page or {}
    
    result = engine.evaluate(request.url, url_features, page_features)
    
    return ScanResponse(
        schema_version=1,
        risk_score=result["score"],
        level=result["level"],
        confidence=0.85,
        detected_brand=result.get("detected_brand"),
        reasons=result["reasons"],
        modules=ModulesResult(
            url=result["modules"]["url"],
            domain=result["modules"]["domain"],
            content=result["modules"]["content"],
            vision=result["modules"]["vision"]
        )
    )


@router.post("/api/v1/report")
def report_scam(report: ScamReport):
    # Tích hợp Community Database Pattern (Lấy cảm hứng từ Dollar-Scholars/scams-database)
    db_path = os.path.join(os.path.dirname(__file__), "../../data/community_scams.sqlite3")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS scams
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT, amount REAL, currency TEXT, 
                      platform TEXT, desc TEXT, scammer TEXT, phishing BOOLEAN)''')
    
    cursor.execute('''INSERT INTO scams (url, amount, currency, platform, desc, scammer, phishing) 
                      VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                   (report.url_or_contact, report.amount_lost, report.currency, report.platform, 
                    report.description, report.scammer_name, report.phishing))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Report logged into community database."}


@router.post("/api/v1/scan/vision")
def scan_vision(req: VisionRequest):
    import urllib.parse
    domain = ""
    try:
        domain = urllib.parse.urlparse(req.url).hostname or ""
    except: pass
    
    result = vision_agent.analyze(req.screenshot, domain)
    level = "safe"
    if result["score"] >= 70:
        level = "dangerous"
    elif result["score"] > 30:
        level = "suspicious"
        
    return {
        "status": "success",
        "risk_score": int(result["score"]),
        "level": level,
        "reason": result["reason"]
    }
