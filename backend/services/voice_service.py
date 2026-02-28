from twilio.rest import Client
import os
import threading
import traceback
from dotenv import load_dotenv
from services.audit import record_event

load_dotenv()

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")

twilio_client = Client(TWILIO_SID, TWILIO_AUTH)

# ---------------------------------------------------
# ROLE-BASED RESOURCE REGISTRY (EXPANDED)
# ---------------------------------------------------

RESOURCE_REGISTRY = {

    "Fire": [
        {"role": "Firefighter Team", "number": "+919363948181"},
        {"role": "Ambulance Team", "number": "+917397074365"}
    ],

    "Flood": [
        {"role": "Flood Medical Team", "number": "+917904657955"},
        {"role": "Disaster Response Team", "number": "+919043275000"}
    ],

    "Accident": [
        {"role": "Traffic Police", "number": "+919363948181"},
        {"role": "Ambulance Team", "number": "+917397074365"}
    ],

    "Gas Leak": [
        {"role": "Hazmat Team", "number": "+919363948181"},
        {"role": "Ambulance Team", "number": "+917397074365"}
    ],

    "Earthquake": [
        {"role": "Search & Rescue Team", "number": "+919043275000"},
        {"role": "Ambulance Team", "number": "+917397074365"}
    ]
}

# ---------------------------------------------------
# APPROVAL CALL
# ---------------------------------------------------

def trigger_approval_call(to_number: str, public_url: str, crisis_id: str) -> str:

    if not public_url.startswith("https://"):
        raise ValueError("PUBLIC_URL must be HTTPS (ngrok URL)")

    voice_url = f"{public_url}/voice?crisis_id={crisis_id}&ngrok-skip-browser-warning=true"

    print("TRIGGERING APPROVAL CALL TO:", to_number)
    print("VOICE URL:", voice_url)

    call = twilio_client.calls.create(
        url=voice_url,
        to=to_number,
        from_=TWILIO_NUMBER
    )

    print("APPROVAL CALL SID:", call.sid)

    return call.sid

# ---------------------------------------------------
# MESSAGE GENERATOR
# ---------------------------------------------------

def generate_team_message(crisis_type, role, location, people_count=None):

    crisis_type = crisis_type.strip()

    if crisis_type == "Fire":
        return f"Fire emergency at {location}. Immediate response required."

    if crisis_type == "Flood":
        return f"Flood emergency at {location}. Rescue and medical teams required."

    if crisis_type == "Accident":
        return f"Road accident reported at {location}. Emergency medical assistance required."

    if crisis_type == "Gas Leak":
        return f"Gas leak detected at {location}. Hazmat response required immediately."

    if crisis_type == "Earthquake":
        return f"Earthquake impact reported at {location}. Search and rescue teams required."

    return f"Emergency reported at {location}. Immediate action required."

# ---------------------------------------------------
# CALL + SMS
# ---------------------------------------------------

def call_resource(number: str, message: str):
    try:
        print(f"[CALL] -> {number}")
        twilio_client.calls.create(
            twiml=f"<Response><Say>{message}</Say></Response>",
            to=number,
            from_=TWILIO_NUMBER
        )
    except Exception:
        traceback.print_exc()

def sms_resource(number: str, message: str):
    try:
        print(f"[SMS] -> {number}")
        twilio_client.messages.create(
            body=message,
            to=number,
            from_=TWILIO_NUMBER
        )
    except Exception:
        traceback.print_exc()

# ---------------------------------------------------
# ORCHESTRATOR
# ---------------------------------------------------

def orchestrate_response(crisis_type: str, location: str, people_count=None):

    crisis_type = crisis_type.strip()

    resources = RESOURCE_REGISTRY.get(crisis_type)

    if not resources:
        print("No registered resources for:", crisis_type)
        record_event("NO_RESOURCE_FOUND", {
            "crisis_type": crisis_type
        })
        return

    threads = []

    for resource in resources:

        role = resource["role"]
        number = resource["number"]

        record_event("DISPATCHING_TEAM", {
            "crisis_type": crisis_type,
            "location": location,
            "role": role,
            "number": number
        })

        message = generate_team_message(
            crisis_type,
            role,
            location,
            people_count
        )

        t_call = threading.Thread(
            target=call_resource,
            args=(number, message),
            daemon=True
        )
        threads.append(t_call)

        t_sms = threading.Thread(
            target=sms_resource,
            args=(number, message),
            daemon=True
        )
        threads.append(t_sms)

    for t in threads:
        t.start()

    print(f"Orchestration triggered for {crisis_type} at {location}") 