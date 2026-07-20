"""Validate generated research, curriculum, translation, and manifest outputs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from src.config.languages import get_script_mapping
from src.pipeline import validate_generated_text, validate_translation
from src.pipeline.artifacts import sha256_file

ROOTS = (
    "data/audience_research",
    "data/domain_research",
    "data/translated_curriculums",
    "data/written_curriculums",
    "data/visualizations",
)
RESEARCH_ROOTS = ("data/audience_research", "data/domain_research")
_NON_ARTIFACT_FILENAMES = {"README.md", "AGENTS.md"}


def _has_symlink_boundary(path: Path, root: Path) -> bool:
    return any(parent != root and parent.is_symlink() for parent in path.parents)


def _metadata(payload: Any) -> dict[str, Any]:
    value = payload.get("metadata", {}) if isinstance(payload, dict) else {}
    return value if isinstance(value, dict) else {}


def _frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    lines = text.splitlines()[1:]
    result: dict[str, str] = {}
    for line in lines:
        if line.strip() == "---":
            break
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip()
    return result


def validate_outputs(root: Path, *, publication: bool = False) -> dict[str, Any]:
    """Return deterministic structural findings without changing generated files."""

    files: list[dict[str, Any]] = []
    for relative in ROOTS:
        directory = root / relative
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*")):
            if path.name in _NON_ARTIFACT_FILENAMES or ".runs" in path.parts:
                continue
            if path.is_symlink():
                files.append(
                    {
                        "path": path.relative_to(root).as_posix(),
                        "valid": False,
                        "errors": ["output contains a symlink boundary"],
                        "warnings": [],
                        "metrics": {},
                    }
                )
                continue
            if not path.is_file():
                continue
            finding: dict[str, Any] = {
                "path": path.relative_to(root).as_posix(),
                "valid": True,
                "errors": [],
                "warnings": [],
                "metrics": {},
            }
            relative_path = path.relative_to(root).as_posix()
            if _has_symlink_boundary(path, root):
                finding["valid"] = False
                finding["errors"].append("output crosses a symlink boundary")
                files.append(finding)
                continue
            if path.suffix.lower() == ".png":
                try:
                    content_bytes = path.read_bytes()
                except OSError as exc:
                    finding["valid"] = False
                    finding["errors"].append(f"unreadable output: {exc}")
                else:
                    if not content_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
                        finding["valid"] = False
                        finding["errors"].append("file is not a PNG image")
                files.append(finding)
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                finding["valid"] = False
                finding["errors"].append(f"unreadable output: {exc}")
                files.append(finding)
                continue
            if not text.strip():
                finding["valid"] = False
                finding["errors"].append("output is empty")
            if path.suffix.lower() == ".json":
                try:
                    payload = json.loads(text)
                except json.JSONDecodeError as exc:
                    finding["valid"] = False
                    finding["errors"].append(f"invalid JSON: {exc.msg}")
                    files.append(finding)
                    continue
                if path.name == "visualization_manifest.json":
                    if payload.get("schema_version") != "1.0":
                        finding["valid"] = False
                        finding["errors"].append(
                            "visualization manifest schema_version must be '1.0'"
                        )
                    if payload.get("kind") != "visualization_bundle":
                        finding["valid"] = False
                        finding["errors"].append(
                            "visualization manifest kind must be 'visualization_bundle'"
                        )
                    for record in payload.get("artifacts", []):
                        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
                            finding["valid"] = False
                            finding["errors"].append(
                                "visualization manifest contains an invalid artifact record"
                            )
                            continue
                        artifact_path = (path.parent / record["path"]).resolve()
                        try:
                            artifact_path.relative_to(path.parent.resolve())
                        except ValueError:
                            finding["valid"] = False
                            finding["errors"].append(
                                f"visualization manifest artifact escapes bundle: {record['path']}"
                            )
                            continue
                        if not artifact_path.is_file() or artifact_path.is_symlink():
                            finding["valid"] = False
                            finding["errors"].append(
                                f"visualization manifest artifact is missing: {record['path']}"
                            )
                            continue
                        expected = record.get("sha256")
                        if not isinstance(expected, str) or sha256_file(artifact_path) != expected:
                            finding["valid"] = False
                            finding["errors"].append(
                                f"visualization manifest hash mismatch: {record['path']}"
                            )
                    finding["metrics"] = {
                        "input_count": len(payload.get("inputs", [])),
                        "artifact_count": len(payload.get("artifacts", [])),
                    }
                    files.append(finding)
                    continue
                metadata = _metadata(payload)
                if any(relative_path.startswith(root) for root in RESEARCH_ROOTS):
                    research_text = "\n\n".join(
                        str(payload.get(key, ""))
                        for key in ("research_data", "domain_analysis", "curriculum_content")
                        if isinstance(payload.get(key), str)
                    )
                    research_quality = validate_generated_text(
                        research_text,
                        min_words=1,
                        require_citations=publication,
                    )
                    finding["metrics"]["research_quality"] = research_quality.metrics
                    if not research_quality.valid:
                        finding["valid"] = False
                        finding["errors"].extend(research_quality.errors)
                    elif not research_quality.metrics.get("citation_count"):
                        finding["warnings"].append(
                            "research output has no citation marker or source URL"
                        )
                if path.name.startswith("complete_curriculum_"):
                    if not isinstance(payload.get("sections"), dict) or not payload["sections"]:
                        finding["valid"] = False
                        finding["errors"].append("curriculum JSON has no sections")
                if not metadata.get("evidence_status") or not metadata.get("provider"):
                    finding["warnings"].append("missing evidence_status or provider metadata")
                if publication and finding["warnings"]:
                    finding["valid"] = False
                    finding["errors"].extend(finding["warnings"])
            elif path.suffix.lower() == ".md":
                is_research = any(relative_path.startswith(root) for root in RESEARCH_ROOTS)
                report = validate_generated_text(
                    text,
                    min_words=1,
                    require_citations=publication and is_research,
                )
                finding["metrics"] = report.metrics
                finding["warnings"].extend(report.warnings)
                if not report.valid:
                    finding["valid"] = False
                    finding["errors"].extend(report.errors)
                if is_research:
                    frontmatter = _frontmatter(text)
                    for key in ("evidence_status", "provider"):
                        if not frontmatter.get(key):
                            finding["warnings"].append(f"research missing {key} metadata")
                if "translated_curriculums" in path.as_posix():
                    frontmatter = _frontmatter(text)
                    for key in ("language", "script", "evidence_status"):
                        if not frontmatter.get(key):
                            finding["warnings"].append(f"translation missing {key} metadata")
                    language = frontmatter.get("language")
                    script = frontmatter.get("script")
                    if language and script:
                        try:
                            expected_script = get_script_mapping(language)
                        except (OSError, ValueError, KeyError):
                            expected_script = script
                        if script != expected_script:
                            finding["warnings"].append(
                                "translation script does not match configured mapping for "
                                f"{language}"
                            )
                    entity_name = path.stem.split("_curriculum_", 1)[0]
                    source_candidates = sorted(
                        (root / "data" / "written_curriculums" / entity_name).glob(
                            "complete_curriculum_*.md"
                        )
                    )
                    if source_candidates:
                        translation_quality = validate_translation(
                            source_candidates[-1].read_text(encoding="utf-8"),
                            text,
                            language or "",
                            require_parity=publication,
                        )
                        finding["metrics"]["translation_quality"] = translation_quality.metrics
                        finding["warnings"].extend(translation_quality.warnings)
                        if not translation_quality.valid:
                            finding["valid"] = False
                            finding["errors"].extend(translation_quality.errors)
                    if publication and finding["warnings"]:
                        finding["valid"] = False
                        finding["errors"].extend(finding["warnings"])
            elif path.suffix.lower() == ".csv":
                try:
                    rows = list(csv.reader(text.splitlines()))
                except csv.Error as exc:
                    finding["valid"] = False
                    finding["errors"].append(f"invalid CSV: {exc}")
                else:
                    if not rows or not any(cell.strip() for cell in rows[0]):
                        finding["valid"] = False
                        finding["errors"].append("CSV has no header")
                    finding["metrics"] = {"row_count": max(0, len(rows) - 1)}
            elif path.suffix.lower() == ".mmd":
                if not any(marker in text for marker in ("flowchart", "graph", "sequenceDiagram")):
                    finding["valid"] = False
                    finding["errors"].append("Mermaid file has no recognized diagram declaration")
            files.append(finding)

    return {
        "schema_version": "1.0",
        "publication_mode": publication,
        "summary": {
            "file_count": len(files),
            "valid_count": sum(bool(item["valid"]) for item in files),
            "invalid_count": sum(not item["valid"] for item in files),
            "warning_count": sum(bool(item["warnings"]) for item in files),
        },
        "files": files,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--publication", action="store_true")
    args = parser.parse_args(argv)
    report = validate_outputs(args.root.expanduser().resolve(), publication=args.publication)
    if args.json_output:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        summary = report["summary"]
        print(
            f"Validated {summary['file_count']} outputs; "
            f"{summary['invalid_count']} invalid; {summary['warning_count']} with warnings"
        )
    if args.check and report["summary"]["invalid_count"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
