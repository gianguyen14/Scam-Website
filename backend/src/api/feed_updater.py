import os
import requests
import sqlite3
import urllib.parse
from datetime import datetime

def update_threat_intel_feeds():
    print(f"[{datetime.now()}] Starting Zero-day Threat Intel Feed Update...")
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    db_path = os.path.join(base_dir, "data", "community_scams.sqlite3")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS live_feeds
                      (domain TEXT PRIMARY KEY, source TEXT, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    new_domains = 0

    # 1. Fetch OpenPhish
    try:
        r = requests.get("https://openphish.com/feed.txt", timeout=10)
        if r.status_code == 200:
            for line in r.text.split("\n"):
                if line.strip():
                    try:
                        domain = urllib.parse.urlparse(line.strip()).hostname
                        if domain:
                            domain = domain.lower()
                            cursor.execute("INSERT OR REPLACE INTO live_feeds (domain, source, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)", (domain, "OpenPhish"))
                            new_domains += 1
                    except Exception: pass
    except Exception as e:
        print("OpenPhish Error:", e)

    # 2. Fetch URLhaus (CSV online only)
    try:
        r = requests.get("https://urlhaus.abuse.ch/downloads/csv_online/", timeout=15)
        if r.status_code == 200:
            lines = r.text.split("\n")
            for line in lines:
                if line and not line.startswith("#"):
                    parts = line.split('","')
                    if len(parts) > 2:
                        url = parts[2].strip('"')
                        try:
                            domain = urllib.parse.urlparse(url).hostname
                            if domain:
                                domain = domain.lower()
                                cursor.execute("INSERT OR REPLACE INTO live_feeds (domain, source, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)", (domain, "URLhaus"))
                                new_domains += 1
                        except Exception: pass
    except Exception as e:
        print("URLhaus Error:", e)

    conn.commit()
    
    # Cleanup old entries (> 7 days) as live feeds rotate fast
    cursor.execute("DELETE FROM live_feeds WHERE updated_at <= date('now', '-7 day')")
    conn.commit()
    conn.close()
    print(f"[{datetime.now()}] Threat Intel Update Complete. Processed {new_domains} live domains.")

if __name__ == "__main__":
    update_threat_intel_feeds()
