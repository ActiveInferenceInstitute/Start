from __future__ import annotations

import json

import pytest

from src.pipeline import parse_visualization_response
from src.visualization.runner import (
    collect_curriculum_files,
    generate_curriculum_metrics,
    run,
)


def test_run_honors_input_and_output_roots(tmp_path) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    curriculum_dir = input_root / "reader"
    curriculum_dir.mkdir(parents=True)
    (curriculum_dir / "complete_curriculum_1.md").write_text(
        "# Title\n\nA useful curriculum paragraph.", encoding="utf-8"
    )
    output_paths = run(str(input_root), str(output_root))
    metrics = output_root / "metrics" / "curriculum_metrics.csv"
    assert metrics.exists()
    assert "Item ID" in metrics.read_text(encoding="utf-8")
    assert (output_root / "metrics" / "curriculum_metrics.json").exists()
    assert (
        (output_root / "charts" / "curriculum_metrics.png")
        .read_bytes()
        .startswith(b"\x89PNG\r\n\x1a\n")
    )
    assert (
        (output_root / "diagrams" / "reader_flow.mmd")
        .read_text(encoding="utf-8")
        .startswith("flowchart")
    )
    manifest = json.loads((output_root / "visualization_manifest.json").read_text(encoding="utf-8"))
    assert manifest["kind"] == "visualization_bundle"
    assert manifest["inputs"][0]["item_id"] == "reader"
    assert all(record["sha256"] for record in manifest["artifacts"])
    parsed = parse_visualization_response(output_paths, require_manifest=True)
    assert parsed.quality.valid
    (output_root / "charts" / "curriculum_metrics.png").write_bytes(b"tampered")
    invalid = parse_visualization_response(output_paths, require_manifest=True)
    assert not invalid.quality.valid
    assert not (tmp_path / "data" / "written_curriculums").exists()


def test_collect_does_not_create_missing_input(tmp_path) -> None:
    missing = tmp_path / "missing"
    assert collect_curriculum_files(str(missing)) == []
    assert not missing.exists()


def test_metrics_require_matching_labels(tmp_path) -> None:
    with pytest.raises(ValueError, match="equal lengths"):
        generate_curriculum_metrics(["text"], [], str(tmp_path))

    with pytest.raises(ValueError, match="non-empty strings"):
        generate_curriculum_metrics(["text"], [""], str(tmp_path))


def test_run_returns_empty_without_curricula(tmp_path) -> None:
    assert run(str(tmp_path / "input"), str(tmp_path / "output")) == []


def test_repeated_display_labels_get_collision_safe_ids(tmp_path) -> None:
    input_root = tmp_path / "input" / "reader"
    input_root.mkdir(parents=True)
    for suffix in ("one", "two"):
        (input_root / f"complete_curriculum_{suffix}.md").write_text(
            f"# {suffix}\n\nContent for {suffix}.", encoding="utf-8"
        )

    output_root = tmp_path / "output"
    run(str(tmp_path / "input"), str(output_root))
    manifest = json.loads((output_root / "visualization_manifest.json").read_text(encoding="utf-8"))
    ids = [record["item_id"] for record in manifest["inputs"]]
    assert len(ids) == len(set(ids)) == 2
    assert len(list((output_root / "diagrams").glob("reader-*_flow.mmd"))) == 2
