import logging
import shutil

import pytest
from pypdf import PdfWriter

from about_rag.config import Settings
from about_rag.loader import Document, load_directory, load_pdf

SAMPLE_PDF = Settings(_env_file=None).raw_data_dir / "about_saeem.pdf"


def write_blank_pdf(path, pages=1):
    """A PDF with pages but no text, like a scanned document."""
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=595, height=842)
    writer.write(path)


def test_load_pdf_extracts_text_and_source():
    document = load_pdf(SAMPLE_PDF)
    assert document.source == "about_saeem.pdf"
    assert len(document.pages) >= 1
    assert "Saeem Mehmood Sadiq" in document.text
    assert "FAST-NUCES" in document.text


def test_text_joins_pages_with_blank_line():
    document = Document(source="x.pdf", pages=("first", "second"))
    assert document.text == "first\n\nsecond"


def test_pdf_without_any_text_is_rejected(tmp_path):
    path = tmp_path / "scanned.pdf"
    write_blank_pdf(path, pages=2)
    with pytest.raises(ValueError, match="OCR"):
        load_pdf(path)


def test_blank_page_logs_warning_but_still_loads(tmp_path, caplog):
    path = tmp_path / "mixed.pdf"
    writer = PdfWriter()
    writer.append(SAMPLE_PDF)
    writer.add_blank_page(width=595, height=842)
    writer.write(path)

    with caplog.at_level(logging.WARNING):
        document = load_pdf(path)

    assert document.pages[-1] == ""
    assert "has no extractable text" in caplog.text


def test_load_directory_reads_only_pdfs_in_name_order(tmp_path):
    shutil.copy(SAMPLE_PDF, tmp_path / "b.pdf")
    shutil.copy(SAMPLE_PDF, tmp_path / "a.pdf")
    (tmp_path / "notes.txt").write_text("not a pdf")

    documents = load_directory(tmp_path)

    assert [d.source for d in documents] == ["a.pdf", "b.pdf"]
