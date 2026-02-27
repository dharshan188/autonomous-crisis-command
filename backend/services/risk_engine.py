def calculate_risk(crisis: dict) -> float:
    """
    Calculates numerical risk score based on severity and context.
    """

    severity = crisis.get("severity", "").lower()
    crisis_type = crisis.get("crisis_type", "").lower()
    risk_factor = crisis.get("risk_factor", "").lower()

    risk_score = 0.0

    # --------------------------------
    # Base severity scoring
    # --------------------------------
    if severity in ["low"]:
        risk_score += 1.0
    elif severity in ["medium", "moderate"]:
        risk_score += 3.0
    elif severity in ["high", "major", "severe", "critical"]:
        risk_score += 5.0
    else:
        risk_score += 2.0  # default fallback

    # --------------------------------
    # Crisis type weight
    # --------------------------------
    if crisis_type in ["fire", "industrial accident", "gas leak"]:
        risk_score += 1.0
    elif crisis_type in ["earthquake"]:
        risk_score += 2.0

    # --------------------------------
    # High danger keywords
    # --------------------------------
    danger_keywords = [
        "fuel",
        "chemical",
        "refinery",
        "radiation",
        "explosion",
        "casualties",
        "toxic",
        "nuclear"
    ]

    for word in danger_keywords:
        if word in risk_factor:
            risk_score += 1.5

    return round(risk_score, 1)