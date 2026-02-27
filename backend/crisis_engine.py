import json
from ai_model import CrisisModel
from services.risk_engine import calculate_risk
from services.resolver import resolve_conflicts
from services.dispatcher import execute_dispatch
from services.surveillance import surveillance_monitor
from services.audit import record_event


class CrisisEngine:
    """
    Crisis management engine that orchestrates the entire crisis response pipeline.
    """

    def __init__(self, crisis_model: CrisisModel):
        self.model = crisis_model

        # Default resource pool
        self.resource_pool = {
            "Fire": 2,
            "Flood": 2,
            "Gas Leak": 1,
            "Accident": 2,
            "Earthquake": 1
        }

    # ------------------------------------------------------------------
    # Resource type normalization
    # ------------------------------------------------------------------
    def _normalize_resource_type(self, crisis_type: str) -> str:
        """Map various crisis descriptions to the canonical type used
        by the resource pool. This runs *after* the model-level
        normalization to catch synonyms that the AI might produce.

        The mapping is intentionally conservative and production-safe.
        """
        if not crisis_type:
            return "Unknown"

        text = crisis_type.strip().lower()
        mapping = {
            "industrial accident": "Accident",
            "road accident": "Accident",
            # explosion is often reported separately but we treat it as fire
            "explosion": "Fire",
        }
        return mapping.get(text, crisis_type.title())

    def process_crises(self, crisis_texts: list, approved: bool) -> dict:
        crises = []

        # -----------------------------------------
        # STEP 1: Extract structured crisis data
        # -----------------------------------------
        for text in crisis_texts:
            crisis_data = self.model.extract_crisis(text)

            # Safety fallback if model fails
            if not isinstance(crisis_data, dict):
                crisis_data = {
                    "crisis_type": "Unknown",
                    "location": "Unknown",
                    "severity": "Low"
                }

            # normalize type for allocation & auditing
            normalized = self._normalize_resource_type(crisis_data.get("crisis_type", ""))
            print("NORMALIZED TYPE:", normalized)
            crisis_data["crisis_type"] = normalized

            # STEP 2: Calculate risk
            crisis_data["risk_score"] = calculate_risk(crisis_data)

            crises.append(crisis_data)

        print("PROCESSED CRISES:", crises)

        # -----------------------------------------
        # STEP 3: Audit log
        # -----------------------------------------
        record_event("CRISIS_RECEIVED", {
            "count": len(crises),
            "crises": crises
        })

        # -----------------------------------------
        # STEP 4: Resolve resource conflicts
        # -----------------------------------------
        decision_output = resolve_conflicts(crises, self.resource_pool)
        print("DECISION OUTPUT:", decision_output)

        record_event("DECISION_MADE", {
            "allocated": len(decision_output["decisions"]),
            "delayed": len(decision_output["tradeoffs"])
        })

        # -----------------------------------------
        # STEP 5: Check high-risk approval
        # -----------------------------------------
        high_risk_cases = [
            d for d in decision_output["decisions"]
            if d.get("risk_score", 0) >= 4
        ]

        if high_risk_cases and not approved:
            record_event("AUTHORIZATION_REQUIRED", {
                "high_risk_count": len(high_risk_cases),
                "risks": high_risk_cases
            })

            # include full decision_output in the response so that the caller
            # can execute dispatch with the complete allocation context later
            return {
                "status": "PENDING_APPROVAL",
                "details": high_risk_cases,
                "decision_output": decision_output
            }

        # -----------------------------------------
        # STEP 6: Execute dispatch
        # -----------------------------------------
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