from fastapi import APIRouter
from src.schemas.models import ScanRequest, ScanResponse, ModulesResult
from src.api.url_detector import extract_url_features
from src.api.risk_model import CoreRiskEngine

router = APIRouter()
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
        detected_brand=None,
        reasons=result["reasons"],
        modules=ModulesResult(
            url=result["modules"]["url"],
            domain=result["modules"]["domain"],
            content=result["modules"]["content"],
            vision=result["modules"]["vision"]
        )
    )
