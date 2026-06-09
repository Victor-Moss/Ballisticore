"""
Generates permit PDFs (full and mini) using ReportLab.
Pure Python — no system GTK/Pango dependencies required.
"""

from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from app.models.permit import Permit
from app.models.guard import Guard
from app.models.firearm import Firearm
from app.services import users as user_svc
from app.core.branding import branding

COMPANY_NAME = branding["company_name"]
COMPANY_REG = branding.get("company_reg", "")
PSIRA_NUMBER = branding.get("psira_number", "")
COMPANY_ADDRESS = branding.get("company_address", "")

PERMITS_DIR = Path(__file__).parent.parent.parent / "permits"

BLACK = colors.black
WHITE = colors.white
DARK = colors.HexColor("#222222")
LIGHT_GREY = colors.HexColor("#f0f0f0")


def _context(db: Session, permit: Permit, guard: Guard, firearm: Firearm) -> dict:
    issued_by_user = user_svc.get_by_id(db, permit.issued_by)
    issued_by_name = issued_by_user.username if issued_by_user else permit.issued_by
    location_name = guard.location.name if guard.location else "—"
    issued_at = permit.issued_at or datetime.utcnow()
    if permit.guard_signed and permit.guard_signed_at:
        guard_signature_display = f"E-SIGNED {permit.guard_signed_at.strftime('%Y-%m-%d %H:%M')}"
    else:
        guard_signature_display = ""  # blank line for a wet signature
    return {
        "permit_number": permit.permit_number,
        "guard_name": f"{guard.first_name} {guard.last_name}",
        "guard_id_number": guard.id_number,
        "guard_cell": guard.cell_phone or "—",
        "guard_address": guard.physical_address or "—",
        "guard_personnel": guard.id[:8],
        "firearm_serial": firearm.serial_number,
        "firearm_make": f"{firearm.make} {firearm.model or ''}".strip(),
        "firearm_calibre": firearm.calibre,
        "firearm_type": firearm.type,
        "firearm_license": firearm.license_number or "—",
        "firearm_license_date": str(firearm.license_issue_date) if firearm.license_issue_date else "—",
        "ammunition_type": permit.ammunition_type or firearm.ammunition_type_name or "—",
        "issued_date": issued_at.strftime("%Y-%m-%d"),
        "issued_time": issued_at.strftime("%H:%M"),
        "valid_date": str(permit.valid_date) if permit.valid_date else "—",
        "issued_by_name": issued_by_name,
        "location_name": location_name,
        "guard_signature_display": guard_signature_display,
    }


def _section_header_style():
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, BLACK),
        ("BACKGROUND", (0, 1), (0, -1), LIGHT_GREY),
        ("BACKGROUND", (2, 1), (2, -1), LIGHT_GREY),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 1), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ])


def generate_full_permit(db: Session, permit: Permit, guard: Guard, firearm: Firearm) -> str:
    PERMITS_DIR.mkdir(parents=True, exist_ok=True)
    ctx = _context(db, permit, guard, firearm)
    filename = f"{permit.permit_number}_full.pdf"
    output_path = str(PERMITS_DIR / filename)

    styles = getSampleStyleSheet()
    centered = ParagraphStyle("centered", parent=styles["Normal"], alignment=TA_CENTER, fontSize=8)
    bold_centered = ParagraphStyle("bold_centered", parent=styles["Normal"], alignment=TA_CENTER,
                                   fontSize=10, fontName="Helvetica-Bold")
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=7, alignment=TA_CENTER)

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            leftMargin=14*mm, rightMargin=14*mm,
                            topMargin=12*mm, bottomMargin=12*mm)

    W = A4[0] - 28*mm  # usable width
    col = W / 4

    elements = []

    # Permit number right-aligned
    elements.append(Paragraph(f"<b>Permit No: {ctx['permit_number']}</b>", styles["Normal"]))
    elements.append(Spacer(1, 2*mm))

    # Header block
    header_data = [
        [Paragraph(f"<b>{COMPANY_NAME}</b><br/>{COMPANY_REG} | PSIRA #: {PSIRA_NUMBER}", bold_centered)],
        [Paragraph("<b>Authority to be in Possession of Company Firearm</b>", centered)],
        [Paragraph(COMPANY_ADDRESS, small)],
    ]
    header_table = Table(header_data, colWidths=[W])
    header_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1.5, BLACK),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 3*mm))

    # Guard details
    guard_data = [
        [Paragraph("<b>GUARD DETAILS</b>", centered), "", "", ""],
        ["Name:", ctx["guard_name"], "ID Number:", ctx["guard_id_number"]],
        ["Cell Phone:", ctx["guard_cell"], "Personnel No:", ctx["guard_personnel"]],
        ["Address:", ctx["guard_address"], "", ""],
    ]
    guard_table = Table(guard_data, colWidths=[col, col, col, col])
    style = _section_header_style()
    style.add("SPAN", (0, 0), (3, 0))
    style.add("SPAN", (1, 3), (3, 3))
    guard_table.setStyle(style)
    elements.append(guard_table)
    elements.append(Spacer(1, 2*mm))

    # Auth text
    elements.append(Paragraph(
        "<i>The above-named person is hereby authorised to be in possession of the undermentioned "
        "firearm for the period hereunder stated.</i>", centered))
    elements.append(Spacer(1, 2*mm))

    # Firearm details
    firearm_data = [
        [Paragraph("<b>FIREARM DETAILS</b>", centered), "", "", ""],
        ["Serial / Firearm No:", ctx["firearm_serial"], "Make / Model:", ctx["firearm_make"]],
        ["Calibre:", ctx["firearm_calibre"], "Type:", ctx["firearm_type"]],
        ["License Number:", ctx["firearm_license"], "License Issue Date:", ctx["firearm_license_date"]],
        ["Ammunition Type:", ctx["ammunition_type"], "", ""],
    ]
    firearm_table = Table(firearm_data, colWidths=[col, col, col, col])
    fs = _section_header_style()
    fs.add("SPAN", (0, 0), (3, 0))
    fs.add("SPAN", (1, 4), (3, 4))
    firearm_table.setStyle(fs)
    elements.append(firearm_table)
    elements.append(Spacer(1, 2*mm))

    # Period
    period_data = [
        [Paragraph("<b>PERIOD OF AUTHORISATION</b>", centered), "", "", ""],
        ["Date Issued:", ctx["issued_date"], "Time Issued:", ctx["issued_time"]],
        ["Valid Date:", ctx["valid_date"], "Permit Number:", ctx["permit_number"]],
    ]
    period_table = Table(period_data, colWidths=[col, col, col, col])
    ps = _section_header_style()
    ps.add("SPAN", (0, 0), (3, 0))
    period_table.setStyle(ps)
    elements.append(period_table)
    elements.append(Spacer(1, 2*mm))

    # Authorisation / signatures
    sig_row_height = 10*mm
    auth_data = [
        [Paragraph("<b>AUTHORISATION</b>", centered), "", "", ""],
        ["Issued by:", ctx["issued_by_name"], "Location / Posted:", ctx["location_name"]],
        ["Guard Signature:", ctx["guard_signature_display"], "Issuer Signature:", ""],
        ["Witness:", "", "CIT Cell / Route:", "—"],
    ]
    auth_table = Table(auth_data, colWidths=[col, col, col, col],
                       rowHeights=[None, None, sig_row_height, sig_row_height])
    as_ = _section_header_style()
    as_.add("SPAN", (0, 0), (3, 0))
    auth_table.setStyle(as_)
    elements.append(auth_table)
    elements.append(Spacer(1, 2*mm))

    # Return section
    return_data = [
        [Paragraph("<b>FIREARM RETURN (TO BE COMPLETED ON RETURN)</b>", centered), "", "", ""],
        ["Date Firearm Back:", "", "Time Firearm Back:", ""],
        ["In Order (YES / NO):", "", "Remarks:", ""],
        ["Return Signature:", "", "Rounds Ammo Returned:", ""],
    ]
    return_table = Table(return_data, colWidths=[col, col, col, col],
                         rowHeights=[None, sig_row_height, sig_row_height, sig_row_height])
    rs = _section_header_style()
    rs.add("SPAN", (0, 0), (3, 0))
    return_table.setStyle(rs)
    elements.append(return_table)
    elements.append(Spacer(1, 3*mm))

    elements.append(Paragraph(
        f"BallistiCore Firearms Register System — {ctx['issued_date']} — {ctx['permit_number']}",
        small))

    doc.build(elements)
    return output_path


def generate_mini_permit(db: Session, permit: Permit, guard: Guard, firearm: Firearm) -> str:
    PERMITS_DIR.mkdir(parents=True, exist_ok=True)
    ctx = _context(db, permit, guard, firearm)
    filename = f"{permit.permit_number}_mini.pdf"
    output_path = str(PERMITS_DIR / filename)

    # Mini permit — 85mm x 140mm (half A5 card size)
    card_w, card_h = 85*mm, 140*mm
    styles = getSampleStyleSheet()
    tiny = ParagraphStyle("tiny", parent=styles["Normal"], fontSize=6.5, alignment=TA_CENTER)
    tiny_bold = ParagraphStyle("tiny_bold", parent=styles["Normal"], fontSize=7,
                               fontName="Helvetica-Bold", alignment=TA_CENTER)
    label_style = ParagraphStyle("label", parent=styles["Normal"], fontSize=7,
                                 fontName="Helvetica-Bold")

    doc = SimpleDocTemplate(output_path, pagesize=(card_w, card_h),
                            leftMargin=4*mm, rightMargin=4*mm,
                            topMargin=4*mm, bottomMargin=4*mm)

    W = card_w - 8*mm
    col1, col2 = W * 0.42, W * 0.58

    elements = []

    # Header
    hdr = Table([
        [Paragraph(f"<b>{COMPANY_NAME}</b>", tiny_bold)],
        [Paragraph(f"{COMPANY_REG} | PSIRA #: {PSIRA_NUMBER}", tiny)],
        [Paragraph("<b>Authority to be in Possession of Company Firearm</b>", tiny_bold)],
        [Paragraph(COMPANY_ADDRESS, tiny)],
    ], colWidths=[W])
    hdr.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, BLACK),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    elements.append(hdr)
    elements.append(Paragraph(f"<b>Permit: {ctx['permit_number']}</b>", tiny_bold))
    elements.append(Spacer(1, 1.5*mm))

    def mini_section(title, rows):
        data = [[Paragraph(f"<b>{title}</b>", tiny_bold), ""]]
        for label, val in rows:
            data.append([Paragraph(label, label_style), Paragraph(str(val), styles["Normal"])])
        t = Table(data, colWidths=[col1, col2])
        t.setStyle(TableStyle([
            ("SPAN", (0, 0), (1, 0)),
            ("BACKGROUND", (0, 0), (1, 0), DARK),
            ("TEXTCOLOR", (0, 0), (1, 0), WHITE),
            ("GRID", (0, 0), (-1, -1), 0.4, BLACK),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 1.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ]))
        return t

    elements.append(mini_section("GUARD", [
        ("Name:", ctx["guard_name"]),
        ("ID #:", ctx["guard_id_number"]),
        ("Cell:", ctx["guard_cell"]),
    ]))
    elements.append(Spacer(1, 1*mm))
    elements.append(Paragraph(
        "<i>Is hereby authorised to be in possession of the undermentioned firearm.</i>", tiny))
    elements.append(Spacer(1, 1*mm))
    elements.append(mini_section("FIREARM", [
        ("Serial No:", ctx["firearm_serial"]),
        ("Make / Model:", ctx["firearm_make"]),
        ("Calibre:", ctx["firearm_calibre"]),
        ("Type:", ctx["firearm_type"]),
        ("License No:", ctx["firearm_license"]),
    ]))
    elements.append(Spacer(1, 1*mm))
    elements.append(mini_section("PERIOD", [
        ("Date Issued:", ctx["issued_date"]),
        ("Time Issued:", ctx["issued_time"]),
        ("Valid Date:", ctx["valid_date"]),
    ]))
    elements.append(Spacer(1, 1*mm))
    elements.append(mini_section("ISSUED BY", [
        ("Name:", ctx["issued_by_name"]),
        ("Location:", ctx["location_name"]),
        ("Guard Sig:", ctx["guard_signature_display"] or " " * 30),
        ("Issuer Sig:", " " * 30),
    ]))
    elements.append(Spacer(1, 1*mm))
    elements.append(Paragraph(f"BallistiCore — {ctx['issued_date']}", tiny))

    doc.build(elements)
    return output_path


def generate_both(db: Session, permit: Permit, guard: Guard, firearm: Firearm) -> dict:
    full_path = generate_full_permit(db, permit, guard, firearm)
    mini_path = generate_mini_permit(db, permit, guard, firearm)
    permit.pdf_path = full_path
    db.commit()
    return {"full": full_path, "mini": mini_path}
