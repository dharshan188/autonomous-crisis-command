# backend/services/voice_service.py

from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")

twilio_client = Client(TWILIO_SID, TWILIO_AUTH)


def trigger_approval_call(to_number: str, public_url: str, crisis_id: str) -> str:
    """
    Triggers Twilio voice approval call.

    Args:
        to_number: Officer phone number
        public_url: Public ngrok URL
        crisis_id: Unique crisis ID

    Returns:
        Twilio Call SID
    """

    if not public_url.startswith("https://"):
        raise ValueError("PUBLIC_URL must be HTTPS (ngrok URL)")

    voice_url = f"{public_url}/voice?crisis_id={crisis_id}"

    print("TRIGGERING CALL TO:", to_number)
    print("VOICE URL:", voice_url)

    call = twilio_client.calls.create(
        url=voice_url,
        to=to_number,
        from_=TWILIO_NUMBER
    )

    print("CALL SID:", call.sid)

    return call.sid