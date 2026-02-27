from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

account_sid = os.getenv("TWILIO_SID")
auth_token = os.getenv("TWILIO_AUTH")
twilio_number = os.getenv("TWILIO_NUMBER")

client = Client(account_sid, auth_token)


def trigger_approval_call(to_number, public_url):
    call = client.calls.create(
        url=f"{public_url}/voice",
        to=to_number,
        from_=twilio_number
    )
    return call.sid