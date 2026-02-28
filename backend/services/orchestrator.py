import os
import threading
import traceback

from dotenv import load_dotenv
from twilio.rest import Client

# load env variables as soon as module is imported
load_dotenv()

# Twilio configuration pulled from environment
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")

# initialize client lazily
_twilio_client = None

def _get_twilio_client():
    global _twilio_client
    if _twilio_client is None:
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
            raise RuntimeError("Twilio credentials are not set in environment")
        _twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    return _twilio_client

# registry mapping crisis types to contact numbers
# consumers can import and modify if needed
RESOURCE_REGISTRY = {
    # example: "fire": "+15551234567",
}


def call_resource(number: str, message: str) -> None:
    """Place a phone call to the given number with a simple voice message.

    Any exception is caught and logged so callers can continue executing.
    """
    try:
        print(f"[orchestrator] initiating call to {number}")
        client = _get_twilio_client()
        # create a call that speaks the message
        client.calls.create(
            to=number,
            from_=TWILIO_FROM_NUMBER,
            twiml=f"<Response><Say>{message}</Say></Response>",
        )
    except Exception:
        print(f"[orchestrator] call_resource failed for {number}")
        traceback.print_exc()


def sms_resource(number: str, message: str) -> None:
    """Send an SMS to the given number with the provided message.

    Exceptions are quietly logged.
    """
    try:
        print(f"[orchestrator] sending sms to {number}")
        client = _get_twilio_client()
        client.messages.create(
            to=number,
            from_=TWILIO_FROM_NUMBER,
            body=message,
        )
    except Exception:
        print(f"[orchestrator] sms_resource failed for {number}")
        traceback.print_exc()


def orchestrate_response(crisis_type: str, message: str) -> None:
    """Look up the resource for the given crisis and alert it via call+sms.

    The calls are executed in parallel threads; any internal error is
    logged and does not propagate.
    """
    number = RESOURCE_REGISTRY.get(crisis_type)
    if not number:
        print(f"[orchestrator] no resource registered for crisis '{crisis_type}'")
        return

    # start threads for call and sms
    threads = []
    t1 = threading.Thread(target=call_resource, args=(number, message), daemon=True)
    threads.append(t1)
    t2 = threading.Thread(target=sms_resource, args=(number, message), daemon=True)
    threads.append(t2)

    for t in threads:
        t.start()

    # we don't join because we don't want to block caller; they run in background


# optional: convenience for registering resources

def register_resource(crisis_type: str, phone_number: str) -> None:
    """Add or update an entry in the registry."""
    RESOURCE_REGISTRY[crisis_type] = phone_number


if __name__ == "__main__":
    # simple manual test
    register_resource("test", os.getenv("TEST_NUMBER", "+15550001111"))
    orchestrate_response("test", "This is a test crisis message.")
