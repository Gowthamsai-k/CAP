import re
from pathlib import Path

import fitz
from docx import Document


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        with fitz.open(path) as pdf:
            text = "\n".join(page.get_text("text") for page in pdf)
    elif suffix == ".docx":
        doc = Document(path)
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    else:
        raise ValueError("Only PDF and DOCX files are supported.")
    if not text.strip():
        raise ValueError("No selectable text found. Scanned PDFs need OCR, which is not enabled in this milestone.")
    return text


_SECTION = re.compile(r"(?im)^\s*((?:section|article|rule|regulation|chapter|schedule)\s+[\w()./-]+[^\n]{0,120})\s*$")
_MARKDOWN_HEADING = re.compile(r"(?m)^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$")


def legal_chunks(text: str, max_chars: int = 1800) -> list[tuple[str | None, str]]:
    """Split first at recognizable legal headings, then paragraph boundaries."""
    normalized = re.sub(r"\r\n?", "\n", text)
    headings = list(_SECTION.finditer(normalized))
    sections: list[tuple[str | None, str]] = []
    if headings:
        for i, heading in enumerate(headings):
            start = heading.start()
            end = headings[i + 1].start() if i + 1 < len(headings) else len(normalized)
            sections.append((heading.group(1).strip(), normalized[start:end].strip()))
        preface = normalized[:headings[0].start()].strip()
        if preface:
            sections.insert(0, (None, preface))
    else:
        sections = [(None, p.strip()) for p in re.split(r"\n\s*\n", normalized) if p.strip()]

    chunks: list[tuple[str | None, str]] = []
    for section, body in sections:
        paragraphs = re.split(r"\n\s*\n", body)
        # The detected heading is already preserved in the section metadata.
        # Don't emit it again as a standalone text chunk when it has no body.
        if section and paragraphs and paragraphs[0].strip().casefold() == section.casefold():
            paragraphs = paragraphs[1:]
        part = ""
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            if len(part) + len(paragraph) + 2 > max_chars and part:
                chunks.append((section, part))
                part = ""
            if len(paragraph) > max_chars:
                for offset in range(0, len(paragraph), max_chars):
                    chunks.append((section, paragraph[offset:offset + max_chars]))
            else:
                part = f"{part}\n\n{paragraph}" if part else paragraph
        if part:
            chunks.append((section, part))
    return chunks


def company_chunks(text: str, max_chars: int = 1800) -> list[tuple[str | None, str]]:
    """Chunk internal Markdown/plain text while preserving its heading labels."""
    normalized = re.sub(r"\r\n?", "\n", text)
    headings = list(_MARKDOWN_HEADING.finditer(normalized))
    sections: list[tuple[str | None, str]] = []
    if headings:
        preface = normalized[:headings[0].start()].strip()
        if preface:
            sections.append((None, preface))
        for i, heading in enumerate(headings):
            end = headings[i + 1].start() if i + 1 < len(headings) else len(normalized)
            sections.append((heading.group(1).strip(), normalized[heading.end():end].strip()))
    else:
        sections = [(None, normalized.strip())]

    chunks: list[tuple[str | None, str]] = []
    for section, body in sections:
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
        part = ""
        for paragraph in paragraphs:
            if len(paragraph) > max_chars:
                if part:
                    chunks.append((section, part))
                    part = ""
                chunks.extend((section, paragraph[offset:offset + max_chars]) for offset in range(0, len(paragraph), max_chars))
            elif part and len(part) + len(paragraph) + 2 > max_chars:
                chunks.append((section, part))
                part = paragraph
            else:
                part = f"{part}\n\n{paragraph}" if part else paragraph
        if part:
            chunks.append((section, part))
    return chunks
