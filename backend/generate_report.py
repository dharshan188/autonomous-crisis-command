#!/usr/bin/env python3
"""
Standalone script to generate comprehensive crisis incident reports from audit logs.
Generates PDF reports saved to the workspace root as report_1.pdf, report_2.pdf, etc.
"""

import os
import sys
from datetime import datetime
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

# Import from main app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from services.audit import get_audit_log


def get_next_report_number():
    """Get the next available report number"""
    workspace_root = "/home/dharshan/autonomous-crisis-command"
    counter = 1
    while os.path.exists(f"{workspace_root}/report_{counter}.pdf"):
        counter += 1
    return counter


def generate_comprehensive_report():
    """Generate a comprehensive PDF report from all audit log events"""
    
    audit_events = get_audit_log()
    
    if not audit_events:
        print("❌ No audit events found. Cannot generate report.")
        return None
    
    # Get workspace root
    workspace_root = "/home/dharshan/autonomous-crisis-command"
    report_num = get_next_report_number()
    file_path = f"{workspace_root}/report_{report_num}.pdf"
    
    print(f"📝 Generating report with {len(audit_events)} events...")
    
    # Setup PDF
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "title",
        parent=styles["Title"],
        fontSize=20,
        textColor=colors.HexColor("#1a3a52"),
        spaceAfter=20,
        alignment=1
    )
    
    heading_style = ParagraphStyle(
        "customHeading",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#2c5aa0"),
        spaceAfter=12,
        spaceBefore=12
    )
    
    elements = []
    
    # Title
    elements.append(Paragraph("Crisis Incident Report", title_style))
    elements.append(Spacer(1, 10))
    
    # Extract key timestamps from events
    event_timeline = {}
    for event in audit_events:
        event_type = event.get("event_type", "")
        timestamp = event.get("timestamp", "")
        data = event.get("data", {})
        
        event_timeline[event_type] = {
            "timestamp": timestamp,
            "data": data
        }
    
    # Generate timeline section
    elements.append(Paragraph("Event Timeline", heading_style))
    elements.append(Spacer(1, 8))
    
    # Define timeline data from events
    timeline_data = [
        ["Stage", "Time", "Details"],
    ]
    
    # Add events in chronological order with better formatting
    event_order = [
        "CRISIS_RECEIVED",
        "DECISION_MADE",
        "AUTHORIZATION_REQUIRED",
        "APPROVAL_CALL_TRIGGERED",
        "APPROVAL_GRANTED",
        "APPROVAL_REJECTED",
        "CALLING_FOR_HELP",
        "DISPATCH_COMPLETED",
        "DISPATCHING_TEAM",
        "UNIT_DISPATCHED"
    ]
    
    for event_name in event_order:
        if event_name in event_timeline:
            event_info = event_timeline[event_name]
            timestamp = event_info["timestamp"]
            data = event_info["data"]
            
            # Format event details based on type
            details = ""
            if event_name == "CRISIS_RECEIVED":
                crises = data.get("crises", [])
                if crises:
                    crisis = crises[0]
                    type_str = crisis.get("crisis_type", "Unknown")
                    loc = crisis.get("location", "Unknown")
                    sev = crisis.get("severity", "Unknown")
                    details = f"{type_str} at {loc} (Severity: {sev})"
            
            elif event_name == "DECISION_MADE":
                allocated = data.get("allocated", 0)
                delayed = data.get("delayed", 0)
                details = f"Allocated: {allocated}, Delayed: {delayed}"
            
            elif event_name == "AUTHORIZATION_REQUIRED":
                risks = data.get("risks", [])
                if risks:
                    risk = risks[0]
                    details = f"Risk Score: {risk.get('risk_score', 'N/A')} - {risk.get('risk_factor', '')}"
            
            elif event_name == "APPROVAL_CALL_TRIGGERED":
                officer = data.get("officer_number", "N/A")
                details = f"Officer: {officer}"
            
            elif event_name == "APPROVAL_GRANTED":
                details = "✓ Approved by Officer - Units Dispatching"
            
            elif event_name == "APPROVAL_REJECTED":
                details = "✗ Rejected by Officer"
            
            elif event_name == "CALLING_FOR_HELP":
                type_str = data.get("crisis_type", "Unknown")
                location = data.get("location", "Unknown")
                details = f"Notifying teams for {type_str} at {location}"
            
            elif event_name == "DISPATCH_COMPLETED":
                total = data.get("total_units", 0)
                remaining = data.get("remaining_resources", {})
                details = f"Units: {total}, Remaining Resources: {remaining}"
            
            elif event_name == "DISPATCHING_TEAM":
                role = data.get("role", "Unknown")
                number = data.get("number", "N/A")
                details = f"{role} - {number}"
            
            elif event_name == "UNIT_DISPATCHED":
                unit_type = data.get("unit_type", "Unknown")
                destination = data.get("destination", "Unknown")
                risk = data.get("risk_score", "N/A")
                details = f"{unit_type} to {destination} (Risk Score: {risk})"
            
            # Format event name for display
            display_name = event_name.replace("_", " ").title()
            timeline_data.append([display_name, timestamp, details])
    
    # Create timeline table
    if len(timeline_data) > 1:  # More than just header
        timeline_table = Table(timeline_data, colWidths=[1.8*inch, 2.2*inch, 3*inch])
        timeline_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2c5aa0")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f5f5f5")),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#cccccc")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9f9f9")]),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(timeline_table)
    
    elements.append(Spacer(1, 20))
    
    # Summary section
    elements.append(Paragraph("Crisis Summary", heading_style))
    elements.append(Spacer(1, 8))
    
    summary_items = []
    
    if "CRISIS_RECEIVED" in event_timeline:
        crisis_data = event_timeline["CRISIS_RECEIVED"]["data"]
        crises = crisis_data.get("crises", [])
        if crises:
            c = crises[0]
            summary_items.append(f"<b>Crisis Type:</b> {c.get('crisis_type', 'Unknown')}")
            summary_items.append(f"<b>Location:</b> {c.get('location', 'Unknown')}")
            summary_items.append(f"<b>Severity:</b> {c.get('severity', 'Unknown')}")
            summary_items.append(f"<b>Risk Score:</b> {c.get('risk_score', 'N/A')}")
    
    if "APPROVAL_GRANTED" in event_timeline:
        summary_items.append(f"<b>Status:</b> <font color='green'>✓ Approved</font>")
    elif "APPROVAL_REJECTED" in event_timeline:
        summary_items.append(f"<b>Status:</b> <font color='red'>✗ Rejected</font>")
    else:
        summary_items.append(f"<b>Status:</b> Pending")
    
    for item in summary_items:
        elements.append(Paragraph(item, styles["Normal"]))
        elements.append(Spacer(1, 5))
    
    elements.append(Spacer(1, 15))
    
    # Footer
    footer_text = f"Report Generated: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')} | Report #: {report_num}"
    elements.append(Paragraph(footer_text, ParagraphStyle(
        "footer",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.grey,
        alignment=1
    )))
    
    # Build PDF
    doc = SimpleDocTemplate(file_path, pagesize=letter)
    doc.build(elements)
    
    return file_path, report_num


if __name__ == "__main__":
    result = generate_comprehensive_report()
    if result:
        file_path, report_num = result
        print(f"✅ Report generated successfully!")
        print(f"📄 Saved as: {file_path}")
        print(f"📊 Report Number: {report_num}")
    else:
        print("❌ Failed to generate report")
        sys.exit(1)
