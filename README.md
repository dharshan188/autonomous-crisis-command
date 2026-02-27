# 🚨 Autonomous Crisis Command System

AI-powered human-in-the-loop crisis response system.

## 🔥 Features

- AI crisis classification
- Conflict resolution engine
- Human approval via phone call
- Twilio IVR integration
- Dispatch execution
- Audit logging
- Thread-safe approval handling

---

## 🛠 Setup Instructions

### 1️⃣ Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/autonomous-crisis-command.git
cd autonomous-crisis-command/backend



step 1

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt


step 2
# install or setup ngrok if you haven't already
1. Download the binary from https://ngrok.com/download and add it to your PATH, or install via `npm install -g ngrok`.
2. Run `ngrok http 8000` from the backend directory (or anywhere on your system).
3. Copy the generated HTTPS URL and paste it in `.env` as `PUBLIC_URL`.

step 3 
uvicorn main:app --reload --port 8000
step 4 test
curl -X POST http://127.0.0.1:8000/crisis_command \
-H "Content-Type: application/json" \
-d '{"crises":["Major fire near fuel depot in Sector 7."], "approved": false}'