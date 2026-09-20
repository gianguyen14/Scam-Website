#!/bin/bash
cd /home/hermes/Scam-Website/backend
. .venv/bin/activate
uvicorn src.main:app --host 127.0.0.1 --port 8000 &> /dev/null &
BGPID=$!

while ! curl -s http://127.0.0.1:8000/health > /dev/null; do sleep 1; done

cd /home/hermes/Scam-Website
node real_test.js
RESULT=$?
kill $BGPID
exit $RESULT
