"""Tests for the ``start-gnn`` orchestrator.

The fixtures here are real: real git repositories, a real pipeline entry-point
script that writes the same summary files the GNN pipeline writes, and real
subprocess execution.  Every test drives the code under test directly.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.gnn import config, utils
from src.gnn.main import (
    EXIT_OK,
    EXIT_PIPELINE_FAILED,
    EXIT_REFUSED,
    build_pipeline_command,
    checkout_status,
    main,
    registered_revision,
    resolve_gnn_checkout,
    resolve_interpreter,
    run_pipeline,
    summarize_outputs,
)
from src.repos.cloning import (
    REVISION_AHEAD_OF_RECORDED,
    REVISION_AT_RECORDED,
    REVISION_DIVERGED,
    REVISION_UNKNOWN,
    get_repository_revision_info,
)

FAKE_PIPELINE = '''"""Minimal stand-in for the GNN pipeline entry point (test fixture)."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


def write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only-steps", required=True)
    parser.add_argument("--target-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    steps = [int(part) for part in args.only_steps.split(",") if part.strip()]
    target = Path(args.target_dir)
    output = Path(args.output_dir)
    models = sorted(target.glob("*.md"))
    selection = [
        {
            "relative_path": model.name,
            "model_id": f"{model.stem}-deadbeef0000",
            "sha256": sha256(model),
            "steps": steps,
        }
        for model in models
    ]
    write(
        output / "00_pipeline_summary" / "pipeline_execution_summary.json",
        {
            "overall_status": "SUCCESS",
            "run_id": "fixture-run",
            "total_duration_seconds": 1.5,
            "planned_steps": [f"{step}_fixture.py" for step in steps],
            "unfinished_steps": [],
            "performance_summary": {"total_steps": len(steps), "failed_steps": 0},
            "steps": [
                {
                    "step_number": index,
                    "script_name": f"{step}_fixture.py",
                    "status": "SUCCESS",
                    "duration_seconds": 0.5,
                    "exit_code": 0,
                }
                for index, step in enumerate(steps, start=1)
            ],
            "model_selection": selection,
        },
    )
    write(
        output / "3_gnn_output" / "gnn_processing_summary.json",
        {"total_files": len(models), "successful_parses": len(models), "failed_parses": 0},
    )
    write(
        output / "5_type_checker_output" / "type_check_summary.json",
        {"files_processed": len(models), "success": True, "invalid_files": 0},
    )
    write(
        output / "11_render_output" / "render_processing_summary.json",
        {"total_files": len(models), "successful_files": len(models), "failed_files": 0},
    )
    write(
        output / "12_execute_output" / "summaries" / "execution_summary.json",
        {"status": "success", "success": True, "successful_executions": len(models)},
    )
    print(f"fixture pipeline finished for {len(models)} model(s) in {output}")
    return int(os.environ.get("FAKE_GNN_EXIT_CODE", "0"))


if __name__ == "__main__":
    raise SystemExit(main())
'''


def _git(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _make_checkout(tmp_path: Path, name: str = "gnn") -> Path:
    """Create a real git checkout containing the fixture pipeline entry point."""
    checkout = tmp_path / name
    (checkout / "src" / "gnn").mkdir(parents=True)
    (checkout / "input" / "gnn_files" / "basics").mkdir(parents=True)
    (checkout / "src" / "gnn" / "main.py").write_text(FAKE_PIPELINE, encoding="utf-8")
    (checkout / "input" / "gnn_files" / "basics" / "static_perception.md").write_text(
        "ModelName: static_perception\n", encoding="utf-8"
    )
    (checkout / "input" / "gnn_files" / "basics" / "dynamic_perception.md").write_text(
        "ModelName: dynamic_perception\n", encoding="utf-8"
    )
    _git("init", "-b", "main", str(checkout))
    _git("config", "user.email", "tests@example.invalid", cwd=checkout)
    _git("config", "user.name", "START tests", cwd=checkout)
    _git("add", ".", cwd=checkout)
    _git("commit", "-m", "checkout fixture", cwd=checkout)
    return checkout


def _commit(checkout: Path, name: str = "follow-up.txt") -> str:
    (checkout / name).write_text("follow up\n", encoding="utf-8")
    _git("add", ".", cwd=checkout)
    _git("commit", "-m", "follow up", cwd=checkout)
    return _git("rev-parse", "HEAD", cwd=checkout)


def test_registered_revision_is_the_gnn_pin():
    assert registered_revision() == "8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1"


def test_resolve_gnn_checkout_prefers_explicit_path(tmp_path):
    explicit = tmp_path / "somewhere"
    assert resolve_gnn_checkout(explicit, tmp_path) == explicit.resolve()
    assert resolve_gnn_checkout(None, tmp_path) == (tmp_path / "gnn").resolve()


def test_resolve_interpreter_prefers_checkout_venv(tmp_path):
    checkout = tmp_path / "gnn"
    venv_python = checkout / ".venv" / "bin" / "python"
    venv_python.parent.mkdir(parents=True)
    venv_python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    venv_python.chmod(0o755)
    command, source = resolve_interpreter(checkout)
    assert source == "checkout-venv"
    assert command == [str(venv_python)]
    override, override_source = resolve_interpreter(checkout, "/usr/bin/python3")
    assert (override, override_source) == (["/usr/bin/python3"], "explicit")
    empty_checkout = tmp_path / "empty"
    empty_checkout.mkdir()
    fallback, fallback_source = resolve_interpreter(empty_checkout)
    assert fallback_source in {"uv-no-sync", "start-interpreter"}
    assert fallback


def test_build_pipeline_command_uses_registered_steps(tmp_path):
    command = build_pipeline_command(
        ["python"],
        (3, 5, 11, 12),
        tmp_path / "input" / "gnn_files" / "basics",
        tmp_path / "output",
    )
    assert command[1] == config.PIPELINE_SCRIPT
    assert command[command.index("--only-steps") + 1] == "3,5,11,12"
    assert command[command.index("--target-dir") + 1].endswith("basics")
    assert command[command.index("--output-dir") + 1] == str(tmp_path / "output")


def test_checkout_status_reports_revision_relationship(tmp_path):
    checkout = _make_checkout(tmp_path)
    head = _git("rev-parse", "HEAD", cwd=checkout)

    at_revision = checkout_status(checkout)
    assert at_revision["is_git_repo"] is True
    assert at_revision["has_pipeline_script"] is True

    ahead = get_repository_revision_info(checkout, _commit(checkout))
    assert ahead["relation"] == REVISION_AT_RECORDED
    followed = _commit(checkout, "second.txt")
    ahead = get_repository_revision_info(checkout, head)
    assert ahead["relation"] == REVISION_AHEAD_OF_RECORDED
    assert ahead["head"] == followed
    assert ahead["revision_object_present"] is True

    unknown = get_repository_revision_info(checkout, "0" * 40)
    assert unknown["relation"] == REVISION_UNKNOWN
    assert unknown["revision_object_present"] is False
    assert "absent locally" in unknown["detail"]

    assert get_repository_revision_info(checkout, "not-a-sha")["relation"] == REVISION_UNKNOWN
    assert get_repository_revision_info(checkout, "")["relation"] == REVISION_UNKNOWN


def test_revision_relationship_detects_divergence(tmp_path):
    checkout = _make_checkout(tmp_path)
    _git("checkout", "-b", "side", cwd=checkout)
    side = _commit(checkout, "side.txt")
    _git("checkout", "main", cwd=checkout)
    main_head = _commit(checkout, "main.txt")
    assert side != main_head
    diverged = get_repository_revision_info(checkout, side)
    assert diverged["relation"] == REVISION_DIVERGED
    assert diverged["revision_object_present"] is True


def test_revision_info_rejects_non_repository(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    info = get_repository_revision_info(plain, "a" * 40)
    assert info["relation"] == REVISION_UNKNOWN
    assert info["head"] is None


def test_run_pipeline_end_to_end_writes_receipts(tmp_path):
    checkout = _make_checkout(tmp_path)
    output_dir = tmp_path / "run-output"
    report = run_pipeline(
        checkout=checkout,
        steps="3,5,11,12",
        target="input/gnn_files/basics",
        output_dir=output_dir,
        interpreter_override=sys.executable,
    )

    assert report["status"] == "ok", report
    assert report["execution"]["exit_code"] == 0
    assert report["steps"] == [3, 5, 11, 12]
    assert report["interpreter"]["source"] == "explicit"

    artifacts = report["artifacts"]
    assert all(artifact["exists"] for artifact in artifacts.values())
    assert artifacts["parse"]["counts"] == {
        "total_files": 2,
        "successful_parses": 2,
        "failed_parses": 0,
    }
    assert artifacts["pipeline"]["counts"]["overall_status"] == "SUCCESS"
    assert len(artifacts["pipeline"]["sha256"]) == 64

    consumed = report["model_selection"]
    assert {entry["relative_path"] for entry in consumed} == {
        "static_perception.md",
        "dynamic_perception.md",
    }
    for entry in consumed:
        source = checkout / entry["relative_path"]
        if not source.is_file():
            source = checkout / "input" / "gnn_files" / "basics" / entry["relative_path"]
        assert utils.sha256_file(source) == entry["sha256"]

    step_records = report["pipeline_steps"]
    assert [record["step_number"] for record in step_records] == [1, 2, 3, 4]
    assert {record["status"] for record in step_records} == {"SUCCESS"}

    receipts = report["receipts"]
    summary = json.loads(Path(receipts["summary"]).read_text(encoding="utf-8"))
    assert summary["status"] == "ok"
    assert Path(receipts["stdout"]).read_text(encoding="utf-8")
    assert (output_dir / config.STDOUT_RECEIPT_NAME).is_file()


def test_run_pipeline_reports_pipeline_failure(tmp_path, monkeypatch):
    checkout = _make_checkout(tmp_path)
    monkeypatch.setenv("FAKE_GNN_EXIT_CODE", "3")
    report = run_pipeline(
        checkout=checkout,
        output_dir=tmp_path / "failed-run",
        interpreter_override=sys.executable,
    )
    assert report["status"] == "failed"
    assert report["execution"]["exit_code"] == 3
    assert "exited with code 3" in report["reason"]


def test_run_pipeline_warns_when_pipeline_reports_warnings(tmp_path):
    checkout = _make_checkout(tmp_path)
    pipeline = checkout / "src" / "gnn" / "main.py"
    pipeline.write_text(
        FAKE_PIPELINE.replace(
            '"overall_status": "SUCCESS"', '"overall_status": "SUCCESS_WITH_WARNINGS"'
        ),
        encoding="utf-8",
    )
    report = run_pipeline(
        checkout=checkout,
        output_dir=tmp_path / "warned-run",
        interpreter_override=sys.executable,
    )
    assert report["status"] == "ok-with-warnings"
    assert report["pipeline_status"] == config.STATUS_WITH_WARNINGS


def test_run_pipeline_refuses_without_target_or_checkout(tmp_path):
    checkout = _make_checkout(tmp_path)
    missing_target = run_pipeline(
        checkout=checkout,
        target="input/gnn_files/absent",
        output_dir=tmp_path / "nope",
        interpreter_override=sys.executable,
    )
    assert missing_target["status"] == "refused"
    assert "target directory does not exist" in missing_target["reason"]

    absent = run_pipeline(checkout=tmp_path / "missing", interpreter_override=sys.executable)
    assert absent["status"] == "refused"
    assert "does not exist" in absent["reason"]

    bad_steps = run_pipeline(checkout=checkout, steps="three", interpreter_override=sys.executable)
    assert bad_steps["status"] == "refused"
    assert "Invalid pipeline step" in bad_steps["reason"]


def test_run_pipeline_require_pin_refuses_advanced_checkout(tmp_path):
    checkout = _make_checkout(tmp_path)
    pinned_head = _git("rev-parse", "HEAD", cwd=checkout)
    _commit(checkout, "later.txt")

    advanced = run_pipeline(
        checkout=checkout,
        output_dir=tmp_path / "pinned-run",
        interpreter_override=sys.executable,
        require_pin=True,
        base_dir=tmp_path,
        revision=pinned_head,
    )
    assert advanced["status"] == "refused"
    assert "registered revision" in advanced["reason"]

    relation_after_commit = get_repository_revision_info(checkout, pinned_head)
    assert relation_after_commit["relation"] == REVISION_AHEAD_OF_RECORDED

    allowed = run_pipeline(
        checkout=checkout,
        output_dir=tmp_path / "unpinned-run",
        interpreter_override=sys.executable,
        require_pin=False,
        revision=pinned_head,
    )
    assert allowed["status"] == "ok"
    assert allowed["checkout_status"]["relation"] == REVISION_AHEAD_OF_RECORDED

    at_pin = run_pipeline(
        checkout=checkout,
        output_dir=tmp_path / "at-pin-run",
        interpreter_override=sys.executable,
        require_pin=True,
        revision=_git("rev-parse", "HEAD", cwd=checkout),
    )
    assert at_pin["status"] == "ok"
    assert at_pin["checkout_status"]["relation"] == REVISION_AT_RECORDED


def test_run_pipeline_dry_run_does_not_execute(tmp_path):
    checkout = _make_checkout(tmp_path)
    output_dir = tmp_path / "dry-output"
    report = run_pipeline(
        checkout=checkout,
        output_dir=output_dir,
        interpreter_override=sys.executable,
        dry_run=True,
    )
    assert report["status"] == "dry-run"
    assert report["execution"] == {}
    assert report["command"][0] == sys.executable
    assert not output_dir.exists()
    assert "nothing executed" in report["reason"]


def test_summarize_outputs_reports_missing_artifacts(tmp_path):
    artifacts = summarize_outputs(tmp_path / "empty")
    assert set(artifacts) == {label for label, _ in config.SUMMARY_ARTIFACTS}
    for artifact in artifacts.values():
        assert artifact["exists"] is False
        assert "counts" not in artifact


def test_main_exit_codes(tmp_path, capsys):
    checkout = _make_checkout(tmp_path)
    ok = main(
        [
            "--checkout",
            str(checkout),
            "--output-dir",
            str(tmp_path / "cli-run"),
            "--python-executable",
            sys.executable,
            "--json",
        ]
    )
    assert ok == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ok"

    refused = main(["--checkout", str(tmp_path / "absent"), "--json"])
    assert refused == EXIT_REFUSED

    failing_checkout = _make_checkout(tmp_path, name="gnn-failing")
    (failing_checkout / "src" / "gnn" / "main.py").write_text(
        "import sys\nsys.exit(4)\n", encoding="utf-8"
    )
    failed = main(
        [
            "--checkout",
            str(failing_checkout),
            "--output-dir",
            str(tmp_path / "cli-failed"),
            "--python-executable",
            sys.executable,
        ]
    )
    assert failed == EXIT_PIPELINE_FAILED


def test_main_prints_human_report(tmp_path, capsys):
    checkout = _make_checkout(tmp_path)
    exit_code = main(
        [
            "--checkout",
            str(checkout),
            "--output-dir",
            str(tmp_path / "human-run"),
            "--python-executable",
            sys.executable,
        ]
    )
    assert exit_code == EXIT_OK
    output = capsys.readouterr().out
    assert "start-gnn: ok" in output
    assert "Models consumed:" in output
    assert "static_perception.md sha256=" in output
    assert "parse: " in output


def test_parse_step_selection_rejects_out_of_range():
    with pytest.raises(ValueError):
        utils.parse_step_selection("3,25")
    with pytest.raises(ValueError):
        utils.parse_step_selection("")
    assert utils.parse_step_selection("3, 3, 5") == (3, 5)
