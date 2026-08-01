"""Small response parsers that keep provider text separate from typed payloads."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .artifacts import sha256_file
from .quality import QualityReport, validate_generated_text, validate_translation


@dataclass(frozen=True)
class ResearchResponse:
    content: str
    citations: tuple[str, ...]
    quality: QualityReport

    def as_dict(self) -> dict[str, object]:
        return {
            "content": self.content,
            "citations": list(self.citations),
            "quality": self.quality.as_dict(),
        }


@dataclass(frozen=True)
class CurriculumResponse:
    sections: dict[str, str]
    quality: QualityReport

    def as_dict(self) -> dict[str, object]:
        return {"sections": dict(self.sections), "quality": self.quality.as_dict()}


@dataclass(frozen=True)
class TranslationResponse:
    content: str
    target_language: str
    quality: QualityReport

    def as_dict(self) -> dict[str, object]:
        return {
            "content": self.content,
            "target_language": self.target_language,
            "quality": self.quality.as_dict(),
        }


@dataclass(frozen=True)
class VisualizationResponse:
    """Validated output contract for derived visualization artifacts."""

    output_paths: tuple[str, ...]
    quality: QualityReport

    def as_dict(self) -> dict[str, object]:
        return {
            "output_paths": list(self.output_paths),
            "quality": self.quality.as_dict(),
        }


def parse_research_response(content: str) -> ResearchResponse:
    quality = validate_generated_text(content, min_words=1)
    citations = tuple(
        sorted(
            {
                citation.rstrip(".,;:)]}")
                for citation in re.findall(r"https?://\S+|\[[0-9]+\]", content or "")
            }
        )
    )
    return ResearchResponse(content or "", citations, quality)


def parse_curriculum_response(content: str) -> CurriculumResponse:
    quality = validate_generated_text(content, min_words=1, require_sections=True)
    sections: dict[str, str] = {}
    current: str | None = None
    in_fence = False
    for line in (content or "").splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if match:
            name = match.group(1).strip()
            if name in sections:
                quality.warnings.append(f"curriculum contains duplicate section heading: {name}")
            else:
                sections.setdefault(name, "")
            current = name
        elif current is not None:
            sections[current] += line + "\n"
    sections = {name: text.strip() for name, text in sections.items() if text.strip()}
    if not sections and content.strip():
        quality.warnings.append("no non-empty Markdown sections were parsed")
    normalized = [re.sub(r"\s+", " ", value).casefold() for value in sections.values()]
    if len(normalized) != len(set(normalized)):
        quality.warnings.append("multiple curriculum sections contain duplicate content")
    return CurriculumResponse(sections, quality)


def parse_translation_response(
    source: str, content: str, target_language: str
) -> TranslationResponse:
    return TranslationResponse(
        content=content or "",
        target_language=target_language,
        quality=validate_translation(source, content or "", target_language),
    )


def parse_visualization_response(
    output_paths: Iterable[str],
    *,
    require_output: bool = True,
    require_manifest: bool = False,
) -> VisualizationResponse:
    """Validate visualization paths without interpreting their visual meaning."""

    report = QualityReport()
    paths = tuple(dict.fromkeys(str(path) for path in output_paths))
    report.metrics["output_count"] = len(paths)
    if require_output and not paths:
        report.fail("visualization stage produced no output artifacts")
    manifests = [
        Path(raw_path) for raw_path in paths if Path(raw_path).name == "visualization_manifest.json"
    ]
    if require_manifest and not manifests:
        report.fail("visualization stage produced no provenance manifest")
    allowed_suffixes = {".png", ".mmd", ".csv", ".json"}
    for raw_path in paths:
        path = Path(raw_path)
        if path.suffix.lower() not in allowed_suffixes:
            report.fail(f"unsupported visualization artifact type: {path.name}")
        if not path.is_file() or path.is_symlink():
            report.fail(f"visualization artifact is not a regular file: {raw_path}")
            continue
        if path.stat().st_size == 0:
            report.fail(f"visualization artifact is empty: {raw_path}")
        if path.suffix.lower() == ".png" and path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
            report.fail(f"visualization artifact is not a valid PNG: {raw_path}")
    for manifest_path in manifests:
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            report.fail(f"visualization manifest is unreadable: {manifest_path}: {exc}")
            continue
        if not isinstance(payload, dict) or payload.get("kind") != "visualization_bundle":
            report.fail(f"visualization manifest has an invalid kind: {manifest_path}")
            continue
        for record in payload.get("artifacts", []):
            if not isinstance(record, dict) or not isinstance(record.get("path"), str):
                report.fail(
                    "visualization manifest has an invalid artifact record: " f"{manifest_path}"
                )
                continue
            artifact = (manifest_path.parent / record["path"]).resolve()
            try:
                artifact.relative_to(manifest_path.parent.resolve())
            except ValueError:
                report.fail(f"visualization manifest escapes its bundle: {record['path']}")
                continue
            expected = record.get("sha256")
            if not artifact.is_file() or artifact.is_symlink() or not isinstance(expected, str):
                report.fail(
                    "visualization manifest references an invalid artifact: " f"{record['path']}"
                )
            elif sha256_file(artifact) != expected:
                report.fail(f"visualization manifest hash mismatch: {record['path']}")
    return VisualizationResponse(paths, report)
