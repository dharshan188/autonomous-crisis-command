"""
Dispatcher Service
Responsible for executing approved crisis dispatch decisions.
"""

from typing import Dict, List
from services.audit import record_event


def execute_dispatch(decision_output: Dict) -> Dict:
    """
    Execute dispatch operations based on conflict resolution decisions.

    Args:
        decision_output: Output dictionary from resolve_conflicts() containing:
            - "decisions": List of allocated crises ready for dispatch
            - "tradeoffs": List of delayed crises
            - "remaining_resources": Resource counts after allocation

    Returns:
        Dictionary containing:
            - "execution_status": "COMPLETED" or "NO_ACTION"
            - "dispatch_log": List of dispatch records
    """

    if not decision_output or not isinstance(decision_output, dict):
        return {
            "execution_status": "NO_ACTION",
            "dispatch_log": []
        }

    decisions: List[Dict] = decision_output.get("decisions", [])

    # If no decisions available
    if not decisions:
        record_event("DISPATCH_SKIPPED", {"reason": "No allocated decisions"})
        return {
            "execution_status": "NO_ACTION",
            "dispatch_log": []
        }

    dispatch_log = []

    for decision in decisions:

        unit_type = decision.get("crisis_type", "Unknown")
        location = decision.get("location", "Unknown")
        risk_score = decision.get("risk_score", 0)

        dispatch_entry = {
            "unit_type": unit_type,
            "destination": location,
            "status": "Dispatched",
            "risk_score": risk_score
        }

        dispatch_log.append(dispatch_entry)

        # 🔥 Audit each dispatch
        record_event(
            "UNIT_DISPATCHED",
            {
                "unit_type": unit_type,
                "destination": location,
                "risk_score": risk_score
            }
        )

    # 🔥 Log overall execution
    record_event(
        "DISPATCH_COMPLETED",
        {
            "total_units": len(dispatch_log),
            "remaining_resources": decision_output.get("remaining_resources", {})
        }
    )

    return {
        "execution_status": "COMPLETED",
        "dispatch_log": dispatch_log
    }