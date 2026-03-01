from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from db import SessionLocal, CrisisReport
from services.audit import get_audit_log
import os


# ---------------------------------------------------------
# REPORT DIRECTORY
# ---------------------------------------------------------
REPORT_DIR = os.path.join(os.getcwd(), "reports")

if not os.path.exists(REPORT_DIR):
    os.makedirs(REPORT_DIR)


# ---------------------------------------------------------
# AUTO INCREMENT REPORT NUMBER
# ---------------------------------------------------------
def get_next_report_number():
    existing = [
        f for f in os.listdir(REPORT_DIR)
        if f.startswith("crisis_report_") and f.endswith(".pdf")
    ]

    if not existing:
        return 1

    numbers = []
    for f in existing:
        try:
            num = int(f.replace("crisis_report_", "").replace(".pdf", ""))
            numbers.append(num)
        except:
            continue

    return max(numbers) + 1


# ---------------------------------------------------------
# MAIN REPORT GENERATOR
# ---------------------------------------------------------
def generate_comprehensive_report(crisis_id):

    session = SessionLocal()
    report = session.query(CrisisReport).filter_by(
        crisis_id=crisis_id
    ).first()

    if not report:
        print("No crisis found for report")
        session.close()
        return None

    report_number = get_next_report_number()
    file_name = f"crisis_report_{report_number}.pdf"
    file_path = os.path.join(REPORT_DIR, file_name)

    doc = SimpleDocTemplate(file_path)
    elements = []
    styles = getSampleStyleSheet()

    # HEADER
    elements.append(Paragraph("AUTONOMOUS CRISIS COMMAND REPORT", styles["Heading1"]))
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph(f"Report Number: {report_number}", styles["Normal"]))
    elements.append(Paragraph(f"Crisis ID: {crisis_id}", styles["Normal"]))
    elements.append(Paragraph(f"Submitted At: {report.submitted_at}", styles["Normal"]))
    elements.append(Paragraph(f"Approval Status: {report.approval_status}", styles["Normal"]))
    elements.append(Paragraph(f"Approval Time: {report.approval_time}", styles["Normal"]))
    elements.append(Paragraph(f"Dispatch Time: {report.dispatch_time}", styles["Normal"]))
    elements.append(Spacer(1, 0.5 * inch))

    # TIMELINE
    elements.append(Paragraph("EVENT TIMELINE", styles["Heading2"]))
    elements.append(Spacer(1, 0.2 * inch))

    events = get_audit_log()
    data = [["Timestamp", "Event Type"]]

    for event in events:
        data.append([
            str(event["timestamp"]),
            event["event_type"]
        ])

    table = Table(data, colWidths=[2.5 * inch, 3 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))

    elements.append(table)

    # BUILD PDF
    doc.build(elements)

    print(f"Report generated: {file_path}")

    session.close()

    return file_path