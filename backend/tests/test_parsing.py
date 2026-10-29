import io

import pytest

from jobfit.parsing import FileTooLargeError, ResumeParseError, extract_text

LIMIT = 2_000_000


def test_plain_text(resume):
    assert extract_text("cv.txt", resume.encode(), max_bytes=LIMIT).startswith("Alex Chen")


def test_markdown_is_read_as_text(resume):
    assert "Tableau" in extract_text("cv.md", resume.encode(), max_bytes=LIMIT)


def test_docx_paragraphs_and_tables():
    docx = pytest.importorskip("docx")
    document = docx.Document()
    document.add_paragraph("Alex Chen, Melbourne. Data analyst with SQL and Python experience.")
    table = document.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "Skills"
    table.rows[0].cells[1].text = "Power BI, Tableau"
    buffer = io.BytesIO()
    document.save(buffer)

    text = extract_text("cv.docx", buffer.getvalue(), max_bytes=LIMIT)
    assert "Data analyst with SQL" in text
    assert "Skills | Power BI, Tableau" in text


def test_pdf():
    canvas_module = pytest.importorskip("reportlab.pdfgen.canvas")
    buffer = io.BytesIO()
    pdf = canvas_module.Canvas(buffer)
    pdf.drawString(72, 750, "Alex Chen - Data Intern at Southbank Retail Co")
    pdf.drawString(72, 730, "Wrote SQL queries to join sales and inventory tables")
    pdf.save()

    text = extract_text("cv.pdf", buffer.getvalue(), max_bytes=LIMIT)
    assert "Wrote SQL queries" in text


def test_broken_pdf_gives_a_friendly_error():
    with pytest.raises(ResumeParseError, match="couldn't be read"):
        extract_text("cv.pdf", b"%PDF-1.7 this is not really a pdf", max_bytes=LIMIT)


def test_unsupported_type():
    with pytest.raises(ResumeParseError, match="Unsupported file type"):
        extract_text("cv.pages", b"x" * 100, max_bytes=LIMIT)


def test_too_large():
    with pytest.raises(FileTooLargeError):
        extract_text("cv.txt", b"x" * 11, max_bytes=10)


def test_too_little_text():
    with pytest.raises(ResumeParseError, match="enough text"):
        extract_text("cv.txt", b"Alex Chen", max_bytes=LIMIT)
