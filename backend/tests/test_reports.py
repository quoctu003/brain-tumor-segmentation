from types import SimpleNamespace

import pytest
from reportlab.pdfbase import pdfmetrics

from app.reports import make_pdf, report_font


def test_pdf_embeds_font_for_vietnamese_and_escapes_study_name():
    font = report_font()
    if font == "Helvetica":
        pytest.skip("Install a Unicode font or set REPORT_FONT_PATH")
    name = "Nghiên cứu u não <MRI> & đối chiếu"
    glyphs = pdfmetrics.getFont(font).face.charToGlyph
    assert all(ord(char) in glyphs for char in name)
    case = SimpleNamespace(id="case-id", name=name)
    job = SimpleNamespace(id="job-id", result={
        "training_epochs": 50, "selected_epoch": 45, "seconds": 1,
        "volumes_cm3": {"wt": 2, "tc": 1, "et": 0.5},
        "model_state_id": "test", "weights_sha256": "0" * 64,
    })
    pdf = make_pdf(case, job)
    assert pdf.startswith(b"%PDF")
    assert b"/ToUnicode" in pdf
