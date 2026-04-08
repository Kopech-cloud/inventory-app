from pathlib import Path
import os
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Register Unicode fonts for Naira sign support
pdfmetrics.registerFont(
    TTFont("DejaVu", resource_path("assets/DejaVuSans.ttf"))
)
pdfmetrics.registerFont(
    TTFont("DejaVu-Bold", resource_path("assets/DejaVuSans-Bold.ttf"))
)
pdfmetrics.registerFontFamily(
    "DejaVu",
    normal="DejaVu",
    bold="DejaVu-Bold",
    italic="DejaVu",
    boldItalic="DejaVu-Bold",
)

def draw_paid_watermark(c, doc):
    c.saveState()
    c.setFont("DejaVu-Bold", 80)
    c.setFillColor(colors.Color(0, 0.6, 0, alpha=0.12))
    c.translate(300, 320)
    c.rotate(35)
    c.drawCentredString(0, 0, "PAID")
    c.restoreState()


def draw_unpaid_watermark(c, doc):
    c.saveState()
    c.setFont("DejaVu-Bold", 72)
    c.setFillColor(colors.Color(0.85, 0.2, 0.2, alpha=0.10))
    c.translate(300, 320)
    c.rotate(35)
    c.drawCentredString(0, 0, "UNPAID")
    c.restoreState()

def draw_background_logo(c, doc):
    logo_path = resource_path("assets/logo.png")

    if not os.path.exists(logo_path):
        return

    try:
        c.saveState()
        c.setFillAlpha(0.05)
        c.drawImage(
            str(logo_path),
            170, 250,   # x, y
            width=240,
            height=120,
            preserveAspectRatio=True,
            mask='auto'
        )
        c.restoreState()
    except Exception:
        pass

def decorate_invoice_page(c, doc, payment_status):
    draw_background_logo(c, doc)

    if payment_status == "PAID":
        draw_paid_watermark(c, doc)
    else:
        draw_unpaid_watermark(c, doc)

def export_invoice_pdf(invoice, items, output_dir="invoices"):
    base_dir = Path(output_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    payment_status = str(
        invoice["payment_status"] if "payment_status" in invoice.keys() else "UNPAID"
    ).upper()

    doc_label = "RECEIPT" if payment_status == "PAID" else "INVOICE"
    file_path = base_dir / f"{doc_label}_{invoice['invoice_number']}.pdf"

    doc = SimpleDocTemplate(
        str(file_path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "InvoiceTitle",
        parent=styles["Normal"],
        fontName="DejaVu-Bold",
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#111827"),
        alignment=TA_RIGHT,
        spaceAfter=2,
    )

    subtitle_style = ParagraphStyle(
        "InvoiceSubTitle",
        parent=styles["Normal"],
        fontName="DejaVu",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#6B7280"),
        alignment=TA_RIGHT,
    )

    section_label_style = ParagraphStyle(
        "SectionLabel",
        parent=styles["Normal"],
        fontName="DejaVu-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#374151"),
        spaceAfter=3,
    )

    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["Normal"],
        fontName="DejaVu",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#111827"),
    )

    small_style = ParagraphStyle(
        "SmallStyle",
        parent=styles["Normal"],
        fontName="DejaVu",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#6B7280"),
    )

    story = []

    # Header with logo + invoice title
    logo_path = resource_path("assets/logo.png")
    logo_cell = ""

    if os.path.exists(logo_path):
        try:
            logo_cell = Image(logo_path, width=42 * mm, height=18 * mm)
        except Exception:
            logo_cell = ""

    title_block = [
        Paragraph(doc_label, title_style),
        Paragraph(f"Invoice No: {invoice['invoice_number']}", subtitle_style),
        Paragraph(f"Date: {invoice['created_at']}", subtitle_style),
    ]

    header_table = Table(
        [[logo_cell, title_block]],
        colWidths=[80 * mm, 90 * mm],
    )
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    story.append(header_table)
    story.append(Spacer(1, 10))

    # Company + Bill To section
    company_info = [
        Paragraph("From", section_label_style),
        Paragraph("Kopech Solutions", body_style),
        Paragraph("No 2 Azeez Aina Street, Olusanya, MKO Abiola Way", small_style),
        Paragraph("Ibadan, Nigeria", small_style),
        Paragraph("Phone: +23490152416401", small_style),
        Paragraph("Email: service@kopech.com", small_style),
    ]

    customer_name = "Walk-in Customer"
    if invoice is not None and "customer_name" in invoice.keys():
        customer_name = invoice["customer_name"]

    bill_to = [
        Paragraph("Bill To", section_label_style),
        Paragraph(customer_name, body_style),
    ]

    info_table = Table(
        [[company_info, bill_to]],
        colWidths=[85 * mm, 85 * mm],
    )
    info_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#E5E7EB")),
                ("INNERGRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#E5E7EB")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )

    story.append(info_table)
    story.append(Spacer(1, 14))

    # Items table
    # Items table
    table_data = [["Item", "Unit Price", "Qty", "Line Total"]]

    grand_total = 0.0
    for item in items:
        line_total = float(item["line_total"])
        grand_total += line_total

        item_name = item["product_name"]
        serial_number = item.get("serial_number", "").strip()

        if serial_number:
            item_name = f"{item_name}<br/><font size='9'>Serial No: {serial_number}</font>"

        table_data.append(
            [
                Paragraph(item_name, body_style),
                f"₦{float(item['price']):,.2f}",
                str(item["quantity"]),
                f"₦{line_total:,.2f}",
            ]
        )
    items_table = Table(
        table_data,
        colWidths=[82 * mm, 32 * mm, 18 * mm, 38 * mm],
        repeatRows=1,
    )

    items_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#10B981")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "DejaVu-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
                ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#D1D5DB")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 1), (-1, -1), "DejaVu"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    story.append(items_table)
    story.append(Spacer(1, 14))

    # Total summary
    summary_table = Table(
        [
            ["Subtotal", f"₦{grand_total:,.2f}"],
            ["Total", f"₦{grand_total:,.2f}"],
        ],
        colWidths=[110 * mm, 40 * mm],
    )

    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F3F4F6")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#111827")),
                ("FONTNAME", (0, 0), (-1, 0), "DejaVu"),
                ("FONTNAME", (0, 1), (-1, 1), "DejaVu-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10.5),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#9CA3AF")),
                ("INNERGRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#D1D5DB")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    story.append(summary_table)
    story.append(Spacer(1, 18))

    story.append(Paragraph("Thank you for your business.", body_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Generated by Kopech Inventory System.", small_style))

    payment_status = str(
        invoice["payment_status"] if "payment_status" in invoice.keys() else "UNPAID"
    ).upper()

    def first_page(canvas_obj, doc_obj):
        decorate_invoice_page(canvas_obj, doc_obj, payment_status)

    def later_pages(canvas_obj, doc_obj):
        decorate_invoice_page(canvas_obj, doc_obj, payment_status)

    doc.build(story, onFirstPage=first_page, onLaterPages=later_pages)

    return str(file_path)