from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from datetime import datetime


HOSPITAL_NAME = "City Care Hospital"
HOSPITAL_ADDRESS = "123, Health Street, Nashik, Maharashtra - 422001"
HOSPITAL_PHONE = "+91-253-XXXXXXX"
HOSPITAL_EMAIL = "info@citycarehospital.in"


def _header(story, styles):
    title_style = ParagraphStyle('HospTitle', fontSize=20, fontName='Helvetica-Bold',
                                 alignment=TA_CENTER, textColor=colors.HexColor('#1a3c6e'), spaceAfter=4)
    sub_style   = ParagraphStyle('HospSub',   fontSize=9,  fontName='Helvetica',
                                 alignment=TA_CENTER, textColor=colors.HexColor('#555555'), spaceAfter=2)
    story.append(Paragraph(HOSPITAL_NAME, title_style))
    story.append(Paragraph(HOSPITAL_ADDRESS, sub_style))
    story.append(Paragraph(f"📞 {HOSPITAL_PHONE}  |  ✉ {HOSPITAL_EMAIL}", sub_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1a3c6e'), spaceAfter=12))


def _section_title(text, styles):
    return Paragraph(f"<b>{text}</b>",
                     ParagraphStyle('SecTitle', fontSize=11, fontName='Helvetica-Bold',
                                    textColor=colors.HexColor('#1a3c6e'), spaceBefore=10, spaceAfter=6))


def _info_table(rows):
    tbl = Table(rows, colWidths=[6*cm, 10*cm])
    tbl.setStyle(TableStyle([
        ('FONTNAME',  (0,0),(-1,-1), 'Helvetica'),
        ('FONTSIZE',  (0,0),(-1,-1), 10),
        ('FONTNAME',  (0,0),(0,-1),  'Helvetica-Bold'),
        ('TEXTCOLOR', (0,0),(0,-1),  colors.HexColor('#333333')),
        ('TEXTCOLOR', (1,0),(1,-1),  colors.HexColor('#555555')),
        ('ROWBACKGROUNDS', (0,0),(-1,-1), [colors.HexColor('#f8f9fa'), colors.white]),
        ('BOTTOMPADDING', (0,0),(-1,-1), 6),
        ('TOPPADDING',    (0,0),(-1,-1), 6),
        ('LEFTPADDING',   (0,0),(-1,-1), 8),
        ('GRID', (0,0),(-1,-1), 0.5, colors.HexColor('#dee2e6')),
    ]))
    return tbl


def _paid_stamp(story):
    stamp_style = ParagraphStyle('Stamp', fontSize=36, fontName='Helvetica-Bold',
                                 alignment=TA_CENTER, textColor=colors.HexColor('#28a745'), spaceBefore=20)
    story.append(Paragraph("✔ PAID", stamp_style))


def generate_appointment_receipt(data):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    _header(story, styles)

    receipt_style = ParagraphStyle('Receipt', fontSize=14, fontName='Helvetica-Bold',
                                   alignment=TA_CENTER, textColor=colors.HexColor('#e63946'), spaceAfter=16)
    story.append(Paragraph("APPOINTMENT RECEIPT", receipt_style))

    story.append(_section_title("Patient & Appointment Details", styles))
    rows = [
        ["Receipt No.",    f"APT-{data.get('appointment_id', 'N/A')}"],
        ["Patient Name",   str(data.get('patient_name', ''))],
        ["Contact",        str(data.get('phone', ''))],
        ["Doctor",         str(data.get('doctor_name', ''))],
        ["Specialization", str(data.get('specialization', ''))],
        ["Date",           str(data.get('date', ''))],
        ["Time Slot",      str(data.get('time_slot', ''))],
        ["Status",         str(data.get('status', ''))],
    ]
    story.append(_info_table(rows))

    story.append(_section_title("Payment Details", styles))
    rows2 = [
        ["Payment Method",  str(data.get('payment_method', ''))],
        ["Transaction ID",  str(data.get('transaction_id', ''))],
        ["Amount Paid",     f"₹ {data.get('amount', '500.00')}"],
        ["Payment Status",  str(data.get('pay_status', 'Completed'))],
        ["Generated On",    datetime.now().strftime('%d-%m-%Y %H:%M:%S')],
    ]
    story.append(_info_table(rows2))

    _paid_stamp(story)

    footer_style = ParagraphStyle('Footer', fontSize=8, fontName='Helvetica',
                                  alignment=TA_CENTER, textColor=colors.grey, spaceBefore=30)
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey, spaceBefore=20))
    story.append(Paragraph("Thank you for choosing City Care Hospital. Get well soon!", footer_style))
    story.append(Paragraph("This is a computer-generated receipt. No signature required.", footer_style))

    doc.build(story)
    buf.seek(0)
    return buf


def generate_prescription_receipt(data):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    _header(story, styles)

    receipt_style = ParagraphStyle('Receipt', fontSize=14, fontName='Helvetica-Bold',
                                   alignment=TA_CENTER, textColor=colors.HexColor('#e63946'), spaceAfter=16)
    story.append(Paragraph("PRESCRIPTION BILL RECEIPT", receipt_style))

    story.append(_section_title("Patient & Doctor Details", styles))
    rows = [
        ["Receipt No.",    f"PRX-{data.get('prescription_id', 'N/A')}"],
        ["Patient Name",   str(data.get('patient_name', ''))],
        ["Contact",        str(data.get('phone', ''))],
        ["Doctor",         str(data.get('doctor_name', ''))],
        ["Specialization", str(data.get('specialization', ''))],
        ["Date",           str(data.get('date', ''))],
        ["Time Slot",      str(data.get('time_slot', ''))],
    ]
    story.append(_info_table(rows))

    story.append(_section_title("Prescription Details", styles))
    rows2 = [
        ["Medicines",       str(data.get('medicines', ''))],
        ["Doctor Notes",    str(data.get('notes', 'N/A'))],
        ["Consultation Fee",f"₹ {data.get('consultation_fee', '')}"],
    ]
    story.append(_info_table(rows2))

    story.append(_section_title("Payment Details", styles))
    rows3 = [
        ["Payment Method",  str(data.get('payment_method', ''))],
        ["Transaction ID",  str(data.get('transaction_id', ''))],
        ["Amount Paid",     f"₹ {data.get('paid_amount', '')}"],
        ["Payment Status",  str(data.get('pay_status', 'Completed'))],
        ["Generated On",    datetime.now().strftime('%d-%m-%Y %H:%M:%S')],
    ]
    story.append(_info_table(rows3))

    _paid_stamp(story)

    footer_style = ParagraphStyle('Footer', fontSize=8, fontName='Helvetica',
                                  alignment=TA_CENTER, textColor=colors.grey, spaceBefore=30)
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey, spaceBefore=20))
    story.append(Paragraph("Thank you for choosing City Care Hospital. Follow the prescription carefully.", footer_style))
    story.append(Paragraph("This is a computer-generated receipt. No signature required.", footer_style))

    doc.build(story)
    buf.seek(0)
    return buf
