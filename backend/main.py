import uvicorn
import os
import threading
import json
from fastapi import FastAPI, Request, Query
from fastapi.responses import Response, FileResponse
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from twilio.twiml.voice_response import VoiceResponse
from uuid import uuid4
from datetime import datetime

from ai_model import CrisisModel
from crisis_engine import CrisisEngine
from services.dispatcher import execute_dispatch
from services.voice_service import (
    trigger_approval_call,
    orchestrate_response
)
from services.audit import get_audit_log, record_event

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Flowable,
    ListFlowable,
    ListItem,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

from db import SessionLocal, create_tables, CrisisReport

load_dotenv()

OFFICER_NUMBER = os.getenv("OFFICER_NUMBER")
PUBLIC_URL = os.getenv("PUBLIC_URL")

if not PUBLIC_URL or not PUBLIC_URL.startswith("https://"):
    # approval call helper enforces HTTPS; if the variable isn't configured correctly
    # we won't be able to reach the FastAPI webhook from Twilio.  Log a warning so
    # developers notice during startup instead of debugging mysterious call failures.
    print("[warning] PUBLIC_URL is not set or not HTTPS. Approval calls may fail.")


# =============================
# MODELS
# =============================

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


# =============================
# GLOBAL STATE
# =============================

crisis_model = None
crisis_engine = None

pending_decisions = {}
pending_decisions_lock = threading.Lock()


# =============================
# LIFESPAN
# =============================

@asynccontextmanager
async def lifespan(app: FastAPI):
    global crisis_model, crisis_engine
    crisis_model = CrisisModel()
    crisis_engine = CrisisEngine(crisis_model)
    create_tables()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================
# CRISIS COMMAND
# =============================

@app.post("/crisis_command", response_model=CrisisCommandResponse)
async def crisis_command(request: CrisisCommandRequest):

    result = crisis_engine.process_crises(
        request.crises,
        request.approved
    )

    if result["status"] == "PENDING_APPROVAL":

        crisis_id = str(uuid4())

        # Save to DB
        session = SessionLocal()
        report = CrisisReport(
            crisis_id=crisis_id,
            submitted_at=datetime.now(),
            approval_status="PENDING",
            approval_time=None,
            dispatch_time=None,
            teams_notified=json.dumps([]),
        )
        session.add(report)
        session.commit()
        session.close()

        record_event("APPROVAL_CALL_TRIGGERED", {
            "crisis_id": crisis_id,
            "officer_number": OFFICER_NUMBER,
            "status": "Calling for approval..."
        })

        try:
            call_sid = trigger_approval_call(
                OFFICER_NUMBER,
                PUBLIC_URL,
                crisis_id
            )
        except Exception:
            call_sid = f"SIM-{uuid4()}"

        with pending_decisions_lock:
            pending_decisions[crisis_id] = {
                "decision_output": result.get("decision_output", {}),
                "timestamp": datetime.now().isoformat()
            }

        return {
            "status": "CALL_TRIGGERED",
            "details": result.get("details"),
            "crisis_id": crisis_id,
            "call_sid": call_sid
        }

    return {"status": "UNKNOWN"}


# =============================
# VOICE ENDPOINT
# =============================

# Twilio may use GET or POST when requesting our voice URL depending on configuration.
# Responding with an error (405) will cause the caller to hear "Application Error, goodbye".
# Allow both methods and make the handler resilient to missing query parameters.

@app.api_route("/voice", methods=["GET", "POST"])
async def voice(crisis_id: str = Query(None)):
    response = VoiceResponse()

    if not crisis_id:
        # If the query parameter didn't make it through, give a generic message so Twilio
        # doesn't return an error status code.
        response.say("An error occurred. Please try again later.")
        return Response(str(response), media_type="text/xml")

    try:
        gather = response.gather(
            num_digits=1,
            action=f"{PUBLIC_URL}/process?crisis_id={crisis_id}&ngrok-skip-browser-warning=true",
            method="POST"
        )
        gather.say("High risk crisis detected. Press 6 to approve dispatch.")
    except Exception as exc:
        # In the unlikely case constructing the TwiML fails, fall back to a generic message
        response = VoiceResponse()
        response.say("An internal error occurred. Goodbye.")
        # Log error for diagnostics
        print("[voice] TwiML build error:", exc)

    return Response(str(response), media_type="text/xml")


# =============================
# PROCESS APPROVAL
# =============================

# Gather will POST by default, but be tolerant of GET just in case.
@app.api_route("/process", methods=["GET", "POST"])
async def process(request: Request, crisis_id: str = Query(None)):

    response = VoiceResponse()

    if crisis_id is None:
        # nothing we can do if we don't know which crisis
        response.say("An error occurred. Goodbye.")
        return Response(str(response), media_type="text/xml")

    try:
        form = await request.form()
        digit = form.get("Digits")
    except Exception:
        # GET requests won't have a form; treat as no digit entered
        digit = None

    with pending_decisions_lock:

        if crisis_id not in pending_decisions:
            response.say("Crisis expired.")
            return Response(str(response), media_type="text/xml")

        decision_output = pending_decisions[crisis_id]["decision_output"]

        session = SessionLocal()
        report = session.query(CrisisReport).filter_by(crisis_id=crisis_id).first()

        if digit == "6":

            record_event("APPROVAL_GRANTED", {
                "crisis_id": crisis_id,
                "status": "Approved by Officer",
                "details": "Units dispatching"
            })

            execution_result = execute_dispatch(decision_output)

            if report:
                report.approval_status = "APPROVED"
                report.approval_time = datetime.now()
                report.dispatch_time = datetime.now()
                session.add(report)
                session.commit()

            # Safe decision access
            if decision_output.get("decisions"):
                crisis_type = decision_output["decisions"][0]["crisis_type"]
                location = decision_output["decisions"][0]["location"]

                threading.Thread(
                    target=notify_and_log,
                    args=(crisis_id, crisis_type, location),
                    daemon=True
                ).start()

            response.say("Approved. Units dispatched and emergency teams notified.")

        else:
            record_event("APPROVAL_REJECTED", {
                "crisis_id": crisis_id,
                "status": "Rejected by Officer",
            })

            if report:
                report.approval_status = "REJECTED"
                report.approval_time = datetime.utcnow()
                session.add(report)
                session.commit()

            response.say("Rejected.")

        session.close()
        del pending_decisions[crisis_id]

    return Response(str(response), media_type="text/xml")


# =============================
# NOTIFY & LOG
# =============================

def notify_and_log(crisis_id, crisis_type, location):

    record_event("CALLING_FOR_HELP", {
        "crisis_id": crisis_id,
        "crisis_type": crisis_type,
        "location": location,
        "status": "Notifying emergency response teams"
    })

    orchestrate_response(crisis_type, location, 25)

    session = SessionLocal()
    report = session.query(CrisisReport).filter_by(crisis_id=crisis_id).first()

    if report:
        teams = json.loads(report.teams_notified or "[]")
        teams.append({
            "type": crisis_type,
            "location": location,
            "time": datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        })
        report.teams_notified = json.dumps(teams)
        session.add(report)
        session.commit()

    session.close()


# =============================
# REPORT ENDPOINTS
# =============================

@app.get("/audit_log")
async def audit_log_endpoint():
    return get_audit_log()


@app.get("/crisis_report/{crisis_id}")
async def crisis_report(crisis_id: str):

    session = SessionLocal()
    report = session.query(CrisisReport).filter_by(crisis_id=crisis_id).first()
    session.close()

    if not report:
        return {"error": "Not found"}

    return report.to_dict()


@app.get("/all_reports")
async def all_reports():

    session = SessionLocal()
    reports = session.query(CrisisReport).order_by(
        CrisisReport.submitted_at.desc()
    ).all()
    session.close()

    return [r.to_dict() for r in reports]


@app.get("/crisis_status/{crisis_id}")
async def crisis_status(crisis_id: str):

    session = SessionLocal()
    report = session.query(CrisisReport).filter_by(crisis_id=crisis_id).first()
    session.close()

    if not report:
        return {"status": "NOT_FOUND"}

    return {"status": report.approval_status}


@app.get("/generate_audit_report")
async def generate_audit_report():
    """Generate comprehensive PDF report from all audit log events"""
    try:
        file_path = generate_comprehensive_report()
        if not file_path:
            return {"error": "No audit events to report"}
        
        filename = os.path.basename(file_path)
        return FileResponse(file_path, media_type="application/pdf", filename=filename)
    except Exception as e:
        return {"error": str(e)}



# =============================
# GENERATE COMPREHENSIVE AUDIT REPORT
# =============================

def get_next_report_number():
    """Get the next available report number"""
    workspace_root = "/home/dharshan/autonomous-crisis-command"
    counter = 1
    while os.path.exists(f"{workspace_root}/report_{counter}.pdf"):
        counter += 1
    return counter


def generate_comprehensive_report():
    """Generate a comprehensive PDF report from all audit log events"""
    
    audit_events = get_audit_log()
    
    if not audit_events:
        return None
    
    # Get workspace root
    workspace_root = "/home/dharshan/autonomous-crisis-command"
    report_num = get_next_report_number()
    file_path = f"{workspace_root}/report_{report_num}.pdf"
    
    # Setup PDF
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "title",
        parent=styles["Title"],
        fontSize=20,
        textColor=colors.HexColor("#1a3a52"),
        spaceAfter=20,
        alignment=1
    )
    
    heading_style = ParagraphStyle(
        "customHeading",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#2c5aa0"),
        spaceAfter=12,
        spaceBefore=12
    )
    
    elements = []
    
    # Title
    elements.append(Paragraph("Crisis Incident Report", title_style))
    elements.append(Spacer(1, 10))
    
    # Extract key timestamps from events
    event_timeline = {}
    for event in audit_events:
        event_type = event.get("event_type", "")
        timestamp = event.get("timestamp", "")
        data = event.get("data", {})
        
        event_timeline[event_type] = {
            "timestamp": timestamp,
            "data": data
        }
    
    # Generate timeline section
    elements.append(Paragraph("Event Timeline", heading_style))
    elements.append(Spacer(1, 8))
    
    # Define timeline data from events
    timeline_data = [
        ["Stage", "Time", "Details"],
    ]
    
    # Add events in chronological order with better formatting
    event_order = [
        "CRISIS_RECEIVED",
        "DECISION_MADE",
        "AUTHORIZATION_REQUIRED",
        "APPROVAL_CALL_TRIGGERED",
        "APPROVAL_GRANTED",
        "APPROVAL_REJECTED",
        "CALLING_FOR_HELP",
        "DISPATCH_COMPLETED",
        "DISPATCHING_TEAM",
        "UNIT_DISPATCHED"
    ]
    
    for event_name in event_order:
        if event_name in event_timeline:
            event_info = event_timeline[event_name]
            timestamp = event_info["timestamp"]
            data = event_info["data"]
            
            # Format event details based on type
            details = ""
            if event_name == "CRISIS_RECEIVED":
                crises = data.get("crises", [])
                if crises:
                    crisis = crises[0]
                    type_str = crisis.get("crisis_type", "Unknown")
                    loc = crisis.get("location", "Unknown")
                    sev = crisis.get("severity", "Unknown")
                    details = f"{type_str} at {loc} (Severity: {sev})"
            
            elif event_name == "DECISION_MADE":
                allocated = data.get("allocated", 0)
                delayed = data.get("delayed", 0)
                details = f"Allocated: {allocated}, Delayed: {delayed}"
            
            elif event_name == "AUTHORIZATION_REQUIRED":
                risks = data.get("risks", [])
                if risks:
                    risk = risks[0]
                    details = f"Risk Score: {risk.get('risk_score', 'N/A')} - {risk.get('risk_factor', '')}"
            
            elif event_name == "APPROVAL_CALL_TRIGGERED":
                officer = data.get("officer_number", "N/A")
                details = f"Officer: {officer}"
            
            elif event_name == "APPROVAL_GRANTED":
                details = "✓ Approved by Officer - Units Dispatching"
            
            elif event_name == "APPROVAL_REJECTED":
                details = "✗ Rejected by Officer"
            
            elif event_name == "CALLING_FOR_HELP":
                type_str = data.get("crisis_type", "Unknown")
                location = data.get("location", "Unknown")
                details = f"Notifying teams for {type_str} at {location}"
            
            elif event_name == "DISPATCH_COMPLETED":
                total = data.get("total_units", 0)
                remaining = data.get("remaining_resources", {})
                details = f"Units: {total}, Remaining Resources: {remaining}"
            
            elif event_name == "DISPATCHING_TEAM":
                role = data.get("role", "Unknown")
                number = data.get("number", "N/A")
                details = f"{role} - {number}"
            
            elif event_name == "UNIT_DISPATCHED":
                unit_type = data.get("unit_type", "Unknown")
                destination = data.get("destination", "Unknown")
                risk = data.get("risk_score", "N/A")
                details = f"{unit_type} to {destination} (Risk Score: {risk})"
            
            # Format event name for display
            display_name = event_name.replace("_", " ").title()
            timeline_data.append([display_name, timestamp, details])
    
    # Create timeline table
    if len(timeline_data) > 1:  # More than just header
        timeline_table = Table(timeline_data, colWidths=[1.8*inch, 2.2*inch, 3*inch])
        timeline_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2c5aa0")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f5f5f5")),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#cccccc")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9f9f9")]),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(timeline_table)
    
    elements.append(Spacer(1, 20))
    
    # Summary section
    elements.append(Paragraph("Crisis Summary", heading_style))
    elements.append(Spacer(1, 8))
    
    summary_items = []
    
    if "CRISIS_RECEIVED" in event_timeline:
        crisis_data = event_timeline["CRISIS_RECEIVED"]["data"]
        crises = crisis_data.get("crises", [])
        if crises:
            c = crises[0]
            summary_items.append(f"<b>Crisis Type:</b> {c.get('crisis_type', 'Unknown')}")
            summary_items.append(f"<b>Location:</b> {c.get('location', 'Unknown')}")
            summary_items.append(f"<b>Severity:</b> {c.get('severity', 'Unknown')}")
            summary_items.append(f"<b>Risk Score:</b> {c.get('risk_score', 'N/A')}")
    
    if "APPROVAL_GRANTED" in event_timeline:
        summary_items.append(f"<b>Status:</b> <font color='green'>✓ Approved</font>")
    elif "APPROVAL_REJECTED" in event_timeline:
        summary_items.append(f"<b>Status:</b> <font color='red'>✗ Rejected</font>")
    else:
        summary_items.append(f"<b>Status:</b> Pending")
    
    for item in summary_items:
        elements.append(Paragraph(item, styles["Normal"]))
        elements.append(Spacer(1, 5))
    
    elements.append(Spacer(1, 15))
    
    # Footer
    footer_text = f"Report Generated: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')} | Report #: {report_num}"
    elements.append(Paragraph(footer_text, ParagraphStyle(
        "footer",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.grey,
        alignment=1
    )))
    
    # Build PDF
    doc = SimpleDocTemplate(file_path, pagesize=letter)
    doc.build(elements)
    
    return file_path


# =============================
# PDF DOWNLOAD
# =============================

@app.get("/download_report/{crisis_id}")
async def download_report(crisis_id: str):

    session = SessionLocal()
    report_obj = session.query(CrisisReport).filter_by(crisis_id=crisis_id).first()
    session.close()

    if not report_obj:
        return {"error": "Report not found"}

    report = report_obj.to_dict()
    report_id = report.get("id", crisis_id)
    file_path = f"/home/dharshan/autonomous-crisis-command/report_{report_id}.pdf"

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Title"], alignment=1)

    elements = []
    elements.append(Paragraph("Autonomous Crisis Command Report", title_style))
    elements.append(Spacer(1, 20))

    # Helper function to format timestamp
    def format_ts(ts):
        if not ts: return "N/A"
        try:
            return datetime.fromisoformat(ts).strftime("%Y-%m-%d %I:%M:%S %p")
        except:
            return ts

    incident_time = format_ts(report.get('submitted_at'))
    approval_time = format_ts(report.get('approval_time'))
    dispatch_time = format_ts(report.get('dispatch_time'))
    
    # We assume 'call for approval time' happens right at submitted_at realistically, since 
    # it's just the time we trigger the call. For clarity on the report we'll note it as slightly after.
    
    # Define table structure
    data = [
        ["Event", "Time", "Details"],
        ["Incident Reported", incident_time, f"Crisis ID: {report.get('crisis_id')}"],
        ["Call for Approval", incident_time, "Called commanding officer"],
        ["Approval Status", approval_time, f"Status: {report.get('approval_status')}"],
        ["Call for Help", dispatch_time, "Triggered notifications to dispatch teams"]
    ]

    table = Table(data, colWidths=[2*inch, 2.5*inch, 3*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 20))

    if report.get("teams_notified"):
        elements.append(Paragraph("Teams Notified & Dispatched:", styles["Heading2"]))
        for team in report.get("teams_notified"):
            team_info = f"- {team.get('type')} Unit to {team.get('location')} (Contacted at {team.get('time')})"
            elements.append(Paragraph(team_info, styles["Normal"]))
            elements.append(Spacer(1, 5))

    doc = SimpleDocTemplate(file_path, pagesize=letter)
    doc.build(elements)

    return FileResponse(file_path, media_type="application/pdf", filename=file_path)


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)