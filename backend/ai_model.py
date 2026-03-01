import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class CrisisModel:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found")

        self.client = Groq(api_key=api_key)

    # =====================================================
    # MAIN EXTRACTION
    # =====================================================

    def extract_crisis(self, text: str) -> dict:
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                temperature=0.1,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You extract structured crisis information. "
                            "Always respond with valid JSON only."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"""
Extract crisis details from this text.

Text:
{text}

Return JSON with exactly these fields:
crisis_type, location, severity, risk_factor.
"""
                    },
                ],
            )

            content = response.choices[0].message.content
            print("GROQ RAW:", content)

            data = json.loads(content)

            # -----------------------------
            # SAFE FIELD HANDLING
            # -----------------------------

            crisis_type = data.get("crisis_type") or ""
            location = data.get("location") or "Unknown"
            severity = data.get("severity") or ""
            risk_factor = data.get("risk_factor") or "Not specified"

            cleaned = {
                "crisis_type": self._normalize_type(crisis_type),
                "location": location.strip(),
                "severity": self._normalize_severity(severity),
                "risk_factor": risk_factor.strip(),
            }

            return cleaned

        except Exception as e:
            print("GROQ ERROR:", str(e))
            return self._fallback("Groq request failed")

    # =====================================================
    # HELPERS
    # =====================================================

    def _normalize_severity(self, value: str) -> str:
        value = value.lower()

        if "critical" in value or "very high" in value:
            return "Critical"
        if "high" in value:
            return "High"
        if "medium" in value:
            return "Medium"
        if "low" in value:
            return "Low"

        return "Medium"

    def _normalize_type(self, crisis_type: str) -> str:
        crisis_type = crisis_type.strip().lower()

        mapping = {
            "fire": "Fire",
            "fire accident": "Fire",
            "fire emergency": "Fire",
            "flood": "Flood",
            "flooding": "Flood",
            "gas leak": "Gas Leak",
            "explosion": "Gas Leak",
            "accident": "Accident",
            "earthquake": "Earthquake",
        }

        return mapping.get(crisis_type, crisis_type.title())

    def _fallback(self, reason):
        return {
            "crisis_type": "Unknown",
            "location": "Unknown",
            "severity": "Medium",
            "risk_factor": reason,
        }