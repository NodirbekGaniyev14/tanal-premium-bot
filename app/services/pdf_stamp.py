"""PDF nusxasiga o'quvchi ismi va ID sini yozish.

Har o'quvchi–har fayl uchun bir marta yaratiladi, natijasi `file_cache` da
`file_id` bo'lib qoladi — ikkinchi marta qayta yaratilmaydi.
"""

from __future__ import annotations

from datetime import date
from io import BytesIO

from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas

_FOOTER_FONT = "Helvetica"
_FOOTER_SIZE = 7.5
_FOOTER_MARGIN = 14
_WATERMARK_SIZE = 34


def _overlay(width: float, height: float, footer: str, watermark: str) -> PdfReader:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(width, height))

    pdf.saveState()
    pdf.setFillColor(Color(0, 0, 0, alpha=0.06))
    pdf.setFont("Helvetica-Bold", _WATERMARK_SIZE)
    pdf.translate(width / 2, height / 2)
    pdf.rotate(35)
    pdf.drawCentredString(0, 0, watermark)
    pdf.restoreState()

    pdf.setFillColor(Color(0, 0, 0, alpha=0.45))
    pdf.setFont(_FOOTER_FONT, _FOOTER_SIZE)
    pdf.drawString(_FOOTER_MARGIN, _FOOTER_MARGIN, footer)

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return PdfReader(buffer)


def _ascii(value: str) -> str:
    """Helvetica o'zbek harflarini chizmaydi — xavfsiz ko'rinishga keltiramiz."""
    table = str.maketrans({"‘": "'", "’": "'", "ʻ": "'", "ʼ": "'"})
    return value.translate(table).encode("ascii", "replace").decode("ascii")


def stamp_pdf(
    source: bytes,
    *,
    student_name: str,
    student_id: int,
    when: date | None = None,
) -> bytes:
    """Har sahifaga ism, ID va sana yozib, yangi PDF baytlarini qaytaradi."""
    when = when or date.today()
    footer = _ascii(f"{student_name} · ID {student_id} · {when.isoformat()}")
    watermark = _ascii(f"{student_name} · ID {student_id}")

    writer = PdfWriter(clone_from=BytesIO(source))

    for page in writer.pages:
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        overlay = _overlay(width, height, footer, watermark)
        page.merge_page(overlay.pages[0])

    output = BytesIO()
    writer.write(output)
    return output.getvalue()
