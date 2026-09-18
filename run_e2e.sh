#!/bin/bash
cd /home/hermes/Scam-Website/backend
. .venv/bin/activate
uvicorn src.main:app --host 127.0.0.1 --port 8000 &
BGPID=$!

echo "Waiting for Uvicorn to start..."
while ! curl -s http://127.0.0.1:8000/health > /dev/null; do
    sleep 1
done
echo "Uvicorn started!"

cd /home/hermes/Scam-Website
node test_puppeteer.js
RESULT=$?

kill $BGPID
exit $RESULT
