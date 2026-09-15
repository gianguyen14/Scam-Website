from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any

class PageData(BaseModel):
    pass

class ModulesResult(BaseModel):
    url: Optional[float] = None
    domain: Optional[float] = None
    content: Optional[float] = None
    vision: Optional[float] = None

class ScanRequest(BaseModel):
    schema_version: int = 1
    url: str
    page: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ScanResponse(BaseModel):
    schema_version: int = 1
    risk_score: int
    level: str
    confidence: float
    detected_brand: Optional[str] = None
    reasons: List[str] = Field(default_factory=list)
    modules: ModulesResult
