def execute_dispatch(decision_output: dict) -> dict:
    """
    Execute dispatch operations based on conflict resolution decisions.
    
    Args:
        decision_output: Output dictionary from resolve_conflicts() containing:
            - "decisions": List of allocated crises ready for dispatch
            - "tradeoffs": List of delayed crises (not processed by this function)
            - "remaining_resources": Resource counts after allocation
    
    Returns:
        Dictionary containing:
            - "execution_status": Either "COMPLETED" if dispatches were made, 
                                 or "NO_ACTION" if no decisions exist
            - "dispatch_log": List of dispatch log entries with unit_type, destination, 
                             status, and risk_score
    
    Example:
        decision_output = {
            "decisions": [
                {
                    "crisis_type": "Fire",
                    "location": "Downtown",
                    "risk_score": 4.5,
                    "status": "allocated"
                }
            ],
            "tradeoffs": [],
            "remaining_resources": {"Fire": 0, "Flood": 1}
        }
        
        Returns:
        {
            "execution_status": "COMPLETED",
            "dispatch_log": [
                {
                    "unit_type": "Fire",
                    "destination": "Downtown",
                    "status": "Dispatched",
                    "risk_score": 4.5
                }
            ]
        }
    """
    decisions = decision_output.get("decisions", [])
    
    # If no decisions, return NO_ACTION
    if not decisions:
        return {
            "execution_status": "NO_ACTION",
            "dispatch_log": []
        }
    
    # Create dispatch log entries
    dispatch_log = []
    
    for decision in decisions:
        dispatch_entry = {
            "unit_type": decision.get("crisis_type"),
            "destination": decision.get("location"),
            "status": "Dispatched",
            "risk_score": decision.get("risk_score")
        }
        dispatch_log.append(dispatch_entry)
    
    return {
        "execution_status": "COMPLETED",
        "dispatch_log": dispatch_log
    }
