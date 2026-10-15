"""Load source documents (PDFs) and extract their text.

v1 uses pypdf: fast and dependency-light, but it only returns plain text. Headings,
bold, and other layout cues are lost, and lines break wherever the PDF's page width
broke them. Run `uv run python -m about_rag.loader` to see the raw output.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

from about_rag.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Document:
    """Extracted text of one source file, kept per page for page-number metadata."""

    source: str
    pages: tuple[str, ...]

    @property
    def text(self) -> str:
        return "\n\n".join(self.pages)


def load_pdf(path: Path) -> Document:
    """Extract the text of every page in a PDF.

    Raises ValueError when no page yields any text, which usually means the PDF is a
    scanned image and needs OCR instead of text extraction.
    """
    reader = PdfReader(path)
    pages = tuple(page.extract_text().strip() for page in reader.pages)

    if not any(pages):
        raise ValueError(f"{path.name}: no extractable text (scanned PDF? needs OCR)")

    for number, text in enumerate(pages, start=1):
        if not text:
            logger.warning("%s: page %d has no extractable text", path.name, number)

    return Document(source=path.name, pages=pages)


def load_directory(directory: Path) -> list[Document]:
    """Load every PDF in a directory, in filename order so runs are reproducible."""
    return [load_pdf(path) for path in sorted(directory.glob("*.pdf"))]


if __name__ == "__main__":
    logging.basicConfig(level=get_settings().log_level)
    for document in load_directory(get_settings().raw_data_dir):
        print(f"===== {document.source} ({len(document.pages)} pages) =====")
        for number, page in enumerate(document.pages, start=1):
            print(f"\n----- page {number} -----\n{page}")
