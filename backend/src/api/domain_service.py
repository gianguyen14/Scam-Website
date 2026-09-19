import os
import json
import urllib.parse
from typing import Dict, Any

class DomainService:
    def __init__(self):
        # Local mock registry of malicious properties
        self.malicious_domains = {"hacker.com", "phish.xyz", "scam.io", "bad.com"}
        self.whitelist = {"example.com", "google.com", "github.com", "vietcombank.com.vn"}
        
        # Load ScamSniffer database
        self._load_scamsniffer()
        
    def _load_scamsniffer(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        db_path = os.path.join(base_dir, "data", "scamsniffer_domains.json")
        try:
            if os.path.exists(db_path):
                with open(db_path, "r", encoding="utf-8") as f:
                    domains = json.load(f)
                    # Use a set for O(1) lookup
                    self.malicious_domains.update([d.lower() for d in domains])
        except Exception as e:
            print("Failed to load scamsniffer domains:", e)

    def extract_domain(self, url: str) -> str:
        try:
            parsed = urllib.parse.urlparse(url if "://" in url else "http://" + url)
            return parsed.hostname or ""
        except Exception:
            return ""

    def evaluate(self, domain: str) -> Dict[str, Any]:
        if not domain:
            return {"known_malicious": False, "score": 0.0}
            
        domain = domain.lower()
        score = 0.0
        reasons = []
        
        # 1. Reputation (Check exact match and wildcard subdomains)
        is_malicious = False
        parts = domain.split('.')
        
        # Check domain and all root variants (e.g. sub.scam.com -> scam.com)
        for i in range(len(parts)):
            sub_domain = ".".join(parts[i:])
            if sub_domain in self.malicious_domains:
                is_malicious = True
                break
                
        if is_malicious:
            return {"known_malicious": True, "score": 100.0, "reasons": ["Domain is listed in Web3/Crypto Scam Blocklist (ScamSniffer)"]}
            
        if domain in self.whitelist:
            return {"known_safe": True, "score": 0.0, "reasons": []}
            
        # 2. Mocked heuristics
        if domain.endswith(".xyz") or domain.endswith(".top"):
            score += 25
            reasons.append("High-risk TLD")
            
        # Unusually high number of digits
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
