from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from src.common.config import _config_name, validate_config_data
from src.common.paths import find_repo_root
from src.common.prompts import (
    list_prompt_templates,
    load_prompt_template,
    render_prompt,
    save_prompt_template,
    substitute_variables,
    validate_prompt_template,
)
from src.config.languages import get_script_mapping, get_target_languages
from src.pipeline import (
    PipelineRunner,
    StageItemResult,
    StageResult,
    StageSpec,
    StageStatus,
    parse_curriculum_response,
    parse_visualization_response,
    validate_translation,
)
from src.pipeline.history import list_runs, retention_candidates


def test_paths_honor_only_valid_repository_override(monkeypatch, tmp_path: Path) -> None:
    valid = tmp_path / "repo"
    (valid / "src").mkdir(parents=True)
    (valid / "pyproject.toml").write_text("[project]\nname='fixture'\n", encoding="utf-8")
    monkeypatch.setenv("START_REPO_ROOT", str(valid))
    assert find_repo_root() == valid.resolve()

    invalid = tmp_path / "not-start"
    invalid.mkdir()
    monkeypatch.setenv("START_REPO_ROOT", str(invalid))
    with pytest.raises(RuntimeError, match="not a START project"):
        find_repo_root()


def test_prompt_store_and_strict_rendering(monkeypatch, tmp_path: Path) -> None:
    import src.common.prompts as prompts

    monkeypatch.setattr(prompts, "data_root", lambda: tmp_path)
    saved = save_prompt_template("fixture", "Hello {{ name }}")
    assert saved == tmp_path / "prompts" / "fixture.md"
    assert load_prompt_template("fixture") == "Hello {{ name }}"
    assert list_prompt_templates() == ["fixture"]
    assert render_prompt("fixture", {"name": "reader"}, strict=True) == "Hello reader"
    with pytest.raises(ValueError, match="Missing required"):
        render_prompt("fixture", {}, strict=True)
    with pytest.raises(ValueError, match="Invalid prompt"):
        load_prompt_template("../fixture")
    with pytest.raises(ValueError, match="Template cannot be empty"):
        substitute_variables("", {})
    assert substitute_variables("{{missing}}", {}) == "{{missing}}"


def test_prompt_validation_reports_empty_malformed_and_size_warnings() -> None:
    assert validate_prompt_template("")["valid"] is False
    malformed = validate_prompt_template("short { text {{")
    assert malformed["valid"] is True
    assert malformed["warnings"]
    long_template = validate_prompt_template("word " * 1001)
    assert any("long" in warning for warning in long_template["warnings"])


def test_config_names_and_values_fail_closed() -> None:
    with pytest.raises(ValueError, match="Invalid configuration name"):
        _config_name("../secrets")
    with pytest.raises(ValueError, match="Invalid configuration name"):
        _config_name("")
    with pytest.raises(ValueError, match="null value"):
        validate_config_data({"key": None}, "fixture")
    with pytest.raises(ValueError, match="must be a dictionary"):
        validate_config_data([], "fixture")  # type: ignore[arg-type]


def test_language_schema_supports_mapping_entries_and_rejects_bad_mappings() -> None:
    config = {
        "target_languages": [{"name": "Arabic", "script": "Arabic"}, "English"],
        "script_mappings": {"English": "Latin"},
    }
    assert get_target_languages(config) == ["Arabic", "English"]
    assert get_script_mapping("English", config) == "Latin"
    with pytest.raises(ValueError, match="non-empty string"):
        get_script_mapping("", config)
    with pytest.raises(ValueError, match="mapping"):
        get_script_mapping("English", {"script_mappings": []})


def test_parser_quality_refusal_paths_are_explicit(tmp_path: Path) -> None:
    parsed = parse_curriculum_response("plain text without headings")
    assert parsed.quality.valid is False
    duplicate = parse_curriculum_response("# A\n\nsame\n\n# B\n\nsame")
    assert any("duplicate" in warning for warning in duplicate.quality.warnings)

    missing = parse_visualization_response([], require_output=True, require_manifest=True)
    assert missing.quality.valid is False
    unsupported = parse_visualization_response([str(tmp_path / "bad.txt")])
    assert any("unsupported" in error for error in unsupported.quality.errors)

    translation = validate_translation("# A\nsource", "# A\nEnglish", "Arabic", require_parity=True)
    assert translation.valid is False


def test_runner_handles_disabled_missing_handler_and_cancellation(tmp_path: Path) -> None:
    disabled = PipelineRunner(
        [StageSpec("disabled", enabled=False, required=False)],
        work_root=tmp_path / "runs",
        run_id="disabled",
    ).run({})
    assert disabled.ok
    assert disabled.stages[0].status == StageStatus.SKIPPED

    missing = PipelineRunner(
        [StageSpec("missing")], work_root=tmp_path / "runs", run_id="missing"
    ).run({})
    assert missing.ok is False
    assert "no handler" in missing.stages[0].errors[0]

    cancelled = threading.Event()
    cancelled.set()
    result = PipelineRunner(
        [StageSpec("cancelled")],
        work_root=tmp_path / "runs",
        run_id="cancelled",
        cancellation_event=cancelled,
    ).run({"cancelled": lambda _ctx: StageResult("cancelled")})
    assert result.ok is False
    assert result.stages[0].status == StageStatus.BLOCKED


def test_runner_rejects_manifest_digest_mismatch_and_invalid_artifact(tmp_path: Path) -> None:
    run_root = tmp_path / "runs"
    output = tmp_path / "output.txt"

    def write(_ctx):
        output.write_text("content", encoding="utf-8")
        return StageResult(
            "write",
            items={"item": StageItemResult("item", output_paths=[str(output)])},
        )

    PipelineRunner([StageSpec("write")], work_root=run_root, run_id="digest").run({"write": write})
    manifest_path = run_root / "digest" / "manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["config_digest"] = "wrong"
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="configuration digest"):
        PipelineRunner([StageSpec("write")], work_root=run_root, run_id="digest").run(
            {"write": write}
        )


def test_history_rejects_symlink_root_and_ignores_invalid_manifests(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    (real / "broken").mkdir()
    (real / "broken" / "manifest.json").write_text("not-json", encoding="utf-8")
    assert list_runs(real) == []
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    with pytest.raises(ValueError, match="cannot be a symlink"):
        list_runs(link)
    assert retention_candidates([], keep=0, older_than_days=0) == []
