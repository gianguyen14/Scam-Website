from typing import Any

from pydantic import BaseModel, Field


class PageData(BaseModel):
    pass

class ModulesResult(BaseModel):
    url: float | None = None
    domain: float | None = None
    content: float | None = None
    vision: float | None = None

class ScanRequest(BaseModel):
    schema_version: int = 1
    url: str
    page: dict[str, Any] | None = Field(default_factory=dict)

class ScanResponse(BaseModel):
    schema_version: int = 1
    risk_score: int
    level: str
    confidence: float
    detected_brand: str | None = None
    reasons: list[str] = Field(default_factory=list)
    modules: ModulesResult
