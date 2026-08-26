import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_pdf_report(client_name: str, kpi_data: dict, output_filename: str) -> str:
    os.makedirs("reports", exist_ok=True)
    filepath = os.path.join("reports", output_filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1E293B"),
    )

    subtitle_style = ParagraphStyle(
        "SubTitleStyle",
        parent=styles["Normal"],
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=15,
    )

    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=12,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
    )

    alert_style = ParagraphStyle(
        "AlertText",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#B91C1C"),
    )

    elements = []

    # Testata
    elements.append(
        Paragraph("<b>WAR ROOM STRATEGICA — REPORT PREDITTIVO</b>", title_style)
    )
    elements.append(
        Paragraph(
            f"Azienda: <b>{client_name}</b> | Stato Rischio: <b>{kpi_data.get('risk_level', 'N/D')}</b> "
            f"(Score: {kpi_data.get('risk_score', 0)}/100)",
            subtitle_style,
        )
    )
    elements.append(
        HRFlowable(
            width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceAfter=12
        )
    )

    # 1. Proiezioni Predittive
    elements.append(
        Paragraph(
            "<b>1. ANALISI PREDITTIVA & TREND MOMENTUM (30-60-90 Giorni)</b>",
            section_heading,
        )
    )
    pred = kpi_data.get("predictive_analysis", {})

    pred_data = [
        ["Orizzonte Temporale", "Stima Indice Operativo", "Stato Trend"],
        ["30 Giorni", f"{pred.get('day_30', 'N/D')}%", "Stabile"],
        ["60 Giorni", f"{pred.get('day_60', 'N/D')}%", "Sotto Target Minimo"],
        ["90 Giorni", f"{pred.get('day_90', 'N/D')}%", "Azione Richiesta"],
    ]

    t_pred = Table(pred_data, colWidths=[130, 140, 180])
    t_pred.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ]
        )
    )

    elements.append(t_pred)
    elements.append(Spacer(1, 8))
    elements.append(
        Paragraph(
            f"<b>AVVISO PREDITTIVO:</b> {pred.get('alert_60_days', '')}", alert_style
        )
    )

    # 2. Raccomandazioni AI
    elements.append(Spacer(1, 10))
    elements.append(
        Paragraph("<b>2. RACCOMANDAZIONI & SUGGERIMENTI AI</b>", section_heading)
    )

    for idx, act in enumerate(kpi_data.get("ai_strategic_action_plan", []), 1):
        elements.append(
            Paragraph(
                f"<b>{idx}. [{act.get('target')}] Urgenza {act.get('urgency')}:</b> {act.get('action')}",
                body_style,
            )
        )
        elements.append(Spacer(1, 4))

    # 3. What-If Simulator
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("<b>3. SIMULATORE SCENARI WHAT-IF</b>", section_heading))

    for key, sc in kpi_data.get("what_if_simulator", {}).items():
        rec = " [CONSIGLIATO DALLA WAR ROOM]" if sc.get("ai_recommended") else ""
        elements.append(
            Paragraph(f"<b>Scenario: {sc.get('description')}{rec}</b>", body_style)
        )
        elements.append(
            Paragraph(
                f"Impatto Ricavi: {sc.get('revenue_impact')} | "
                f"Cash Flow: {sc.get('cash_flow_annual')} | "
                f"Rischio: {sc.get('risk_level')}",
                body_style,
            )
        )
        elements.append(Spacer(1, 6))

    doc.build(elements)
    return filepath
