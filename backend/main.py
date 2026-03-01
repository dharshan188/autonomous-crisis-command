import uvicorn
import os
import threading
import json
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import Response, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from twilio.twiml.voice_response import VoiceResponse
from uuid import uuid4
from datetime import datetime

from ai_model import CrisisModel
from crisis_engine import CrisisEngine
from services.dispatcher import execute_dispatch
from services.voice_service import trigger_approval_call, orchestrate_response
from services.autonomous_monitor import detect_flood
from services.audit import get_audit_log
from db import SessionLocal, create_tables, CrisisReport

from generate_report import generate_comprehensive_report

load_dotenv()

OFFICER_NUMBER = os.getenv("OFFICER_NUMBER")
PUBLIC_URL = os.getenv("PUBLIC_URL")

# =========================================================
# MODELS
# =========================================================

class CrisisCommandRequest(BaseModel):
    crises: list
    approved: bool


class CrisisCommandResponse(BaseModel):
    status: str
    details: dict | list | None = None
    crisis_id: str | None = None
    call_sid: str | None = None


class AutonomousRequest(BaseModel):
    location: str


# =========================================================
# GLOBAL STATE
# =========================================================

crisis_model = None
crisis_engine = None
pending_decisions = {}
pending_decisions_lock = threading.Lock()
active_autonomous_alerts = {}

# =========================================================
# LIFESPAN
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    global crisis_model, crisis_engine
    crisis_model = CrisisModel()
    crisis_engine = CrisisEngine(crisis_model)
    create_tables()
    yield


app = FastAPI(lifespan=lifespan)

# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# MANUAL MODE
# =========================================================

@app.post("/crisis_command", response_model=CrisisCommandResponse)
async def crisis_command(request: CrisisCommandRequest):

    result = crisis_engine.process_crises(
        request.crises,
        request.approved
    )

    if result["status"] != "PENDING_APPROVAL":
        return result

    crisis_id = str(uuid4())

    session = SessionLocal()
    report = CrisisReport(
        crisis_id=crisis_id,
        submitted_at=datetime.now(),
        approval_status="PENDING",
        teams_notified=json.dumps([])
    )
    session.add(report)
    session.commit()
    session.close()

    with pending_decisions_lock:
        pending_decisions[crisis_id] = {
            "decision_output": result.get("decision_output", {}),
            "timestamp": datetime.now().isoformat()
        }

    call_sid = trigger_approval_call(
        OFFICER_NUMBER,
        PUBLIC_URL,
        crisis_id
    )

    return {
        "status": "CALL_TRIGGERED",
        "details": result.get("details"),
        "crisis_id": crisis_id,
        "call_sid": call_sid
    }

# =========================================================
# =========================================================
# AUTONOMOUS MODE (FIXED FULL INTELLIGENCE RETURN)
# =========================================================

@app.post("/autonomous_scan")
async def autonomous_scan(request: AutonomousRequest):

    result = detect_flood(request.location)

    # Always return result if not flood
    if result["status"] != "FLOOD_DETECTED":
        return result

    location_key = result["location"]

    # 🔥 If already pending, still return FULL data
    if location_key in active_autonomous_alerts:
        return {
            "status": "ALREADY_PENDING",
            **result
        }

    crisis_id = str(uuid4())
    active_autonomous_alerts[location_key] = crisis_id

    session = SessionLocal()
    report = CrisisReport(
        crisis_id=crisis_id,
        submitted_at=datetime.now(),
        approval_status="PENDING",
        teams_notified=json.dumps([])
    )
    session.add(report)
    session.commit()
    session.close()

    decision_output = {
        "decisions": [{
            "crisis_type": "Flood",
            "location": location_key
        }]
    }

    with pending_decisions_lock:
        pending_decisions[crisis_id] = {
            "decision_output": decision_output,
            "timestamp": datetime.now().isoformat()
        }

    call_sid = trigger_approval_call(
        OFFICER_NUMBER,
        PUBLIC_URL,
        crisis_id
    )

    # 🔥 Return FULL intelligence + call info
    return {
        "status": "FLOOD_CALL_TRIGGERED",
        "crisis_id": crisis_id,
        "call_sid": call_sid,
        **result
    }
# =========================================================
# VOICE
# =========================================================

@app.api_route("/voice", methods=["GET", "POST"])
async def voice(crisis_id: str = Query(None)):

    response = VoiceResponse()

    gather = response.gather(
        num_digits=1,
        action=f"{PUBLIC_URL}/process?crisis_id={crisis_id}",
        method="POST"
    )
    gather.say("good morning sir ..there is a disaster emergency reported.to call the required emergency response team.")
    gather.say("Press 6 to approve, or any other key to reject.")
    return Response(str(response), media_type="text/xml")

# =========================================================
# PROCESS APPROVAL
# =========================================================

@app.api_route("/process", methods=["GET", "POST"])
async def process(request: Request, crisis_id: str = Query(None)):

    response = VoiceResponse()

    with pending_decisions_lock:

        if crisis_id not in pending_decisions:
            response.say("Crisis expired.")
            return Response(str(response), media_type="text/xml")

        form = await request.form()
        digit = form.get("Digits")

        decision_output = pending_decisions[crisis_id]["decision_output"]

        session = SessionLocal()
        report = session.query(CrisisReport).filter_by(
            crisis_id=crisis_id
        ).first()

        if digit == "6":

            execute_dispatch(decision_output)

            crisis_type = decision_output["decisions"][0]["crisis_type"]
            location = decision_output["decisions"][0]["location"]

            threading.Thread(
                target=orchestrate_response,
                args=(crisis_type, location, 25),
                daemon=True
            ).start()

            if report:
                report.approval_status = "APPROVED"
                report.approval_time = datetime.now()
                report.dispatch_time = datetime.now()

                # 🔥 Generate report AND store path
                file_path = generate_comprehensive_report(crisis_id)
                report.report_path = file_path

                session.commit()

            response.say("Approved.Thank you sir, Emergency teams notified.")

        else:
            if report:
                report.approval_status = "REJECTED"
                report.approval_time = datetime.now()
                session.commit()

            response.say("Rejected.")

        del pending_decisions[crisis_id]

        for loc, cid in list(active_autonomous_alerts.items()):
            if cid == crisis_id:
                del active_autonomous_alerts[loc]

        session.close()

    return Response(str(response), media_type="text/xml")

# =========================================================
# STATUS + REPORT ENDPOINT
# =========================================================

@app.get("/crisis_status/{crisis_id}")
async def crisis_status(crisis_id: str):
    session = SessionLocal()
    report = session.query(CrisisReport).filter_by(crisis_id=crisis_id).first()
    session.close()

    if not report:
        return {"status": "NOT_FOUND"}

    return {"status": report.approval_status}


@app.get("/crisis_report/{crisis_id}")
async def crisis_report(crisis_id: str):
    session = SessionLocal()
    report = session.query(CrisisReport).filter_by(crisis_id=crisis_id).first()
    session.close()

    if not report or not report.report_path:
        raise HTTPException(status_code=404, detail="Report not found")

    if not os.path.exists(report.report_path):
        raise HTTPException(status_code=404, detail="File missing")

    return FileResponse(
        report.report_path,
        media_type="application/pdf",
        filename=os.path.basename(report.report_path)
    )


@app.get("/audit_log")
async def audit_log_endpoint():
    return get_audit_log()


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)