"""Read course concepts, notes and slides without inventing slide provenance.

The default corpus is CONTEXT.md §8 and the existing unit expectations.
Research and architecture sections inform design rather than student answers.
Optional source manifests add Markdown, text, PDF or PowerPoint course files.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from modules.rag.config import REPO_ROOT, UNIT_IDS
from modules.rag.models import CourseChunk, SourceSection


def repository_sections(root: Path = REPO_ROOT) -> list[SourceSection]:
    """Load unit concepts, expectations and explicitly labelled misconceptions."""
    context = (root / "docs" / "CONTEXT.md").read_text(encoding="utf-8-sig")
    match = re.search(r"^## 8\..*?\n(.*?)(?=^## |\Z)", context, re.M | re.S)
    if match is None:
        raise ValueError("CONTEXT.md has no §8 course domain scope")
    blocks = re.split(r"(?=^[1-3]\. \*\*Unit )", match.group(1), flags=re.M)
    sections: list[SourceSection] = []
    for block in blocks:
        heading = re.match(r"([1-3])\. \*\*(.*?)\*\*", block)
        if heading:
            sections.append(SourceSection(
                unit_id=UNIT_IDS[int(heading[1]) - 1],
                source_path="docs/CONTEXT.md",
                source_title="SAGE Master Project Context",
                reference=f"§8 Course Domain Scope, Unit {heading[1]}",
                text=block.strip(),
            ))
    for unit_id in UNIT_IDS:
        relative = f"data/units/{unit_id}.json"
        unit = json.loads((root / relative).read_text(encoding="utf-8-sig"))
        if unit["unit_id"] != unit_id:
            raise ValueError(f"Unit ID mismatch in {relative}")
        for topic_number, topic in enumerate(unit["topics"]):
            for expectation_number, expectation in enumerate(topic["expectations"]):
                sections.append(SourceSection(
                    unit_id=unit_id,
                    source_path=relative,
                    source_title=f"SAGE Unit {UNIT_IDS.index(unit_id) + 1} course taxonomy",
                    reference=f"/topics/{topic_number}/expectations/{expectation_number}",
                    topic_id=topic["topic_id"],
                    text=f"{topic['title']}. Expected understanding: {expectation['text']}",
                ))
            for misconception_number, misconception in enumerate(topic["misconceptions"]):
                sections.append(SourceSection(
                    unit_id=unit_id,
                    source_path=relative,
                    source_title=f"SAGE Unit {UNIT_IDS.index(unit_id) + 1} course taxonomy",
                    reference=f"/topics/{topic_number}/misconceptions/{misconception_number}",
                    topic_id=topic["topic_id"],
                    text=(f"{topic['title']}. Common misconception (incorrect belief): "
                          f"{misconception['label']}. Description of this misconception: "
                          f"{misconception['description']}"),
                ))
    if {section.unit_id for section in sections} != set(UNIT_IDS):
        raise ValueError("Repository corpus must cover all three units")
    return sections


def read_source(path: Path, unit_id: str, title: str | None = None) -> list[SourceSection]:
    """Extract sections/pages/slides; reject blank or scanned-only documents."""
    if unit_id not in UNIT_IDS:
        raise ValueError(f"Unsupported unit_id: {unit_id}")
    path = path.resolve()
    source_title = title or path.stem
    suffix = path.suffix.lower()
    parts: list[tuple[str, str]] = []
    if suffix in {".md", ".txt"}:
        text = path.read_text(encoding="utf-8-sig")
        heading = "Notes"
        lines: list[str] = []
        in_code = False
        for line in text.splitlines():
            if line.lstrip().startswith("```"):
                in_code = not in_code
            match = None if in_code else re.match(r"^#{1,6}\s+(.+?)\s*$", line)
            if match:
                if lines:
                    parts.append((heading, "\n".join(lines)))
                heading, lines = match[1], []
            else:
                lines.append(line)
        if lines:
            parts.append((heading, "\n".join(lines)))
    elif suffix == ".pdf":
        # Requires pypdf (dynamic import avoids hard startup dependency when reading Markdown)
        from pypdf import PdfReader
        parts = [(f"Page {i}", page.extract_text() or "")
                 for i, page in enumerate(PdfReader(path).pages, 1)]
    elif suffix == ".pptx":
        # Requires python-pptx (dynamic import avoids hard startup dependency when reading Markdown)
        from pptx import Presentation
        for i, slide in enumerate(Presentation(path).slides, 1):
            text_parts = []
            for shape in slide.shapes:
                if shape.has_text_frame:
                    text_parts.append(shape.text)
                if shape.has_table:
                    text_parts.extend(" | ".join(cell.text for cell in row.cells)
                                      for row in shape.table.rows)
            parts.append((f"Slide {i}", "\n".join(text_parts)))
    else:
        raise ValueError(f"Unsupported course source format: {suffix}")
    sections = [SourceSection(
        unit_id=unit_id, source_path=path.as_posix(), source_title=source_title,
        reference=reference, text=text.strip(),
    ) for reference, text in parts if text.strip()]
    if not sections:
        raise ValueError(f"No extractable text in {path.name}; scanned PDFs need OCR first")
    return sections


def manifest_sections(manifest: Path) -> list[SourceSection]:
    """Read a JSON list of {path, unit_id, source_title?}, relative to the manifest."""
    manifest = manifest.resolve()
    sources = json.loads(manifest.read_text(encoding="utf-8-sig"))
    if not isinstance(sources, list):
        raise ValueError("Source manifest must be a JSON list")
    sections = []
    for source in sources:
        sections.extend(read_source(
            manifest.parent / source["path"], source["unit_id"], source.get("source_title"),
        ))
    return sections


def chunk_sections(
    sections: list[SourceSection], max_chars: int = 700, overlap_chars: int = 100,
) -> list[CourseChunk]:
    """Bounded chunks with word overlap, never crossing a source section boundary.

    IDs hash source, section, position and text, so rebuilding unchanged inputs
    is deterministic while edited source passages receive new identifiers.
    """
    if max_chars < 100 or not 0 <= overlap_chars < max_chars:
        raise ValueError("max_chars must be >= 100 and 0 <= overlap_chars < max_chars")
    chunks: dict[str, CourseChunk] = {}
    for section in sections:
        if section.unit_id not in UNIT_IDS:
            raise ValueError(f"Unsupported unit_id: {section.unit_id}")
        text = " ".join(section.text.split())
        start, part = 0, 1
        while start < len(text):
            end = min(start + max_chars, len(text))
            if end < len(text):
                boundary = text.rfind(" ", start + max_chars // 2, end)
                if boundary > start:
                    end = boundary
            excerpt = text[start:end].strip()
            identity = json.dumps([
                section.unit_id, section.source_path, section.reference, part, excerpt,
            ], ensure_ascii=False)
            chunk_id = "rag_" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]
            chunks[chunk_id] = CourseChunk(
                chunk_id=chunk_id, unit_id=section.unit_id, source_title=section.source_title,
                slide_or_section=section.reference + (f"; part {part}" if len(text) > max_chars else ""),
                excerpt=excerpt, source_path=section.source_path, topic_id=section.topic_id,
            )
            if end == len(text):
                break
            next_start = max(start + 1, end - overlap_chars)
            # Begin at a complete word if the overlap cuts a word in half.
            if next_start > 0 and text[next_start - 1] != " ":
                boundary = text.find(" ", next_start, end)
                next_start = boundary + 1 if boundary >= 0 else end
            start, part = next_start, part + 1
    return list(chunks.values())
