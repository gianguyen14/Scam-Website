from fastapi import APIRouter
from src.schemas.models import ScanRequest, ScanResponse, ModulesResult
from src.api.url_detector import extract_url_features
from src.api.risk_model import URLRiskModel

router = APIRouter()
model = URLRiskModel()

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.post("/api/v1/scan", response_model=ScanResponse)
def scan_url(request: ScanRequest):
    # Extract features
    features = extract_url_features(request.url)
    
    # Predict score using model (heuristic for now)
    url_score_raw = model.predict(features)
    
    # Convert to 0-100 range
    risk_score = int(url_score_raw * 100)
    
    # Determine level and explanation
    reasons = []
    if features.get('is_ip_address'): reasons.append("Uses IP address instead of domain name")
    if features.get('has_punycode'): reasons.append("Uses IDN/Punycode evasion")
    if features.get('suspicious_tld'): reasons.append("Uses suspicious Top Level Domain")
    if features.get('has_shortener'): reasons.append("Uses URL shortener")
    kw_hits = [k.replace('has_kw_', '') for k, v in features.items() if k.startswith('has_kw_') and v]
    if kw_hits: reasons.append(f"Contains suspicious keywords: {', '.join(kw_hits)}")
    if features.get('num_subdomains', 0) > 2: reasons.append("Has unusual number of subdomains")
    
    if risk_score >= 70:
        level = "dangerous"
    elif risk_score >= 30:
        level = "suspicious"
    else:
        level = "safe"
        
    if not reasons and risk_score < 30:
        reasons.append("No suspicious URL patterns detected")

    return ScanResponse(
        schema_version=1,
        risk_score=risk_score,
        level=level,
        confidence=0.85,
        detected_brand=None,
        reasons=reasons,
        modules=ModulesResult(
            url=round(url_score_raw, 2),
            domain=None,
            content=None,
            vision=None
        )
    )
