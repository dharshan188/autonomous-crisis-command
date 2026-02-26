def calculate_risk(crisis: dict) -> float:
    """
    Calculate risk score based on crisis type and severity.
    
    Args:
        crisis: Dictionary containing:
            - crisis_type (str): Type of crisis (Fire, Flood, Gas Leak, Accident, Earthquake, etc.)
            - severity (str): Severity level (Low, Medium, High, Critical)
    
    Returns:
        float: Risk score rounded to 2 decimal places
        
    Example:
        calculate_risk({"crisis_type": "Fire", "severity": "High"})
        Returns: 4.5 (3 * 1.5)
    """
    # Severity mapping
    severity_mapping = {
        "Low": 1,
        "Medium": 2,
        "High": 3,
        "Critical": 4
    }
    
    # Crisis type multipliers
    crisis_multipliers = {
        "Fire": 1.5,
        "Flood": 1.3,
        "Gas Leak": 1.7,
        "Accident": 1.2,
        "Earthquake": 2.0
    }
    
    # Extract and validate severity
    severity = crisis.get("severity", "Low")
    severity_value = severity_mapping.get(severity, 1)
    
    # Extract and validate crisis type
    crisis_type = crisis.get("crisis_type", "Unknown")
    multiplier = crisis_multipliers.get(crisis_type, 1.0)
    
    # Calculate risk score
    risk_score = severity_value * multiplier
    
    # Round to 2 decimal places
    return round(risk_score, 2)
