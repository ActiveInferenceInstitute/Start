"""Regenerate deterministic, explicitly synthetic pipeline fixtures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.common.io import safe_name, write_text
from src.pipeline import (
    PipelineRunner,
    StageItemResult,
    StageResult,
    StageSpec,
    parse_curriculum_response,
    validate_generated_text,
)
from src.pipeline.artifacts import sha256_file
from src.pipeline.provenance import input_record

EVIDENCE = {
    "evidence_status": "offline_fixture",
    "provider": "offline_reference",
    "live_evidence": False,
    "verification_status": "unverified",
}


def _item(
    stage: str, item_id: str, path: Path | list[Path], *, provenance: dict[str, Any]
) -> StageResult:
    paths = path if isinstance(path, list) else [path]
    output_paths = [str(item) for item in paths]
    return StageResult(
        stage,
        items={
            item_id: StageItemResult(
                item_id,
                output_paths=output_paths,
                artifact_hashes={item: sha256_file(Path(item)) for item in output_paths},
                provenance=provenance,
            )
        },
    )


def regenerate(
    output_dir: Path,
    *,
    domain: str = "offline_biochemistry",
    entity: str = "offline_learner",
    language: str = "Spanish",
    run_id: str = "offline-fixture",
) -> dict[str, Any]:
    """Generate one deterministic synthetic run and return its summary."""

    domain_id = safe_name(domain).casefold()
    entity_id = safe_name(entity).casefold()
    language_id = safe_name(language).casefold()
    item_id = f"{domain_id}:{entity_id}:{language_id}"
    root = output_dir.expanduser().resolve()
    # Keep the human-readable stable item ID in metadata while applying the
    # shared single-component naming policy to filesystem paths.
    run_root = root / "fixtures" / safe_name(item_id).casefold()
    source_path = run_root / "raw" / "source.json"
    prepared_path = run_root / "prepared" / "prompt.json"
    response_path = run_root / "processed" / "response.md"
    parsed_path = run_root / "parsed" / "response.json"
    rendered_path = run_root / "rendered" / "curriculum.md"
    translation_path = run_root / "rendered" / "translation.md"
    visualization_path = run_root / "rendered" / "visualization.json"

    runner = PipelineRunner(
        [
            StageSpec("acquire"),
            StageSpec("prepare", depends_on=("acquire",)),
            StageSpec("process", depends_on=("prepare",)),
            StageSpec("parse", depends_on=("process",)),
            StageSpec("render", depends_on=("parse",)),
        ],
        work_root=root / ".runs",
        run_id=run_id,
        offline=True,
        metadata={
            "project": "START",
            "fixture": True,
            "provider_metadata": {"offline": EVIDENCE},
            "prompt_versions": {"offline_fixture": "deterministic-v1"},
        },
    )

    def acquire(_context: Any) -> StageResult:
        payload = {
            "domain": domain,
            "entity": entity,
            "language": language,
            **EVIDENCE,
        }
        write_text(source_path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return _item("acquire", item_id, source_path, provenance=payload)

    def prepare(_context: Any) -> StageResult:
        payload = {
            "prompt_version": "deterministic-v1",
            "input": input_record(source_path.read_text(encoding="utf-8"), label="source"),
            "instruction": "Produce a short, structured offline curriculum fixture.",
            **EVIDENCE,
        }
        write_text(prepared_path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return _item("prepare", item_id, prepared_path, provenance=payload)

    def process(_context: Any) -> StageResult:
        content = (
            f"# {domain}\n\n"
            f"## Audience\n\n{entity}\n\n"
            "## Foundation\n\n"
            "This synthetic fixture describes a deterministic offline learning path.\n"
        )
        write_text(response_path, content)
        return _item("process", item_id, response_path, provenance=EVIDENCE)

    def parse(_context: Any) -> StageResult:
        response = parse_curriculum_response(response_path.read_text(encoding="utf-8"))
        quality = response.quality.as_dict()
        if not validate_generated_text(
            response_path.read_text(encoding="utf-8"), require_sections=True
        ).valid:
            return StageResult(
                "parse",
                items={
                    item_id: StageItemResult(item_id, "failed", errors=["fixture quality failed"])
                },
            )
        payload = {"sections": response.sections, "quality": quality, **EVIDENCE}
        write_text(parsed_path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return _item("parse", item_id, parsed_path, provenance=payload)

    def render(_context: Any) -> StageResult:
        parsed = json.loads(parsed_path.read_text(encoding="utf-8"))
        lines = [
            "---",
            "evidence_status: offline_fixture",
            "provider: offline_reference",
            "---",
            "",
        ]
        for name, content in parsed["sections"].items():
            lines.extend([f"# {name}", "", content, ""])
        write_text(rendered_path, "\n".join(lines))
        write_text(
            translation_path,
            "---\n"
            "language: Spanish\n"
            "script: Latin\n"
            "evidence_status: offline_fixture\n"
            "---\n\n"
            "# Traducción\n\n"
            "Esta es una traducción sintética y determinista de referencia.\n",
        )
        write_text(
            visualization_path,
            json.dumps(
                {
                    "item_id": item_id,
                    "type": "offline_fixture",
                    "sections": sorted(parsed["sections"]),
                    **EVIDENCE,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
        )
        return _item(
            "render",
            item_id,
            [rendered_path, translation_path, visualization_path],
            provenance=EVIDENCE,
        )

    result = runner.run(
        {
            "acquire": acquire,
            "prepare": prepare,
            "process": process,
            "parse": parse,
            "render": render,
        }
    )
    return result.as_dict()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("data/offline_fixtures"))
    parser.add_argument("--domain", default="offline_biochemistry")
    parser.add_argument("--entity", default="offline_learner")
    parser.add_argument("--language", default="Spanish")
    parser.add_argument("--run-id", default="offline-fixture")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args(argv)
    summary = regenerate(
        args.output_dir,
        domain=args.domain,
        entity=args.entity,
        language=args.language,
        run_id=args.run_id,
    )
    if args.json_output:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        status = "ok" if summary.get("ok") else "failed"
        print(f"offline fixture run {summary.get('run_id')}: {status}")
    return 0 if summary.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
