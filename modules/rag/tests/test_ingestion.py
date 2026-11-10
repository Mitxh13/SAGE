"""Provenance, bounded chunking and actual document extraction tests."""

import json

import pytest

from modules.rag.config import UNIT_IDS
from modules.rag.ingestion import chunk_sections, manifest_sections, read_source, repository_sections
from modules.rag.models import SourceSection


def test_repository_corpus_has_real_references_without_architecture() -> None:
    chunks = chunk_sections(repository_sections())
    assert {c.unit_id for c in chunks} == set(UNIT_IDS)
    assert all(c.source_path.startswith(("docs/", "data/units/")) for c in chunks)
    assert all(c.slide_or_section and "Slide " not in c.slide_or_section for c in chunks)
    assert not any("struggle_turn_count" in c.excerpt for c in chunks)
    assert any(c.topic_id == "topic_rag_grounding" for c in chunks)


def test_chunking_is_bounded_deterministic_and_keeps_units_separate() -> None:
    section = SourceSection(unit_id=UNIT_IDS[0], source_path="notes.md",
                            source_title="Notes", reference="Format", text="format context " * 120)
    chunks = chunk_sections([section], max_chars=150, overlap_chars=30)
    assert len(chunks) > 1
    assert all(0 < len(c.excerpt) <= 150 for c in chunks)
    assert len({c.chunk_id for c in chunks}) == len(chunks)
    assert chunks == chunk_sections([section], max_chars=150, overlap_chars=30)
    assert len(chunk_sections([section, section], max_chars=150, overlap_chars=30)) == len(chunks)
    with pytest.raises(ValueError):
        chunk_sections([section], max_chars=100, overlap_chars=100)


def test_markdown_and_relative_manifest(tmp_path) -> None:
    notes = tmp_path / "notes.md"
    notes.write_text("# Formatting\nUse explicit JSON.\n# Context\nProvide context.", encoding="utf-8")
    manifest = tmp_path / "sources.json"
    manifest.write_text(json.dumps([{"path": "notes.md", "unit_id": UNIT_IDS[0]}]), encoding="utf-8")
    sections = manifest_sections(manifest)
    assert [s.reference for s in sections] == ["Formatting", "Context"]
    assert sections[0].text == "Use explicit JSON."
    assert sections[0].source_path == notes.resolve().as_posix()


def test_powerpoint_preserves_slide_and_table_text(tmp_path) -> None:
    from pptx import Presentation
    from pptx.util import Inches

    deck = Presentation()
    slide = deck.slides.add_slide(deck.slide_layouts[6])
    slide.shapes.add_textbox(Inches(1), Inches(1), Inches(5), Inches(1)).text = "Temperature and top-p"
    table = slide.shapes.add_table(1, 1, Inches(1), Inches(2), Inches(5), Inches(1)).table
    table.cell(0, 0).text = "Sampling controls randomness"
    path = tmp_path / "course.pptx"
    deck.save(path)
    sections = read_source(path, UNIT_IDS[2])
    assert sections[0].reference == "Slide 1"
    assert "Sampling controls randomness" in sections[0].text


def test_pdf_extracts_actual_page_text(tmp_path) -> None:
    # A tiny PDF with actual text, rather than mocking the PDF reader.
    content = b"BT /F1 12 Tf 72 720 Td (Temperature controls sampling) Tj ET"
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>",
               b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
               b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
               b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream"]
    payload, offsets = b"%PDF-1.4\n", [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(len(payload))
        payload += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(payload)
    payload += b"xref\n0 6\n0000000000 65535 f \n"
    payload += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:])
    payload += f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    path = tmp_path / "slides.pdf"
    path.write_bytes(payload)
    sections = read_source(path, UNIT_IDS[2])
    assert sections[0].reference == "Page 1"
    assert "Temperature controls sampling" in sections[0].text


def test_empty_and_unknown_sources_are_not_silently_indexed(tmp_path) -> None:
    path = tmp_path / "blank.txt"
    path.write_text("   ", encoding="utf-8")
    with pytest.raises(ValueError, match="No extractable text"):
        read_source(path, UNIT_IDS[0])
    with pytest.raises(ValueError, match="Unsupported unit_id"):
        read_source(path, "unit_unknown")
