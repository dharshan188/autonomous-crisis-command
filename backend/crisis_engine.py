import json
from ai_model import CrisisModel
from services.risk_engine import calculate_risk
from services.resolver import resolve_conflicts
from services.dispatcher import execute_dispatch
from services.surveillance import surveillance_monitor
from services.audit import record_event
from services.nearby_services import find_nearby_services


class CrisisEngine:
    """
    Crisis management engine that orchestrates
    extraction → risk scoring → allocation → approval → execution
    """

    def __init__(self, crisis_model: CrisisModel):
        self.model = crisis_model

        self.resource_pool = {
            "Fire": 2,
            "Flood": 2,
            "Gas Leak": 1,
            "Accident": 2,
            "Earthquake": 1
        }

    # -------------------------
    # Crisis Type Normalization
    # -------------------------

    def normalize_type(self, crisis_type: str) -> str:

        if not crisis_type:
            return "Unknown"

        ctype = crisis_type.lower()

        if "fire" in ctype:
            return "Fire"
        if "flood" in ctype:
            return "Flood"
        if "gas" in ctype:
            return "Gas Leak"
        if "accident" in ctype:
            return "Accident"
        if "explosion" in ctype:
            return "Accident"
        if "earthquake" in ctype:
            return "Earthquake"

        return "Unknown"

    # -------------------------
    # Main Pipeline
    # -------------------------

    def process_crises(self, crisis_texts: list, approved: bool) -> dict:

        crises = []

        # STEP 1: Extract structured crisis
        for text in crisis_texts:

            crisis_data = self.model.extract_crisis(text)

            if not isinstance(crisis_data, dict):
                crisis_data = {
                    "crisis_type": "Unknown",
                    "location": "Unknown",
                    "severity": "Low"
                }

            normalized = self.normalize_type(
                crisis_data.get("crisis_type", "")
            )

            crisis_data["crisis_type"] = normalized

            print("NORMALIZED TYPE:", normalized)

            # STEP 2: Risk scoring
            crisis_data["risk_score"] = calculate_risk(crisis_data)

            # ------------------------------------------------
            # 🔥 STEP 3: SAFE Nearby Lookup (DO NOT BREAK FLOW)
            # ------------------------------------------------
            try:
                if crisis_data.get("location") and crisis_data["location"] != "Unknown":
                    nearby = find_nearby_services(crisis_data["location"])
                    crisis_data["nearby_units"] = nearby
                else:
                    crisis_data["nearby_units"] = []
            except Exception as e:
                print("NEARBY LOOKUP ERROR:", str(e))
                crisis_data["nearby_units"] = []

            crises.append(crisis_data)

        print("PROCESSED CRISES:", crises)

        # STEP 4: Audit
        record_event("CRISIS_RECEIVED", {
            "count": len(crises),
            "crises": crises
        })

        # STEP 5: Resource Allocation
        decision_output = resolve_conflicts(crises, self.resource_pool)

        print("DECISION OUTPUT:", decision_output)

        record_event("DECISION_MADE", {
            "allocated": len(decision_output["decisions"]),
            "delayed": len(decision_output["tradeoffs"])
        })

        # ---------------------------------
        # STEP 6: Approval Check
        # ---------------------------------

        if not decision_output["decisions"]:
            return {
                "status": "NO_RESOURCES",
                "details": decision_output["tradeoffs"]
            }

        approval_required_cases = [
            d for d in decision_output["decisions"]
            if d.get("risk_score", 0) >= 1
        ]

        if approval_required_cases and not approved:

            record_event("AUTHORIZATION_REQUIRED", {
                "approval_required_count": len(approval_required_cases),
                "cases": approval_required_cases
            })

            return {
                "status": "PENDING_APPROVAL",
                "details": approval_required_cases,
                "decision_output": decision_output
            }

        # ---------------------------------
        # STEP 7: Execute
        # ---------------------------------

        execution_result = execute_dispatch(decision_output)
        alerts = surveillance_monitor(decision_output)

        record_event("EXECUTION_COMPLETED", {
            "execution_status": execution_result["execution_status"],
            "dispatch_count": len(execution_result["dispatch_log"]),
            "alert_count": len(alerts)
        })

        return {
            "status": "EXECUTED",
            "execution_result": execution_result,
            "alerts": alerts
        }