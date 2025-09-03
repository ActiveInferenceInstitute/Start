from __future__ import annotations

from src.perplexity.curriculum import extract_sections


def test_extract_sections_with_headers():
    content = """
Intro text
## Section A
Line 1
Line 2
## Section B
Line 3
""".strip()
    sections = extract_sections(content)
    assert list(sections.keys()) == ["Section A", "Section B"]
    assert "Line 1" in sections["Section A"]
    assert "Line 3" in sections["Section B"]


def test_extract_sections_without_headers():
    content = "Only text, no headers"
    sections = extract_sections(content)
    assert list(sections.keys()) == ["Research Content"]
    assert sections["Research Content"] == content


