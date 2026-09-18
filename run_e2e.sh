#!/bin/bash
cd /home/hermes/Scam-Website/backend
. .venv/bin/activate
uvicorn src.main:app --host 127.0.0.1 --port 8000 &
BGPID=$!

# Wait for backend
sleep 3

cd /home/hermes/Scam-Website
node test_puppeteer.js
RESULT=$?

kill $BGPID
exit $RESULT
