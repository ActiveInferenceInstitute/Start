"""Deterministic quality checks for generated pipeline content."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from src.config.languages import get_script_mapping

_SCRIPT_RANGES: dict[str, tuple[tuple[int, int], ...]] = {
    "arabic": ((0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF)),
    "chinese": ((0x3400, 0x4DBF), (0x4E00, 0x9FFF)),
    "japanese": ((0x3040, 0x30FF), (0x3400, 0x4DBF), (0x4E00, 0x9FFF)),
    "devanagari": ((0x0900, 0x097F),),
    "cyrillic": ((0x0400, 0x04FF),),
    "hangul": ((0x1100, 0x11FF), (0xAC00, 0xD7AF)),
    "hebrew": ((0x0590, 0x05FF),),
    "thai": ((0x0E00, 0x0E7F),),
}


def _script_key(script: str) -> str | None:
    lowered = script.casefold()
    for key in _SCRIPT_RANGES:
        if key in lowered:
            return key
    return None


def _contains_script(content: str, ranges: tuple[tuple[int, int], ...]) -> bool:
    return any(any(start <= ord(char) <= end for start, end in ranges) for char in content)


@dataclass
class QualityReport:
    """Machine-readable quality result for one text artifact."""

    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    def fail(self, message: str) -> None:
        self.valid = False
        self.errors.append(message)

    def as_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "metrics": dict(self.metrics),
        }


def validate_generated_text(
    content: str,
    *,
    min_words: int = 1,
    max_words: int | None = None,
    require_sections: bool = False,
    require_citations: bool = False,
) -> QualityReport:
    """Validate basic structure without pretending to judge factual truth."""

    report = QualityReport()
    if not isinstance(content, str) or not content.strip():
        report.fail("content is empty")
        return report
    words = len(content.split())
    headings = re.findall(r"^#{1,6}\s+.+$", content, flags=re.MULTILINE)
    citations = re.findall(r"\[[0-9]+\]|https?://\S+", content)
    report.metrics.update(
        {"word_count": words, "heading_count": len(headings), "citation_count": len(citations)}
    )
    if words < min_words:
        report.fail(f"content is short ({words} words; minimum {min_words})")
    if max_words is not None and words > max_words:
        report.fail(f"content is too long ({words} words; maximum {max_words})")
    if require_sections and not headings:
        report.fail("content must contain at least one Markdown heading")
    if require_citations and not citations:
        report.fail("content must contain a citation marker or source URL")
    sentences = [part.strip().casefold() for part in re.split(r"[.!?]+", content) if part.strip()]
    if len(sentences) >= 6 and len(set(sentences)) / len(sentences) < 0.8:
        report.warnings.append("content may contain repetitive sentences")
    return report


def validate_translation(
    source: str,
    translated: str,
    target_language: str,
    *,
    require_parity: bool = False,
) -> QualityReport:
    """Check translation completeness and structural parity."""

    report = validate_generated_text(translated, min_words=1, require_sections=False)
    if not isinstance(target_language, str) or not target_language.strip():
        report.fail("target language is empty")
    source_headings = re.findall(r"^#{1,6}\s+.+$", source or "", flags=re.MULTILINE)
    translated_headings = re.findall(r"^#{1,6}\s+.+$", translated or "", flags=re.MULTILINE)
    report.metrics["source_heading_count"] = len(source_headings)
    report.metrics["translated_heading_count"] = len(translated_headings)
    try:
        expected_script = get_script_mapping(target_language)
    except (OSError, ValueError, KeyError):
        expected_script = target_language
    report.metrics["expected_script"] = expected_script
    script_key = _script_key(expected_script)
    if script_key and not _contains_script(translated or "", _SCRIPT_RANGES[script_key]):
        report.fail(f"translation does not contain the expected {expected_script} script")
    if source_headings and len(source_headings) != len(translated_headings):
        message = "translated heading count differs from source"
        if require_parity:
            report.fail(message)
        else:
            report.warnings.append(message)
    return report
