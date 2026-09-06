from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.services.pdf_stamp import stamp_pdf


def _sample_pdf(pages: int = 3) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    for index in range(pages):
        pdf.drawString(72, 720, f"Savol varaqasi — {index + 1}-sahifa")
        pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def test_stamp_keeps_pages_and_adds_text() -> None:
    source = _sample_pdf(3)
    stamped = stamp_pdf(source, student_name="Aziza Karimova", student_id=42)

    reader = PdfReader(BytesIO(stamped))
    assert len(reader.pages) == 3

    text = reader.pages[0].extract_text() or ""
    assert "Aziza Karimova" in text
    assert "ID 42" in text
    assert "Savol varaqasi" in text


def test_stamp_handles_uzbek_apostrophes() -> None:
    stamped = stamp_pdf(
        _sample_pdf(1), student_name="Gʻulom Oʻrinov", student_id=7
    )
    text = PdfReader(BytesIO(stamped)).pages[0].extract_text() or ""
    assert "ID 7" in text
