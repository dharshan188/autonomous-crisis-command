import os
import requests
import json
import re
from dotenv import load_dotenv

load_dotenv()


class CrisisModel:
    def __init__(self):
        self.model_name = "google/flan-t5-large"
        self.endpoint = f"https://api-inference.huggingface.co/models/{self.model_name}"
        self.token = os.environ.get("HF_API_TOKEN")

        if not self.token:
            raise EnvironmentError("HF_API_TOKEN not set in environment")

    def extract_crisis(self, text: str) -> dict:
        prompt = f"""
You are a disaster intelligence parser.

Return STRICT JSON only.
No explanation.
No extra text.
Do not repeat the prompt.

Allowed crisis types:
Fire, Flood, Gas Leak, Accident, Earthquake, Other

Allowed severity:
Low, Medium, High, Critical

Format exactly like this:
{{
  "crisis_type": "",
  "location": "",
  "severity": "",
  "risk_factor": ""
}}

Text:
{text}

JSON:
"""

        headers = {
            "Authorization": f"Bearer {self.token}"
        }

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 120,
                "temperature": 0.1
            }
        }

        try:
            resp = requests.post(self.endpoint, headers=headers, json=payload)
            resp.raise_for_status()

            data = resp.json()
            print("HF FULL RESPONSE:", data)

            # Extract raw text from HF response
            if isinstance(data, list) and data:
                raw_text = data[0].get("generated_text", "")
            elif isinstance(data, dict):
                raw_text = data.get("generated_text", "")
            else:
                print("HF unexpected format")
                return {}

            print("HF RAW TEXT:", raw_text)

            # Extract first JSON object from text
            match = re.search(r"\{.*?\}", raw_text, re.DOTALL)
            if match:
                json_str = match.group(0)
                parsed = json.loads(json_str)
                print("PARSED JSON:", parsed)
                return parsed

            print("No JSON found in response")
            return {}

        except Exception as e:
            print("HF ERROR:", e)
            return {}