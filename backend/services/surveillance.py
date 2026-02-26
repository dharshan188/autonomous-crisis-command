def surveillance_monitor(decision_output: dict) -> list:
    """
    Monitor allocated crises for high-risk situations requiring special attention.
    
    Args:
        decision_output: Output dictionary from resolve_conflicts() containing:
            - "decisions": List of allocated crises with risk_score
            - "tradeoffs": List of delayed crises
            - "remaining_resources": Resource counts after allocation
    
    Returns:
        List of alert dictionaries for high-risk crises (risk_score >= 4).
        Each alert contains:
            - message: "High Risk Ongoing"
            - location: Crisis location
            - crisis_type: Type of crisis
            - risk_score: The risk score that triggered the alert
        
        Returns empty list if no high-risk decisions exist.
    
    Example:
        decision_output = {
            "decisions": [
                {
                    "crisis_type": "Earthquake",
                    "location": "Downtown",
                    "risk_score": 5.2,
                    "status": "allocated"
                },
                {
                    "crisis_type": "Fire",
                    "location": "Suburb",
                    "risk_score": 3.5,
                    "status": "allocated"
                }
            ],
            "tradeoffs": [],
            "remaining_resources": {}
        }
        
        Returns:
        [
            {
                "message": "High Risk Ongoing",
                "location": "Downtown",
                "crisis_type": "Earthquake",
                "risk_score": 5.2
            }
        ]
    """
    alerts = []
    decisions = decision_output.get("decisions", [])
    
    # Check each decision for high-risk situations
    for decision in decisions:
        risk_score = decision.get("risk_score", 0)
        
        # Alert if risk_score >= 4
        if risk_score >= 4:
            alert = {
                "message": "High Risk Ongoing",
                "location": decision.get("location"),
                "crisis_type": decision.get("crisis_type"),
                "risk_score": risk_score
            }
            alerts.append(alert)
    
    return alerts
