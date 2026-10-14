"""Render data/about_saeem.md into a PDF, to simulate a real-world PDF dataset.

The markdown file is where Saeem writes everything down. In a real RAG project the
source documents usually arrive as PDFs, so this script produces one, and the ingestion
pipeline then extracts text back out of it.

Run with: uv run --group tools python scripts/make_pdf.py
"""

from pathlib import Path

import markdown
from xhtml2pdf import pisa

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT_ROOT / "data" / "about_saeem.md"
TARGET = PROJECT_ROOT / "data" / "raw" / "about_saeem.pdf"

CSS = """
@page { size: a4; margin: 2cm; }
body { font-family: Helvetica; font-size: 10pt; line-height: 1.4; color: #222; }
h1 { font-size: 20pt; margin-bottom: 4pt; }
h2 { font-size: 14pt; color: #1f3a5f; margin-top: 14pt; border-bottom: 1px solid #ccc; }
h3 { font-size: 11.5pt; margin-top: 10pt; }
blockquote { color: #666; font-style: italic; margin-left: 0; }
code { font-family: Courier; }
a { color: #1f5fbf; text-decoration: none; }
hr { display: none; }
"""


def render(source: Path, target: Path) -> None:
    html_body = markdown.markdown(source.read_text(encoding="utf-8"))
    html = f"<html><head><style>{CSS}</style></head><body>{html_body}</body></html>"

    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("wb") as out:
        result = pisa.CreatePDF(html, dest=out, encoding="utf-8")
    if result.err:
        raise RuntimeError(f"PDF rendering failed with {result.err} error(s)")


if __name__ == "__main__":
    render(SOURCE, TARGET)
    print(f"Wrote {TARGET.relative_to(PROJECT_ROOT)}")
