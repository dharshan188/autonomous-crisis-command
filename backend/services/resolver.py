def resolve_conflicts(crisis_list: list, resources: dict) -> dict:
    """
    Resolve resource allocation conflicts by prioritizing crises by risk score.
    
    Args:
        crisis_list: List of crisis dictionaries, each containing:
            - crisis_type (str): Type of crisis
            - risk_score (float): Calculated risk score for prioritization
            - Other crisis details
        resources: Dictionary mapping crisis types to available resource counts
                   e.g., {"Fire": 5, "Flood": 3, "Earthquake": 2}
    
    Returns:
        Dictionary containing:
            - "decisions": List of crises with allocated resources
            - "tradeoffs": List of crises delayed due to insufficient resources
            - "remaining_resources": Updated resource counts after allocation
    
    Example:
        crisis_list = [
            {"crisis_type": "Fire", "risk_score": 4.5, "location": "Downtown"},
            {"crisis_type": "Flood", "risk_score": 2.6, "location": "Riverside"}
        ]
        resources = {"Fire": 1, "Flood": 1}
        
        Result will allocate Fire team to the Fire crisis and Flood team to the Flood crisis.
    """
    # Create a copy of resources to avoid modifying the original
    remaining_resources = resources.copy()
    
    # Sort crises by risk_score in descending order
    sorted_crises = sorted(crisis_list, key=lambda x: x.get("risk_score", 0), reverse=True)
    
    decisions = []
    tradeoffs = []
    
    # Process each crisis in priority order
    for crisis in sorted_crises:
        crisis_type = crisis.get("crisis_type")
        
        # Check if resources are available for this crisis type
        if crisis_type in remaining_resources and remaining_resources[crisis_type] > 0:
            # Allocate resource
            remaining_resources[crisis_type] -= 1
            decisions.append({
                **crisis,
                "status": "allocated",
                "action": f"Allocated resource for {crisis_type}"
            })
        else:
            # No resources available, mark as delayed
            tradeoffs.append({
                **crisis,
                "status": "delayed",
                "reason": f"No resources available for {crisis_type}"
            })
    
    return {
        "decisions": decisions,
        "tradeoffs": tradeoffs,
        "remaining_resources": remaining_resources
    }
