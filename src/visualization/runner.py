from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import List, Tuple

import matplotlib.pyplot as plt
import pandas as pd

from src.common.io import ensure_directory, write_json, write_text
from src.config.schemas import stable_identifier
from src.pipeline.artifacts import sha256_file

logger = logging.getLogger(__name__)


def collect_curriculum_files(base_dir: str) -> List[Tuple[str, str]]:
    curriculum_dir = Path(base_dir)
    if not curriculum_dir.exists():
        return []
    files: List[Tuple[str, str]] = []
    for curr_file in sorted(curriculum_dir.rglob("complete_curriculum_*.md")):
        files.append((curr_file.parent.name, str(curr_file)))
    return files


def generate_curriculum_metrics(
    curriculum_docs: List[str],
    entity_labels: List[str],
    output_dir: str,
    item_ids: List[str] | None = None,
) -> None:
    if len(curriculum_docs) != len(entity_labels):
        raise ValueError("curriculum_docs and entity_labels must have equal lengths")
    if any(not isinstance(label, str) or not label.strip() for label in entity_labels):
        raise ValueError("entity_labels must contain non-empty strings")
    if item_ids is not None and len(item_ids) != len(entity_labels):
        raise ValueError("item_ids and entity_labels must have equal lengths")
    metrics = []
    import re

    for i, curriculum in enumerate(curriculum_docs):
        words = len(curriculum.split())
        sections = len(re.findall(r"^#+\s+(.+)$", curriculum, re.MULTILINE))
        paragraphs = len(re.split(r"\n\s*\n", curriculum))
        metrics.append(
            {
                "Item ID": (
                    item_ids[i] if item_ids is not None else stable_identifier(entity_labels[i])
                ),
                "Entity": entity_labels[i],
                "Total Words": words,
                "Sections": sections,
                "Paragraphs": paragraphs,
                "Words per Section": words / max(sections, 1),
                "Words per Paragraph": words / max(paragraphs, 1),
            }
        )
    df = pd.DataFrame(metrics)
    output_path = Path(output_dir)
    ensure_directory(output_path)
    write_text(output_path / "curriculum_metrics.csv", df.to_csv(index=False))
    write_json(
        output_path / "curriculum_metrics.json",
        {
            "schema_version": "1.0",
            "kind": "curriculum_metrics",
            "evidence_status": "derived_visualization",
            "records": metrics,
        },
    )


def _flow_diagram(entity: str, content: str) -> str:
    """Create a bounded, deterministic Mermaid flow for one curriculum."""

    sections = re.findall(r"^#+\s+(.+)$", content, re.MULTILINE)
    lines = [
        "flowchart TD",
        f'    A["{entity.replace(chr(34), chr(39))}<br/>Curriculum"] --> B["Foundation"]',
    ]
    previous = "B"
    for index, section in enumerate(sections, start=1):
        node = f"S{index}"
        label = section.replace('"', "'").strip()
        if len(label) > 42:
            label = label[:39] + "..."
        lines.append(f'    {previous} --> {node}["{label}"]')
        previous = node
    lines.append(f'    {previous} --> Z["Mastery / review"]')
    return "\n".join(lines) + "\n"


def _structure_diagram(records: list[dict[str, object]]) -> str:
    """Create a deterministic overview diagram from metric records."""

    lines = [
        "graph TB",
        '    START["START curriculum evidence"]',
    ]
    for index, record in enumerate(records, start=1):
        node = f"C{index}"
        entity = str(record["Entity"]).replace('"', "'")
        sections = int(str(record["Sections"]))
        lines.append(f'    START --> {node}["{entity}<br/>{sections} sections"]')
    return "\n".join(lines) + "\n"


def _item_identifier(label: str, path: Path, label_counts: dict[str, int]) -> str:
    """Keep single-item IDs stable while making repeated inputs collision-safe."""

    if label_counts.get(label, 0) == 1:
        return stable_identifier(label)
    return stable_identifier(f"{label}-{path.stem}")


def _metrics_chart(records: list[dict[str, object]], output_path: Path) -> None:
    """Render a small deterministic summary chart for the canonical pipeline."""

    if not records:
        raise ValueError("records cannot be empty")
    labels = [str(record["Entity"]) for record in records]
    values = [int(str(record["Total Words"])) for record in records]
    figure, axis = plt.subplots(figsize=(max(6, len(labels) * 1.2), 4.5))
    axis.bar(labels, values, color="#3568a8")
    axis.set_title("Curriculum volume by target")
    axis.set_ylabel("Words")
    axis.tick_params(axis="x", rotation=35)
    figure.tight_layout()
    ensure_directory(output_path.parent)
    figure.savefig(output_path, dpi=160, format="png")
    plt.close(figure)


def _manifest(
    input_root: Path,
    inputs: list[tuple[str, str, Path]],
    output_root: Path,
    output_paths: list[Path],
    item_ids: dict[Path, str],
) -> dict[str, object]:
    """Return a provenance manifest for derived visual artifacts."""

    input_records = []
    for _label, _content, path in inputs:
        input_records.append(
            {
                "item_id": item_ids[path],
                "path": path.resolve().relative_to(input_root.resolve()).as_posix(),
                "sha256": sha256_file(path),
            }
        )
    artifacts = []
    for path in sorted(output_paths):
        artifacts.append(
            {
                "path": path.resolve().relative_to(output_root.resolve()).as_posix(),
                "kind": path.suffix.lower().lstrip(".") or "file",
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    return {
        "schema_version": "1.0",
        "kind": "visualization_bundle",
        "evidence_status": "derived_visualization",
        "generator": "src.visualization.runner",
        "input_root": input_root.resolve().as_posix(),
        "inputs": input_records,
        "artifacts": artifacts,
        "reproducibility": {
            "ordering": "stable item identifier and relative artifact path",
            "source": "curriculum Markdown content and hashes",
            "semantic_limit": "charts summarize structure; they do not establish factual truth",
        },
    }


def run(input_root: str, output_root: str) -> list[str]:
    if not input_root or not output_root:
        raise ValueError("input_root and output_root are required")
    input_path = Path(input_root).expanduser()
    output_path = Path(output_root).expanduser()
    collected = collect_curriculum_files(str(input_path))
    if not collected:
        return []
    curriculums: list[str] = []
    labels: list[str] = []
    inputs: list[tuple[str, str, Path]] = []
    for entity, path in collected:
        try:
            source_path = Path(path)
            content = source_path.read_text(encoding="utf-8")
            curriculums.append(content)
            labels.append(entity)
            inputs.append((entity, content, source_path))
        except OSError as exc:
            # A single unreadable file must not discard an otherwise healthy
            # visualization bundle; skip it and continue.
            logger.warning("Skipping unreadable curriculum file %s: %s", path, exc)
            continue
    if not inputs:
        return []
    metrics_dir = output_path / "metrics"
    diagrams_dir = output_path / "diagrams"
    charts_dir = output_path / "charts"
    label_counts = {label: labels.count(label) for label in set(labels)}
    item_ids = {
        path: _item_identifier(label, path, label_counts) for label, _content, path in inputs
    }
    generate_curriculum_metrics(
        curriculums,
        labels,
        str(metrics_dir),
        [item_ids[path] for _label, _content, path in inputs],
    )
    records = []
    for content, label, (_input_label, _input_content, source_path) in zip(
        curriculums, labels, inputs, strict=True
    ):
        words = len(content.split())
        sections = len(re.findall(r"^#+\s+(.+)$", content, re.MULTILINE))
        paragraphs = len(re.split(r"\n\s*\n", content))
        records.append(
            {
                "Item ID": item_ids[source_path],
                "Entity": label,
                "Total Words": words,
                "Sections": sections,
                "Paragraphs": paragraphs,
                "Words per Section": words / max(sections, 1),
                "Words per Paragraph": words / max(paragraphs, 1),
            }
        )
    ensure_directory(diagrams_dir)
    diagram_paths: list[Path] = []
    for label, content, source_path in inputs:
        diagram_path = diagrams_dir / f"{item_ids[source_path]}_flow.mmd"
        write_text(diagram_path, _flow_diagram(label, content))
        diagram_paths.append(diagram_path)
    structure_path = diagrams_dir / "curriculum_structure.mmd"
    write_text(structure_path, _structure_diagram(records))
    chart_path = charts_dir / "curriculum_metrics.png"
    _metrics_chart(records, chart_path)
    output_files = [
        metrics_dir / "curriculum_metrics.csv",
        metrics_dir / "curriculum_metrics.json",
        *diagram_paths,
        structure_path,
        chart_path,
    ]
    manifest = _manifest(input_path, inputs, output_path, output_files, item_ids)
    manifest_path = output_path / "visualization_manifest.json"
    write_json(manifest_path, manifest)
    output_files.append(manifest_path)
    return [str(path) for path in sorted(output_files)]
