import uvicorn
import os
from fastapi import FastAPI, Request
from fastapi.responses import Response
from pydantic import BaseModel
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from uuid import uuid4
from datetime import datetime
import threading

from ai_model import CrisisModel
from crisis_engine import CrisisEngine
from services.audit import get_audit_log, record_event
from services.dispatcher import execute_dispatch

# ==============================
# Load Environment
# ==============================

load_dotenv()

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")
OFFICER_NUMBER = os.getenv("OFFICER_NUMBER")
PUBLIC_URL = os.getenv("PUBLIC_URL")

twilio_client = Client(TWILIO_SID, TWILIO_AUTH)

# ==============================
# Request / Response Models
# ==============================

class CrisisCommandRequest(BaseModel):
    crises: list
    approved: bool


class CrisisCommandResponse(BaseModel):
    status: str
    details: dict | list | None = None
    execution_result: dict | None = None
    alerts: list | None = None
    crisis_id: str | None = None


# ==============================
# Global State
# ==============================

crisis_model: CrisisModel | None = None
crisis_engine: CrisisEngine | None = None

pending_decisions = {}
pending_decisions_lock = threading.Lock()
DECISION_TIMEOUT_SECONDS = 900  # 15 minutes

# ==============================
# Lifespan
# ==============================

@asynccontextmanager
async def lifespan(app: FastAPI):
    global crisis_model, crisis_engine

    print("Initializing CrisisModel...")
    crisis_model = CrisisModel()

    print("Initializing CrisisEngine...")
    crisis_engine = CrisisEngine(crisis_model)

    print("Application startup complete")
    yield
    print("Shutting down application...")

app = FastAPI(
    title="Autonomous Crisis Command System",
    version="3.0.0",
    lifespan=lifespan
)

# ==============================
# Crisis Command
# ==============================

@app.post("/crisis_command", response_model=CrisisCommandResponse)
async def crisis_command(request: CrisisCommandRequest):

    if crisis_engine is None:
        return {"status": "ERROR", "details": "Engine not initialized"}

    result = crisis_engine.process_crises(
        request.crises,
        request.approved
    )

    # 🔥 Approval Required
    if result["status"] == "PENDING_APPROVAL":

        crisis_id = str(uuid4())

        call = twilio_client.calls.create(
            url=f"{PUBLIC_URL}/voice?crisis_id={crisis_id}",
            to=OFFICER_NUMBER,
            from_=TWILIO_NUMBER
        )

        with pending_decisions_lock:
            pending_decisions[crisis_id] = {
                "decision_output": result.get("decision_output", {}),
                "call_sid": call.sid,
                "timestamp": datetime.utcnow().isoformat()
            }

        record_event("APPROVAL_REQUESTED", {
            "crisis_id": crisis_id,
            "call_sid": call.sid,
            "details": result.get("details"),
            "timestamp": datetime.utcnow().isoformat()
        })

        return {
            "status": "CALL_TRIGGERED",
            "details": result.get("details"),
            "crisis_id": crisis_id
        }

    # 🔥 Auto Execution
    if result["status"] == "EXECUTED":

        execution_result = execute_dispatch(result["execution_result"])

        return {
            "status": "EXECUTED",
            "execution_result": execution_result,
            "alerts": result.get("alerts")
        }

    return {"status": "UNKNOWN"}


# ==============================
# Twilio Voice Endpoint
# ==============================

@app.post("/voice")
async def voice(crisis_id: str):

    response = VoiceResponse()

    with pending_decisions_lock:
        if crisis_id not in pending_decisions:
            response.say("No valid crisis associated with this call.")
            return Response(content=str(response), media_type="text/xml")

        pending = pending_decisions[crisis_id]
        timestamp = datetime.fromisoformat(pending["timestamp"])
        age = (datetime.utcnow() - timestamp).total_seconds()

        if age > DECISION_TIMEOUT_SECONDS:
            del pending_decisions[crisis_id]
            record_event("APPROVAL_TIMEOUT", {"crisis_id": crisis_id})
            response.say("This approval request has expired.")
            return Response(content=str(response), media_type="text/xml")

    response.say("High risk crisis detected requiring authorization.")

    gather = response.gather(
        num_digits=1,
        action=f"/process?crisis_id={crisis_id}",
        method="POST"
    )

    gather.say("Press 6 to approve dispatch. Press any other number to reject.")

    return Response(content=str(response), media_type="text/xml")


# ==============================
# Process Approval
# ==============================

@app.post("/process")
async def process(request: Request, crisis_id: str):

    form = await request.form()
    digit = form.get("Digits")

    response = VoiceResponse()

    with pending_decisions_lock:
        if crisis_id not in pending_decisions:
            response.say("Crisis not found or expired.")
            return Response(content=str(response), media_type="text/xml")

        pending = pending_decisions[crisis_id]
        decision_output = pending["decision_output"]
        call_sid = pending["call_sid"]

        if digit == "6":

            execution_result = execute_dispatch(decision_output)

            record_event("APPROVAL_EXECUTED", {
                "crisis_id": crisis_id,
                "call_sid": call_sid,
                "execution_status": execution_result["execution_status"],
                "dispatch_count": len(execution_result.get("dispatch_log", []))
            })

            response.say("Request approved. Units dispatched successfully.")

        else:

            record_event("APPROVAL_REJECTED", {
                "crisis_id": crisis_id,
                "call_sid": call_sid,
                "digit": digit
            })

            response.say("Request rejected. No action taken.")

        del pending_decisions[crisis_id]

    return Response(content=str(response), media_type="text/xml")


# ==============================
# Audit & Health
# ==============================

@app.get("/audit")
async def audit():
    return get_audit_log()

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "model_initialized": crisis_model is not None,
        "engine_initialized": crisis_engine is not None
    }


# ==============================
# Run
# ==============================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )