from datetime import datetime

# Global in-memory audit log
audit_log = []


def record_event(event_type: str, data: dict) -> None:
    """
    Record an event to the audit log.
    
    Args:
        event_type: Type of event being logged (e.g., "CRISIS_DETECTED", "DISPATCH_EXECUTED")
        data: Dictionary containing event-specific data
    
    Example:
        record_event("CRISIS_DETECTED", {
            "crisis_type": "Fire",
            "location": "Downtown",
            "risk_score": 4.5
        })
    """
    event_record = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "data": data
    }
    audit_log.append(event_record)


def get_audit_log() -> list:
    """
    Retrieve the complete audit log.
    
    Returns:
        List of audit log entries, each containing timestamp, event_type, and data.
    
    Example:
        log = get_audit_log()
        for entry in log:
            print(f"{entry['timestamp']} - {entry['event_type']}")
    """
    return audit_log
