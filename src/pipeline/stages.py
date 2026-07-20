"""Canonical filesystem stage helpers shared by CLI and workflow entrypoints."""

from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from src.common.io import read_text, safe_name
from src.common.logging_utils import setup_logging
from src.perplexity.clients import RequestLimiter
from src.perplexity.curriculum import process_research_file
from src.pipeline.provenance import file_input_record


def get_research_files(research_dir: Path, pattern: str = "*_research_*") -> list[Path]:
    if not research_dir.exists():
        return []
    files = [
        path for suffix in (".json", ".md") for path in research_dir.glob(f"{pattern}{suffix}")
    ]
    unique: dict[str, Path] = {}
    for path in sorted(
        (path for path in files if not path.name.startswith("not_research")),
        key=lambda candidate: (candidate.stem, candidate.suffix != ".json", candidate.name),
    ):
        # Domain research is published as a JSON/Markdown bundle.  Process
        # that bundle once, preferring JSON because it carries structured
        # metadata and the Markdown file remains available for review.
        unique.setdefault(path.stem, path)
    return sorted(unique.values())


def process_research_directory_detailed(
    client: Any,
    research_dir: Path,
    fep_actinf_file: Path,
    output_dir: Path,
    dir_type: str,
    *,
    skip_existing: bool = False,
    max_concurrent: int = 1,
    limiter: RequestLimiter | None = None,
    cancellation_event: threading.Event | None = None,
    **generation_options: Any,
) -> tuple[int, int, list[dict[str, Any]]]:
    """Process research inputs and retain item-level outputs and telemetry."""

    logger = setup_logging()

    def artifact_paths_for(curriculum_path: Path) -> list[str]:
        """Return the complete atomic bundle for one curriculum timestamp."""

        paths = [curriculum_path]
        sibling_json = curriculum_path.with_suffix(".json")
        if sibling_json.is_file():
            paths.append(sibling_json)
        prefix = "complete_curriculum_"
        timestamp = curriculum_path.stem.removeprefix(prefix)
        if timestamp:
            paths.extend(sorted(curriculum_path.parent.glob(f"section_*_{timestamp}.md")))
        return [str(path) for path in dict.fromkeys(paths)]

    if max_concurrent < 1:
        raise ValueError("max_concurrent must be at least one")
    if not research_dir.exists() or not fep_actinf_file.exists():
        files = get_research_files(research_dir)
        return (
            0,
            len(files),
            [
                {
                    "item_id": safe_name(path.stem.split("_research_", 1)[0]).casefold(),
                    "status": "failed",
                    "errors": [f"missing {dir_type} research input or foundation file"],
                    "input_hashes": {},
                }
                for path in files
            ],
        )
    active: list[Path] = []
    skipped: list[dict[str, Any]] = []
    for path in get_research_files(research_dir):
        item_id = safe_name(path.stem.split("_research_", 1)[0]).casefold()
        source_hash = file_input_record(path, label="research")["sha256"]
        existing = list((output_dir / item_id).glob("complete_curriculum_*.md"))
        if skip_existing and existing:
            skipped.append(
                {
                    "item_id": item_id,
                    "status": "skipped",
                    "output_paths": [
                        output_path
                        for curriculum_path in existing
                        for output_path in artifact_paths_for(curriculum_path)
                    ],
                    "provenance": {"mode": "existing_output"},
                    "input_hashes": {
                        "research": source_hash,
                        "fep_actinf": file_input_record(fep_actinf_file, label="fep_actinf")[
                            "sha256"
                        ],
                    },
                }
            )
        elif path.stat().st_size > 0:
            active.append(path)
        else:
            skipped.append(
                {
                    "item_id": item_id,
                    "status": "failed",
                    "errors": ["research input is empty"],
                    "input_hashes": {
                        "research": source_hash,
                        "fep_actinf": file_input_record(fep_actinf_file, label="fep_actinf")[
                            "sha256"
                        ],
                    },
                }
            )

    def process(path: Path) -> dict[str, Any]:
        item_id = safe_name(path.stem.split("_research_", 1)[0]).casefold()
        try:
            if cancellation_event is not None and cancellation_event.is_set():
                return {
                    "item_id": item_id,
                    "status": "failed",
                    "errors": ["run cancelled before provider request"],
                    "input_hashes": {
                        "research": file_input_record(path, label="research")["sha256"]
                    },
                }
            output_path = process_research_file(
                client,
                str(path),
                str(fep_actinf_file),
                str(output_dir),
                **generation_options,
                limiter=limiter,
                cancellation_event=cancellation_event,
            )
            logger.info("Processed %s research item %s", dir_type, item_id)
            if output_path is None:
                raise ValueError("processing completed without publishing an output")
            output_paths = artifact_paths_for(Path(output_path))
            json_path = Path(output_path).with_suffix(".json")
            provenance: dict[str, Any] = {
                "inputs": [
                    file_input_record(path, label="research"),
                    file_input_record(fep_actinf_file, label="fep_actinf"),
                ],
            }
            usage: dict[str, Any] = {}
            if json_path.is_file():
                try:
                    payload = json.loads(json_path.read_text(encoding="utf-8"))
                    metadata = payload.get("metadata", {})
                    if isinstance(metadata, dict):
                        provenance.update(metadata)
                        usage = dict(metadata.get("usage", {}))
                except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                    provenance["metadata_warning"] = "published metadata could not be parsed"
            return {
                "item_id": item_id,
                "status": "success",
                "output_paths": output_paths,
                "provenance": provenance,
                "usage": usage,
                "input_hashes": {
                    "research": file_input_record(path, label="research")["sha256"],
                    "fep_actinf": file_input_record(fep_actinf_file, label="fep_actinf")["sha256"],
                },
            }
        except Exception as exc:
            logger.error("Failed %s research item %s: %s", dir_type, item_id, exc)
            return {"item_id": item_id, "status": "failed", "errors": [str(exc)]}

    with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        outcomes = list(executor.map(process, active))
    items = [*outcomes, *skipped]
    successes = sum(item.get("status") == "success" for item in items)
    failures = sum(item.get("status") == "failed" for item in items)
    return successes, failures, items


def read_curriculum_inputs(curriculum_dir: Path) -> list[tuple[str, str, Path]]:
    """Return stable item IDs, content, and source paths for visualization/translation."""

    records = []
    for path in sorted(curriculum_dir.glob("*/complete_curriculum_*.md")):
        content = read_text(path)
        if content.strip():
            records.append((path.parent.name, content, path))
    return records
