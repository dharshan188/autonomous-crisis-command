#/bin/bash
echo "1. Posting crisis to backend..."
RES=$(curl -s -X POST http://127.0.0.1:8000/crisis_command -H "Content-Type: application/json" -d '{"crises":["Massive fire at 4th street"], "approved": false}')
echo $RES
CRISIS_ID=$(echo $RES | grep -o '"crisis_id":"[^"]*' | cut -d'"' -f4)
if [ -z "$CRISIS_ID" ]; then
    echo "No crisis ID found"
    exit 1
fi
echo "Crisis ID: $CRISIS_ID"

echo "2. Simulating Twilio approval digit 6..."
curl -s -X POST "http://127.0.0.1:8000/process?crisis_id=$CRISIS_ID" -d "Digits=6"
echo ""

echo "3. Checking Audit logs..."
curl -s http://127.0.0.1:8000/audit | jq .
