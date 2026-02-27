import uvicorn
import os
from fastapi import FastAPI, Request, Query
from fastapi.responses import Response
from starlette.middleware.cors import CORSMiddleware
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

load_dotenv()

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")
OFFICER_NUMBER = os.getenv("OFFICER_NUMBER")
PUBLIC_URL = os.getenv("PUBLIC_URL")

twilio_client = Client(TWILIO_SID, TWILIO_AUTH)

class CrisisCommandRequest(BaseModel):
    crises: list
    approved: bool

class CrisisCommandResponse(BaseModel):
    status: str
    details: dict | list | None = None
    execution_result: dict | None = None
    alerts: list | None = None
    crisis_id: str | None = None
    call_sid: str | None = None

crisis_model = None
crisis_engine = None

pending_decisions = {}
completed_decisions = {}
pending_decisions_lock = threading.Lock()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global crisis_model, crisis_engine
    crisis_model = CrisisModel()
    crisis_engine = CrisisEngine(crisis_model)
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Crisis Command
# -----------------------------
@app.post("/crisis_command", response_model=CrisisCommandResponse)
async def crisis_command(request: CrisisCommandRequest):

    result = crisis_engine.process_crises(
        request.crises,
        request.approved
    )

    if result["status"] == "PENDING_APPROVAL":

        crisis_id = str(uuid4())

        try:
            call = twilio_client.calls.create(
                url=f"{PUBLIC_URL}/voice?crisis_id={crisis_id}",
                to=OFFICER_NUMBER,
                from_=TWILIO_NUMBER
            )
            call_sid = call.sid
        except Exception:
            call_sid = f"SIM-{uuid4()}"

        with pending_decisions_lock:
            pending_decisions[crisis_id] = {
                "decision_output": result.get("decision_output", {}),
                "call_sid": call_sid,
                "timestamp": datetime.utcnow().isoformat()
            }

        return {
            "status": "CALL_TRIGGERED",
            "details": result.get("details"),
            "crisis_id": crisis_id,
            "call_sid": call_sid
        }

    if result["status"] == "EXECUTED":

        execution_result = execute_dispatch(result["execution_result"])

        return {
            "status": "EXECUTED",
            "execution_result": execution_result,
            "alerts": result.get("alerts")
        }

    return {"status": "UNKNOWN"}


# -----------------------------
# Voice
# -----------------------------
@app.post("/voice")
async def voice(crisis_id: str = Query(...)):

    response = VoiceResponse()

    gather = response.gather(
        num_digits=1,
        action=f"{PUBLIC_URL}/process?crisis_id={crisis_id}",
        method="POST"
    )

    gather.say("High risk crisis detected. Press 6 to approve dispatch.")

    return Response(str(response), media_type="text/xml")


# -----------------------------
# Process Approval
# -----------------------------
@app.post("/process")
async def process(request: Request, crisis_id: str = Query(...)):

    form = await request.form()
    digit = form.get("Digits")

    response = VoiceResponse()

    with pending_decisions_lock:
        if crisis_id not in pending_decisions:
            response.say("Crisis expired.")
            return Response(str(response), media_type="text/xml")

        pending = pending_decisions[crisis_id]
        decision_output = pending["decision_output"]

        if digit == "6":
            execution_result = execute_dispatch(decision_output)

            completed_decisions[crisis_id] = {
                "status": "EXECUTED",
                "execution_result": execution_result
            }

            response.say("Approved. Units dispatched.")

        else:
            completed_decisions[crisis_id] = {
                "status": "REJECTED"
            }

            response.say("Rejected.")

        del pending_decisions[crisis_id]

    return Response(str(response), media_type="text/xml")


# -----------------------------
# Crisis Status (NEW)
# -----------------------------
@app.get("/crisis_status/{crisis_id}")
async def crisis_status(crisis_id: str):

    if crisis_id in completed_decisions:
        return completed_decisions[crisis_id]

    if crisis_id in pending_decisions:
        return {"status": "WAITING_APPROVAL"}

    return {"status": "NOT_FOUND"}


@app.get("/health")
async def health():
    return {"status": "healthy"}