from datetime import datetime
import threading

# Global in-memory audit log
audit_log = []
# Thread-safe lock for concurrent access
audit_lock = threading.Lock()


def record_event(event_type: str, data: dict) -> None:
    """
    Record an event to the audit log in a thread-safe manner.
    
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
    with audit_lock:  # Acquire lock before modifying shared state
        event_record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),
            "event_type": event_type,
            "data": data
        }
        audit_log.append(event_record)


def get_audit_log() -> list:
    """
    Retrieve the complete audit log in a thread-safe manner.
    
    Returns:
        List of audit log entries, each containing timestamp, event_type, and data.
    
    Example:
        log = get_audit_log()
        for entry in log:
            print(f"{entry['timestamp']} - {entry['event_type']}")
    """
    with audit_lock:  # Acquire lock before reading shared state
        return [entry.copy() for entry in audit_log]  # Return a copy to prevent external modifications
