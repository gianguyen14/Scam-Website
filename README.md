# ScamGuard AI
Browser Extension phát hiện URL phishing và website lừa đảo theo thời gian thực (Manifest V3 + FastAPI).

## Features
- **URL Analysis**: Heuristic & rule-based scanning (IP, Suspicious TLDs, Shorteners, Keywords).
- **DOM Scanner**: Detects password fields, OTPs, external forms, and hidden iFrames securely (no passwords transmitted!).
- **Brand Guard**: Warns if a site pretends to be Vietcombank, Binance, or Microsoft but uses a mismatched domain.
- **Risk Aggregator**: Computes score 0-100 indicating `safe`, `suspicious`, or `dangerous`.
- **Warning Overlay**: Interrupts unsafe browsing with explicit bypass buttons.
- **Cache Strategy**: Caches decisions for 1 hour to prevent redundant backend calls.

## Run Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```
Or via Docker:
```bash
cd backend
docker build -t scamguard-backend .
docker run -p 8000:8000 scamguard-backend
```

## Load Extension
1. Open Chrome/Edge and go to `chrome://extensions/`
2. Enable "Developer Mode"
3. Click "Load unpacked"
4. Select the `extension/` folder inside this repository.
