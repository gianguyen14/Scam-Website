import urllib.parse
from typing import Any


class DomainService:
    def __init__(self):
        # Local mock registry of malicious properties
        self.malicious_domains = {"hacker.com", "phish.xyz", "scam.io", "bad.com"}
        self.whitelist = {"example.com", "google.com", "github.com", "vietcombank.com.vn"}
        
    def extract_domain(self, url: str) -> str:
        try:
            parsed = urllib.parse.urlparse(url if "://" in url else "http://" + url)
            return parsed.hostname or ""
        except Exception:
            return ""

    def evaluate(self, domain: str) -> dict[str, Any]:
        if not domain:
            return {"known_malicious": False, "score": 0.0}
            
        domain = domain.lower()
        score = 0.0
        reasons = []
        
        # 1. Reputation
        if domain in self.malicious_domains:
            return {"known_malicious": True, "score": 100.0, "reasons": ["Domain is blocklisted"]}
            
        if domain in self.whitelist:
            return {"known_safe": True, "score": 0.0, "reasons": []}
            
        # 2. Mocked heuristics
        if domain.endswith(".xyz") or domain.endswith(".top"):
            score += 25
            reasons.append("High-risk TLD")
            
        if sum(1 for c in domain if c.isdigit()) > 5:
            score += 15
            reasons.append("Unusually high number of digits in domain")
            
        if "-" in domain:
            score += 10
        
        return {
            "known_malicious": False,
            "score": score,
            "reasons": reasons
        }
