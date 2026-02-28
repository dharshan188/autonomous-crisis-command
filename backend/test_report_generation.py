#!/usr/bin/env python3
"""
Test script to simulate a fire crisis scenario and generate comprehensive report.
This replicates the events shown in the user's log output.
"""

import os
import sys
from datetime import datetime, timedelta

# Import from main app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from services.audit import record_event, get_audit_log

# Import report generator
from generate_report import generate_comprehensive_report


def simulate_fire_crisis():
    """Simulate the fire crisis scenario from the user's example"""
    
    print("🔥 Simulating Fire Crisis in Sector 12...")
    print()
    
    # Base time for all events
    base_time = datetime.now()
    
    # Event 1: Crisis Received
    print("1️⃣  Receiving crisis report...")
    record_event("CRISIS_RECEIVED", {
        "count": 1,
        "crises": [
            {
                "crisis_type": "Fire",
                "location": "Sector 12",
                "severity": "High",
                "risk_factor": "Multiple Injuries, Heavy Smoke",
                "risk_score": 6
            }
        ]
    })
    
    # Event 2: Decision Made
    print("2️⃣  Making allocation decision...")
    record_event("DECISION_MADE", {
        "allocated": 1,
        "delayed": 0
    })
    
    # Event 3: Authorization Required
    print("3️⃣  Authorization required from officer...")
    record_event("AUTHORIZATION_REQUIRED", {
        "high_risk_count": 1,
        "risks": [
            {
                "crisis_type": "Fire",
                "location": "Sector 12",
                "severity": "High",
                "risk_factor": "Multiple Injuries, Heavy Smoke",
                "risk_score": 6,
                "status": "allocated",
                "action": "Allocated resource for Fire"
            }
        ]
    })
    
    # Event 4: Approval Call Triggered
    print("4️⃣  Triggering approval call to officer...")
    record_event("APPROVAL_CALL_TRIGGERED", {
        "crisis_id": "f2a1f160-4637-40c2-bc27-4c8436c7d21c",
        "officer_number": "+918925326955",
        "status": "Calling for approval..."
    })
    
    # Event 5: Approval Granted
    print("5️⃣  Approval granted by officer...")
    record_event("APPROVAL_GRANTED", {
        "crisis_id": "f2a1f160-4637-40c2-bc27-4c8436c7d21c",
        "status": "Approved by Officer",
        "details": "Units dispatching"
    })
    
    # Event 6: Unit Dispatched
    print("6️⃣  Unit dispatched...")
    record_event("UNIT_DISPATCHED", {
        "unit_type": "Fire",
        "destination": "Sector 12",
        "risk_score": 6
    })
    
    # Event 7: Dispatch Completed
    print("7️⃣  Dispatch completed...")
    record_event("DISPATCH_COMPLETED", {
        "total_units": 1,
        "remaining_resources": {
            "Fire": 1,
            "Flood": 2,
            "Gas Leak": 1,
            "Accident": 2,
            "Earthquake": 1
        }
    })
    
    # Event 8: Calling for Help
    print("8️⃣  Calling for help - notifying teams...")
    record_event("CALLING_FOR_HELP", {
        "crisis_id": "f2a1f160-4637-40c2-bc27-4c8436c7d21c",
        "crisis_type": "Fire",
        "location": "Sector 12",
        "status": "Notifying emergency response teams"
    })
    
    # Event 9: Dispatching Teams (Ambulance)
    print("9️⃣  Dispatching Ambulance Team...")
    record_event("DISPATCHING_TEAM", {
        "crisis_type": "Fire",
        "location": "Sector 12",
        "role": "Ambulance Team",
        "number": "+917397074365",
        "action": "Sending SMS and Voice Call"
    })
    
    # Event 10: Dispatching Teams (Firefighters)
    print("🔟 Dispatching Firefighter Team...")
    record_event("DISPATCHING_TEAM", {
        "crisis_type": "Fire",
        "location": "Sector 12",
        "role": "Firefighter Team",
        "number": "+919363948181",
        "action": "Sending SMS and Voice Call"
    })
    
    print()
    print("✅ All events recorded successfully!")
    print()


def show_audit_log():
    """Display the complete audit log"""
    events = get_audit_log()
    print("📋 Complete Audit Log:")
    print("=" * 80)
    for event in events:
        print(f"{event['timestamp']} - {event['event_type']}")
        print(f"   Data: {event['data']}")
    print("=" * 80)
    print()


if __name__ == "__main__":
    print("\n" + "="*80)
    print("AUTONOMOUS CRISIS COMMAND - TEST SCENARIO")
    print("="*80 + "\n")
    
    # Simulate the crisis
    simulate_fire_crisis()
    
    # Show audit log
    show_audit_log()
    
    # Generate report
    print("📄 Generating comprehensive report...")
    result = generate_comprehensive_report()
    
    if result:
        file_path, report_num = result
        print(f"✅ Report generated successfully!")
        print(f"📊 Saved as: report_{report_num}.pdf")
        print(f"📁 Location: /home/dharshan/autonomous-crisis-command/")
        print()
        print("You can now view the PDF report!")
    else:
        print("❌ Failed to generate report")
        sys.exit(1)
