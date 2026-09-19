import os
import json
import gzip
import urllib.parse
import socket
from typing import Dict, Any

class DomainService:
    def __init__(self):
        # Local mock registry of malicious properties
        self.malicious_domains = {"hacker.com", "phish.xyz", "scam.io", "bad.com"}
        self.whitelist = {
            "example.com", "google.com", "github.com", "vietcombank.com.vn",
            "chatgpt.com", "openai.com", "facebook.com", "youtube.com", 
            "shopee.vn", "tiki.vn", "lazada.vn", "vnexpress.net", "dantri.com.vn",
            "tiktok.com", "messenger.com", "apple.com", "microsoft.com",
            "vercel.app", "gianguyen14.tech"
        }
        
        
        
        # Load ScamSniffer database
        self._load_scamsniffer()
        
        # Load Global Phishing Database
        self._load_phishing_db()
        
        # Load Malicious IP Infrastructure
        self.malicious_ips = set()
        self._load_malicious_ips()
        
    
    def _load_malicious_ips(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        ipsum_path = os.path.join(base_dir, "data", "ipsum.txt.gz")
        try:
            if os.path.exists(ipsum_path):
                with gzip.open(ipsum_path, "rt", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            parts = line.split()
                            if len(parts) >= 2:
                                ip = parts[0]
                                score = int(parts[1])
                                if score >= 2:
                                    self.malicious_ips.add(ip)
        except Exception as e:
            print("Failed to load IPs:", e)


        
    
    def _load_scamsniffer(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        db_path = os.path.join(base_dir, "data", "scamsniffer_domains.json.gz")
        try:
            if os.path.exists(db_path):
                with gzip.open(db_path, "rt", encoding="utf-8") as f:
                    domains = json.load(f)
                    self.malicious_domains.update([d.lower() for d in domains])
        except Exception as e:
            print("Failed to load scamsniffer domains:", e)

    def _load_phishing_db(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        db_path = os.path.join(base_dir, "data", "phishing_domains.txt.gz")
        try:
            if os.path.exists(db_path):
                with gzip.open(db_path, "rt", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            self.malicious_domains.add(line.lower())
        except Exception as e:
            print("Failed to load phishing db:", e)



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
        
        
        # Live Feed Check (Zero-Day from OpenPhish / URLhaus)
        try:
            
            if os.environ.get("VERCEL") or os.environ.get("VERCEL_BUILD"):
                db_path = "/tmp/community_scams.sqlite3"
            else:
                db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "community_scams.sqlite3")

            if os.path.exists(db_path):
                import sqlite3
                conn = sqlite3.connect(db_path)
                c = conn.cursor()
                # Check root domain and subdomains
                c.execute("SELECT source FROM live_feeds WHERE domain=?", (domain,))
                row = c.fetchone()
                conn.close()
                if row:
                    return {"known_malicious": True, "score": 100.0, "reasons": [f"Zero-Day Threat: Domain detected in Live Feed ({row[0]})"]}
        except Exception:
            pass

        # 0. Infrastructure Check (DNS Resolve -> Malicious IP Blocklist)
        resolved_ip = None
        try:
            # Short timeout so we don't hang the API
            socket.setdefaulttimeout(1.5)
            resolved_ip = socket.gethostbyname(domain)
            if resolved_ip in self.malicious_ips:
                return {"known_malicious": True, "score": 100.0, "reasons": [f"Domain hosted on known Malicious Infrastructure / Botnet IP (IPSUM Flagged: {resolved_ip})"]}
        except Exception:
            pass
            
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
            return {"known_malicious": True, "score": 100.0, "reasons": ["Domain is listed in Global Scam/Phishing Database (ScamSniffer / Phishing.Database)"]}
            
        
        # Government & Education Safe TLDs Override (Vietnam specific)
        if domain.endswith(".gov.vn") or domain.endswith(".edu.vn"):
            return {"known_safe": True, "score": 0.0, "reasons": []}
            
        if domain in self.whitelist:
            return {"known_safe": True, "score": 0.0, "reasons": []}
            
        # 2. Mocked heuristics
        suspicious_tlds = [".xyz", ".top", ".icu", ".click", ".fun", ".cyou", ".space", ".cc", ".vip", ".live"]
        matched_tld = [tld for tld in suspicious_tlds if domain.endswith(tld)]
        if matched_tld:
            score += 35
            reasons.append(f"High-risk TLD used frequently by scammers ({matched_tld[0]})")
            
        # Unusually high number of digits or hyphens (typical in autogen domains)

            
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
