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
# ROLE-BASED RESOURCE REGISTRY
# ---------------------------------------------------

RESOURCE_REGISTRY = {
    "Fire": [
        {
            "role": "Firefighter Team",
            "number": "+919363948181"
        },
        {
            "role": "Ambulance Team",
            "number": "+917397074365"
        }
    ],
    "Flood": [
        {
            "role": "Flood Medical Team",
            "number": "+917904657955"
        },
        {
            "role": "Disaster Response Team",
            "number": "+919043275000"
        }
    ]
}


# ---------------------------------------------------
# APPROVAL CALL
# ---------------------------------------------------

def trigger_approval_call(to_number: str, public_url: str, crisis_id: str) -> str:
    """
    Triggers Twilio voice approval call.
    """

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
# TEAM MESSAGE GENERATOR
# ---------------------------------------------------

def generate_team_message(crisis_type, role, location, people_count=None):

    if crisis_type == "Fire":

        if role == "Firefighter Team":
            return (
                f"Emergency fire alert at {location}. "
                "Deploy fire suppression units immediately."
            )

        if role == "Ambulance Team":
            return (
                f"Medical emergency due to fire at {location}. "
                "Prepare trauma kits and proceed immediately."
            )

    if crisis_type == "Flood":

        if role == "Flood Medical Team":
            return (
                f"Flood emergency at {location}. "
                f"Approximately {people_count or 'multiple'} people affected. "
                "Prepare emergency medical kits and respond immediately."
            )

        if role == "Disaster Response Team":
            return (
                f"Severe flood reported at {location}. "
                f"{people_count or 'Multiple'} civilians stranded. "
                "Deploy rescue equipment and evacuation gear immediately."
            )

    return f"Emergency reported at {location}. Immediate action required."


# ---------------------------------------------------
# CALL + SMS TO SINGLE RESOURCE
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
        print(f"[ERROR] Call failed for {number}")
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
        print(f"[ERROR] SMS failed for {number}")
        traceback.print_exc()


# ---------------------------------------------------
# ORCHESTRATE MULTI-TEAM RESPONSE
# ---------------------------------------------------

def orchestrate_response(crisis_type: str, location: str, people_count=None):
    """
    Notify ALL registered resources for a crisis.
    Calls + SMS sent in parallel threads.
    """

    resources = RESOURCE_REGISTRY.get(crisis_type)

    if not resources:
        print("No registered resources for:", crisis_type)
        return

    threads = []

    for resource in resources:

        role = resource["role"]
        number = resource["number"]
        
        record_event("DISPATCHING_TEAM", {
            "crisis_type": crisis_type,
            "location": location,
            "role": role,
            "number": number,
            "action": "Sending SMS and Voice Call"
        })

        message = generate_team_message(
            crisis_type,
            role,
            location,
            people_count
        )

        # Call thread
        t_call = threading.Thread(
            target=call_resource,
            args=(number, message),
            daemon=True
        )
        threads.append(t_call)

        # SMS thread
        t_sms = threading.Thread(
            target=sms_resource,
            args=(number, message),
            daemon=True
        )
        threads.append(t_sms)

    for t in threads:
        t.start()

    print(f"Orchestration triggered for {crisis_type} at {location}")