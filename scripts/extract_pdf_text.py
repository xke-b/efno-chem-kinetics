#!/usr/bin/env python3
"""Extract PDF text into reproducible plain-text artifacts.

Usage:
    python scripts/extract_pdf_text.py --pdf /path/to/file.pdf --outdir out/dir

Outputs:
- metadata.json
- full_text.txt
- pages/page-XXX.txt
- extraction_report.md
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass
class PageSummary:
    page: int
    characters: int
    empty: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True, help="Path to input PDF")
    parser.add_argument("--outdir", required=True, help="Directory for extracted artifacts")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pdf_path = Path(args.pdf).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()
    pages_dir = outdir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(str(pdf_path))
    page_summaries: list[PageSummary] = []
    full_text_parts: list[str] = []

    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        page_summaries.append(PageSummary(page=i, characters=len(text), empty=(text.strip() == "")))
        page_header = f"\n\n===== PAGE {i:03d} =====\n\n"
        full_text_parts.append(page_header + text)
        (pages_dir / f"page-{i:03d}.txt").write_text(text, encoding="utf-8")

    metadata = {
        "pdf_path": str(pdf_path),
        "page_count": len(reader.pages),
        "page_summaries": [asdict(item) for item in page_summaries],
        "document_info": {k: str(v) for k, v in (reader.metadata or {}).items()},
    }
    (outdir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    (outdir / "full_text.txt").write_text("".join(full_text_parts), encoding="utf-8")

    empty_pages = [item.page for item in page_summaries if item.empty]
    report = [
        "# PDF Extraction Report",
        "",
        f"- PDF: `{pdf_path}`",
        f"- Pages: {len(reader.pages)}",
        f"- Empty extracted pages: {empty_pages if empty_pages else 'none'}",
        f"- Extractor: `pypdf`",
        "",
        "## Character counts by page",
        "",
        "| Page | Characters | Empty |",
        "| --- | ---: | :---: |",
    ]
    for item in page_summaries:
        report.append(f"| {item.page} | {item.characters} | {'yes' if item.empty else 'no'} |")
    (outdir / "extraction_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
