from io import BytesIO
from functools import lru_cache
from pathlib import Path
import os
import math
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.charts.barcharts import HorizontalBarChart


@lru_cache(maxsize=1)
def report_font():
    candidates = [os.getenv("REPORT_FONT_PATH", ""),
                  "C:/Windows/Fonts/arial.ttf",
                  "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                  "/System/Library/Fonts/Supplemental/Arial.ttf"]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            pdfmetrics.registerFont(TTFont("ResearchUnicode", candidate))
            pdfmetrics.registerFontFamily("ResearchUnicode", normal="ResearchUnicode", bold="ResearchUnicode",
                                          italic="ResearchUnicode", boldItalic="ResearchUnicode")
            return "ResearchUnicode"
    return "Helvetica"


def make_pdf(case, job) -> bytes:
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=(21 * cm, 29.7 * cm), title="BrainTumor AI Research Report",
                            leftMargin=1.6 * cm, rightMargin=1.6 * cm, topMargin=1.5 * cm, bottomMargin=1.6 * cm)
    styles = getSampleStyleSheet()
    font = report_font()
    for style in styles.byName.values():
        style.fontName = font
    result = job.result
    elements = [Paragraph("BrainTumor AI", styles["Title"]),
                Paragraph("MRI Segmentation — Research Report", styles["Heading2"]), Spacer(1, 0.6 * cm)]
    for text in [f"Study: {escape(case.name)}", f"Case ID: {case.id}", f"Job ID: {job.id}",
                 f"Training: {result['training_epochs']} epochs | Selected model: epoch {result['selected_epoch']}",
                 f"Inference duration: {result['seconds']} seconds", "Output labels: 0 Background, 1 NCR/NET, 2 Edema, 3 Enhancing tumor"]:
        elements.append(Paragraph(text, styles["BodyText"]))
        elements.append(Spacer(1, 0.2 * cm))
    provenance = result.get("provenance", {})
    if provenance.get("kind") == "recorded_inference":
        elements.append(Paragraph("RECORDED PREDICTION: this report uses a previously recorded result. "
                                  "No new inference was executed when opening this result. Recorded at: "
                                  + escape(provenance.get("recorded_at", "unknown")), styles["BodyText"]))
    elements.append(Spacer(1, 0.5 * cm))
    rows = [["Region", "Definition", "Volume (cm3)"]]
    for code, definition in [("wt", "Whole tumor (1 + 2 + 3)"), ("tc", "Tumor core (1 + 3)"), ("et", "Enhancing tumor (3)")]:
        rows.append([code.upper(), definition, f"{result['volumes_cm3'][code]:.3f}"])
    table = Table(rows, colWidths=[2 * cm, 9 * cm, 5 * cm])
    table.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), font),
                               ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#153e46")),
                               ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                               ("TOPPADDING", (0, 0), (-1, -1), 12), ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey)]))
    chart = Drawing(450, 155)
    chart.add(String(0, 140, "Estimated region volumes (cm3)", fontName=font, fontSize=10, fillColor=colors.HexColor("#153e46")))
    bars = HorizontalBarChart()
    bars.x, bars.y, bars.width, bars.height = 110, 25, 310, 95
    values = [float(result["volumes_cm3"][code]) for code in ("wt", "tc", "et")]
    bars.data = [values]
    bars.categoryAxis.categoryNames = ["Whole tumor (WT)", "Tumor core (TC)", "Enhancing tumor (ET)"]
    bars.categoryAxis.labels.fontName = font
    bars.categoryAxis.labels.fontSize = 8
    bars.valueAxis.labels.fontName = font
    bars.valueAxis.labels.fontSize = 8
    bars.valueAxis.valueMin = 0
    bars.valueAxis.valueMax = max(1, math.ceil(max(values) * 1.15))
    bars.bars[0].fillColor = colors.HexColor("#448b7c")
    bars.strokeColor = None
    chart.add(bars)
    elements += [table, Spacer(1, 0.5 * cm), chart, Spacer(1, 0.4 * cm), Paragraph("WT, TC and ET overlap; do not sum their volumes.", styles["BodyText"]),
                 Paragraph("Volumes assume millimeter voxel coordinates. Images must be registered on the same grid. "
                           "No case Dice is available without ground truth. This output is for research and demonstration; "
                           "it is not a clinical diagnosis.", styles["BodyText"]), Spacer(1, cm),
                 Paragraph("Model state: " + result["model_state_id"], styles["BodyText"]),
                 Paragraph("SHA-256: " + result["weights_sha256"], styles["BodyText"])]
    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont(font, 8)
        canvas.setFillColor(colors.HexColor("#55726c"))
        canvas.drawString(1.6 * cm, cm, "BrainTumor AI | Research output")
        canvas.drawRightString(19.4 * cm, cm, f"Page {document.page}")
        canvas.restoreState()
    doc.build(elements, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()
