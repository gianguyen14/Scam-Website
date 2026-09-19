import os
import sqlite3
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

@router.get("/", include_in_schema=False)
def read_root():
    return RedirectResponse(url='/dashboard')

from fastapi.templating import Jinja2Templates
from src.schemas.models import ScanRequest, ScanResponse, ModulesResult, ScamReport, VisionRequest
from src.api.url_detector import extract_url_features
from src.api.risk_model import CoreRiskEngine
from src.api.vision_ai import AdvancedVisionAI

router = APIRouter()
vision_agent = AdvancedVisionAI()


base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
templates = Jinja2Templates(directory=os.path.join(base_dir, "src", "templates"))

# Dynamic SQLite Path: Vercel serverless only allows writing to /tmp/
if os.environ.get("VERCEL") or os.environ.get("VERCEL_BUILD"):
    db_path = "/tmp/community_scams.sqlite3"
else:
    db_path = os.path.join(base_dir, "data", "community_scams.sqlite3")


def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS scams
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT, amount REAL, currency TEXT, 
                      platform TEXT, desc TEXT, scammer TEXT, phishing BOOLEAN, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS telemetry
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, domain TEXT, score INTEGER, level TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

engine = CoreRiskEngine()

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.post("/api/v1/scan", response_model=ScanResponse)
def scan_url(request: ScanRequest):
    url_features = extract_url_features(request.url)
    page_features = request.page or {}
    
    result = engine.evaluate(request.url, url_features, page_features)
    
    
    # Ghi log Telemetry nhanh
    import urllib.parse
    try:
        req_domain = urllib.parse.urlparse(request.url).hostname or "unknown"
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('INSERT INTO telemetry (domain, score, level) VALUES (?, ?, ?)', (req_domain, risk_score, level))
        conn.commit()
        conn.close()
    except Exception:
        pass

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


@router.get("/dashboard", response_class=HTMLResponse)
def view_dashboard(request: Request):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM telemetry")
    total_scans = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM telemetry WHERE level='dangerous'")
    total_blocked = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM scams")
    total_reports = c.fetchone()[0]
    
    c.execute("SELECT domain, score, timestamp FROM telemetry ORDER BY timestamp DESC LIMIT 10")
    recent_scans = c.fetchall()
    
    c.execute("SELECT url, desc, timestamp FROM scams ORDER BY timestamp DESC LIMIT 10")
    recent_reports = c.fetchall()
    conn.close()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "total_scans": total_scans,
        "total_blocked": total_blocked,
        "total_reports": total_reports,
        "recent_scans": recent_scans,
        "recent_reports": recent_reports
    })


@router.get("/api/v1/cron/update-feeds")
def vercel_cron_update():
    from src.api.feed_updater import update_threat_intel_feeds
    update_threat_intel_feeds()
    return {"status": "success", "message": "Updated intelligence feeds globally."}
