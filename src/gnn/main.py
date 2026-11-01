"""``start-gnn``: run the cloned GNN pipeline and summarize what it produced.

The GNN project (Generalized Notation Notation) owns a 25-step pipeline that
parses Active Inference generative models, type-checks them, renders them into
simulation framework code and executes the results.  START does not re-implement
any of that: this module is a thin orchestrator that

1. locates the registered checkout (``src/_clones/gnn`` by default),
2. reports its HEAD against the pinned upstream revision recorded in
   :mod:`src.repos.cloning`,
3. runs a bounded step selection (default steps 3, 5, 11, 12) with the
   checkout's own interpreter,
4. reads the artifacts the pipeline wrote and reports their counts and hashes.

Nothing is written into the clone unless ``--output-dir`` says so; the default
output directory is the upstream default ``<checkout>/output``.

Example::

    uv run start-gnn --target input/gnn_files/basics --json
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.common.paths import ensure_dir
from src.gnn import config, utils
from src.repos.cloning import (
    REVISION_AT_RECORDED,
    REVISION_UNKNOWN,
    clone_repository,
    get_clone_destination,
    get_predefined_repositories,
    get_repository_revision_info,
    get_repository_status,
)

EXIT_OK = 0
EXIT_PIPELINE_FAILED = 1
EXIT_REFUSED = 2

_GIT_SAFE_ENV = {
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_TERMINAL_PROMPT": "0",
}


def resolve_gnn_checkout(path: str | Path | None = None, base_dir: Path | None = None) -> Path:
    """Return the GNN checkout path (explicit ``path`` wins over the registration).

    Parameters:
        path: Explicit checkout directory.
        base_dir: Clone root override used when no explicit path is given.

    Returns:
        Resolved checkout path (not guaranteed to exist yet).
    """
    if path:
        return Path(path).expanduser().resolve()
    return get_clone_destination(config.GNN_REPO_NAME, base_dir)


def registered_revision() -> str:
    """Pinned upstream revision recorded with the clone registration."""
    repo_info = get_predefined_repositories().get(config.GNN_REPO_NAME)
    return (getattr(repo_info, "revision", "") or "").strip()


def checkout_status(checkout: Path, revision: str | None = None) -> dict[str, Any]:
    """Report whether ``checkout`` looks like a usable GNN checkout.

    Parameters:
        checkout: Candidate checkout directory.
        revision: Revision to compare against; defaults to the registered pin.

    Returns:
        Dictionary with ``exists``, ``is_git_repo``, ``has_pipeline_script``,
        the registered revision and its relationship to HEAD.
    """
    registered = (revision or registered_revision() or "").strip()
    status: dict[str, Any] = {
        "path": str(checkout),
        "exists": checkout.is_dir(),
        "is_git_repo": False,
        "has_pipeline_script": (checkout / config.PIPELINE_SCRIPT).is_file(),
        "registered_revision": registered,
        "registered_revision_short": registered[:9],
        "head": None,
        "head_short": None,
        "relation": REVISION_UNKNOWN,
        "detail": "",
        "branch": None,
    }
    if not status["exists"]:
        status["detail"] = "checkout directory does not exist"
        return status

    repository = get_repository_status(checkout)
    status["is_git_repo"] = bool(repository.get("is_git_repo"))
    status["branch"] = repository.get("branch")
    if not status["is_git_repo"]:
        status["detail"] = "checkout directory is not a git working tree"
        return status

    revision_info = get_repository_revision_info(checkout, registered) if registered else {}
    status["head"] = revision_info.get("head")
    status["head_short"] = (revision_info.get("head") or "")[:9] or None
    status["relation"] = revision_info.get("relation", REVISION_UNKNOWN)
    status["revision_object_present"] = revision_info.get("revision_object_present")
    status["detail"] = revision_info.get("detail", "")
    if not status["has_pipeline_script"]:
        status["detail"] = (
            f"pipeline entry point missing: {config.PIPELINE_SCRIPT} is not in the checkout"
        )
    return status


def resolve_interpreter(checkout: Path, override: str | None = None) -> tuple[list[str], str]:
    """Choose the interpreter that runs the GNN pipeline.

    Preference order: an explicit override, the checkout's own virtual
    environment, ``uv run --frozen --no-sync python`` (no environment mutation),
    then the interpreter running START.

    Returns:
        ``(command prefix, source label)``.
    """
    if override:
        return [override], "explicit"
    candidates = (
        checkout / ".venv" / "bin" / "python",
        checkout / ".venv" / "Scripts" / "python.exe",
    )
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return [str(candidate)], "checkout-venv"
    if shutil.which("uv"):
        return ["uv", "run", "--frozen", "--no-sync", "python"], "uv-no-sync"
    return [sys.executable], "start-interpreter"


def build_pipeline_command(
    interpreter: Sequence[str],
    steps: Sequence[int],
    target_dir: Path,
    output_dir: Path,
) -> list[str]:
    """Build the GNN pipeline command line."""
    return [
        *interpreter,
        config.PIPELINE_SCRIPT,
        "--only-steps",
        ",".join(str(step) for step in steps),
        "--target-dir",
        str(target_dir),
        "--output-dir",
        str(output_dir),
    ]


def _resolve_inside(checkout: Path, value: str | Path | None, default_parts: Sequence[str]) -> Path:
    """Resolve ``value`` (absolute or checkout-relative) or the default sub-path."""
    if value is None:
        return (checkout / Path(*default_parts)).resolve()
    candidate = Path(value).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (checkout / candidate).resolve()


def summarize_outputs(output_dir: Path) -> dict[str, Any]:
    """Read the pipeline summary artifacts and fingerprint them.

    Missing artifacts are reported as missing; counts are reported only for
    fields the artifact actually contains.
    """
    artifacts: dict[str, Any] = {}
    for label, relative in config.SUMMARY_ARTIFACTS:
        path = output_dir / relative
        entry: dict[str, Any] = {
            "path": str(path),
            "relative_path": relative,
            "exists": path.is_file(),
        }
        payload = utils.read_json_object(path)
        if payload is not None:
            entry["sha256"] = utils.sha256_file(path)
            entry["modified_utc"] = utils.file_modified_utc(path)
            entry["counts"] = utils.normalize_counts(payload, config.SUMMARY_FIELDS.get(label, ()))
            entry["top_level_keys"] = sorted(payload)
        artifacts[label] = entry
    return artifacts


def _pipeline_payload(artifacts: Mapping[str, Any]) -> dict[str, Any] | None:
    pipeline = artifacts.get("pipeline") or {}
    if not pipeline.get("exists"):
        return None
    return utils.read_json_object(Path(pipeline.get("path", "")))


def pipeline_steps(artifacts: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Per-step records from the pipeline summary (empty when it is absent)."""
    payload = _pipeline_payload(artifacts)
    entries = payload.get("steps") if payload else None
    if not isinstance(entries, list):
        return []
    return [
        utils.select_fields(entry, config.STEP_ENTRY_FIELDS)
        for entry in entries
        if isinstance(entry, dict)
    ]


def model_selection(artifacts: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Models the pipeline recorded as consumed, with their source hashes."""
    payload = _pipeline_payload(artifacts)
    entries = payload.get("model_selection") if payload else None
    if not isinstance(entries, list):
        return []
    return [
        utils.select_fields(entry, config.MODEL_ENTRY_FIELDS)
        for entry in entries
        if isinstance(entry, dict)
    ]


def _receipt_paths(output_dir: Path) -> dict[str, str]:
    if not output_dir.is_dir():
        return {}
    return {
        "summary": str(output_dir / config.SUMMARY_RECEIPT_NAME),
        "stdout": str(output_dir / config.STDOUT_RECEIPT_NAME),
        "stderr": str(output_dir / config.STDERR_RECEIPT_NAME),
    }


def _write_receipts(
    output_dir: Path, report: dict[str, Any], stdout: str, stderr: str
) -> dict[str, str]:
    """Write the run report and raw pipeline output beside the pipeline artifacts."""
    receipts = report.get("receipts") or {}
    if not receipts:
        return {}
    Path(receipts["summary"]).write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    Path(receipts["stdout"]).write_text(stdout, encoding="utf-8")
    written = {"summary": receipts["summary"], "stdout": receipts["stdout"]}
    if stderr:
        Path(receipts["stderr"]).write_text(stderr, encoding="utf-8")
        written["stderr"] = receipts["stderr"]
    return written


def run_pipeline(
    checkout: str | Path | None = None,
    steps: str | Sequence[int] | None = None,
    target: str | Path | None = None,
    output_dir: str | Path | None = None,
    interpreter_override: str | None = None,
    timeout: int | None = None,
    dry_run: bool = False,
    require_pin: bool = False,
    clone_missing: bool = False,
    base_dir: Path | None = None,
    revision: str | None = None,
) -> dict[str, Any]:
    """Run the GNN pipeline steps in ``checkout`` and summarize the outputs.

    Parameters:
        checkout: Explicit checkout path; defaults to the registered clone.
        steps: Comma-separated or integer step selection (default 3, 5, 11, 12).
        target: GNN target directory, absolute or relative to the checkout.
        output_dir: Pipeline output directory, absolute or relative to the checkout.
        interpreter_override: Python executable to use instead of the detected one.
        timeout: Seconds allowed for the pipeline (default 3600).
        dry_run: Report the command without executing it.
        require_pin: Refuse to run when HEAD is not the registered revision.
        clone_missing: Clone the registered repository when the checkout is absent.
        base_dir: Clone root override used when ``checkout`` is not given.
        revision: Revision to verify against; defaults to the registered pin.

    Returns:
        Run report: checkout status, command, execution result, artifact digests
        and the models the pipeline recorded as consumed.
    """
    resolved_checkout = resolve_gnn_checkout(checkout, base_dir)
    report: dict[str, Any] = {
        "status": "refused",
        "checkout": str(resolved_checkout),
        "steps": [],
        "target_dir": None,
        "output_dir": None,
        "command": [],
        "interpreter": {},
        "execution": {},
        "artifacts": {},
        "pipeline_steps": [],
        "model_selection": [],
        "receipts": {},
        "reason": "",
        "clone": None,
    }

    if clone_missing and not resolved_checkout.is_dir():
        repo_info = get_predefined_repositories().get(config.GNN_REPO_NAME)
        if repo_info is None:
            report["reason"] = f"no registered repository named {config.GNN_REPO_NAME!r}"
            return report
        clone_result = clone_repository(repo_info, base_dir=base_dir)
        report["clone"] = {
            "success": clone_result.success,
            "destination": str(clone_result.destination) if clone_result.destination else None,
            "error_message": clone_result.error_message,
        }
        if not clone_result.success:
            report["reason"] = f"clone failed: {clone_result.error_message}"
            return report

    status = checkout_status(resolved_checkout, revision)
    report["checkout_status"] = status
    if not status["exists"] or not status["is_git_repo"] or not status["has_pipeline_script"]:
        report["reason"] = status.get("detail") or "checkout is not usable"
        return report

    try:
        selected_steps = utils.parse_step_selection(steps)
    except ValueError as exc:
        report["reason"] = str(exc)
        return report

    target_path = _resolve_inside(resolved_checkout, target, (config.DEFAULT_TARGET_SUBDIR,))
    output_path = _resolve_inside(resolved_checkout, output_dir, (config.DEFAULT_OUTPUT_SUBDIR,))
    interpreter, interpreter_source = resolve_interpreter(resolved_checkout, interpreter_override)
    command = build_pipeline_command(interpreter, selected_steps, target_path, output_path)

    report.update(
        {
            "steps": list(selected_steps),
            "step_descriptions": {
                str(step): config.STEP_DESCRIPTIONS.get(step, "") for step in selected_steps
            },
            "target_dir": str(target_path),
            "output_dir": str(output_path),
            "interpreter": {"command": interpreter, "source": interpreter_source},
            "command": command,
            "dry_run": dry_run,
        }
    )

    if require_pin and status["relation"] != REVISION_AT_RECORDED:
        report["reason"] = (
            f"checkout HEAD {status['head_short']} is {status['relation']} "
            f"the registered revision {status['registered_revision_short']}"
        )
        return report
    if not target_path.is_dir():
        report["reason"] = f"target directory does not exist: {target_path}"
        return report

    if dry_run:
        report["status"] = "dry-run"
        report["reason"] = "command prepared; nothing executed"
        report["artifacts"] = summarize_outputs(output_path)
        report["pipeline_steps"] = pipeline_steps(report["artifacts"])
        report["model_selection"] = model_selection(report["artifacts"])
        return report

    ensure_dir(output_path)
    started = time.time()
    try:
        completed = subprocess.run(
            command,
            cwd=resolved_checkout,
            capture_output=True,
            text=True,
            timeout=timeout or config.DEFAULT_TIMEOUT_SECONDS,
            env={**os.environ, **_GIT_SAFE_ENV},
        )
    except subprocess.TimeoutExpired as exc:
        report["status"] = "failed"
        report["execution"] = {
            "exit_code": None,
            "duration_seconds": round(time.time() - started, 3),
            "stdout_tail": utils.tail_lines(exc.stdout or "", config.STDOUT_TAIL_LINES),
            "stderr_tail": utils.tail_lines(exc.stderr or "", config.STDERR_TAIL_LINES),
        }
        report["reason"] = (
            f"pipeline exceeded timeout of {timeout or config.DEFAULT_TIMEOUT_SECONDS}s"
        )
        report["artifacts"] = summarize_outputs(output_path)
        return report
    except OSError as exc:
        report["status"] = "failed"
        report["reason"] = f"could not start the pipeline: {exc}"
        return report

    report["execution"] = {
        "exit_code": completed.returncode,
        "duration_seconds": round(time.time() - started, 3),
        "stdout_lines": len(completed.stdout.splitlines()),
        "stdout_tail": utils.tail_lines(completed.stdout, config.STDOUT_TAIL_LINES),
        "stderr_tail": utils.tail_lines(completed.stderr, config.STDERR_TAIL_LINES),
    }
    report["artifacts"] = summarize_outputs(output_path)
    report["pipeline_steps"] = pipeline_steps(report["artifacts"])
    report["model_selection"] = model_selection(report["artifacts"])

    pipeline_counts = (report["artifacts"].get("pipeline") or {}).get("counts") or {}
    overall = pipeline_counts.get("overall_status")
    report["pipeline_status"] = overall
    if completed.returncode != 0:
        report["status"] = "failed"
        report["reason"] = f"pipeline exited with code {completed.returncode}"
    elif overall and overall != "SUCCESS":
        report["status"] = "ok-with-warnings"
        report["reason"] = f"pipeline reported {overall}"
    else:
        report["status"] = "ok"

    report["receipts"] = _receipt_paths(output_path)
    report["receipts"] = _write_receipts(output_path, report, completed.stdout, completed.stderr)
    return report


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="start-gnn",
        description=(
            "Run the cloned GNN pipeline (default steps 3,5,11,12) and summarize its outputs"
        ),
        epilog=(
            "Exit codes: 0 pipeline ran, 1 pipeline failed, 2 run refused "
            "(missing checkout, bad selection, or --require-pin mismatch)."
        ),
    )
    parser.add_argument("--checkout", help="GNN checkout directory (default: src/_clones/gnn)")
    parser.add_argument(
        "--steps",
        default=",".join(str(step) for step in config.DEFAULT_STEPS),
        help="Comma-separated pipeline steps to run",
    )
    parser.add_argument(
        "--target",
        help=(
            "GNN target directory, absolute or relative to the checkout "
            f"(default: {config.DEFAULT_TARGET_SUBDIR})"
        ),
    )
    parser.add_argument(
        "--output-dir",
        dest="output_dir",
        help=(
            "Pipeline output directory, absolute or relative to the checkout "
            f"(default: {config.DEFAULT_OUTPUT_SUBDIR})"
        ),
    )
    parser.add_argument("--python-executable", help="Interpreter used to run the pipeline")
    parser.add_argument(
        "--timeout",
        type=int,
        default=config.DEFAULT_TIMEOUT_SECONDS,
        help="Seconds allowed for the pipeline",
    )
    parser.add_argument(
        "--require-pin",
        action="store_true",
        help="Refuse to run unless HEAD is the registered upstream revision",
    )
    parser.add_argument(
        "--revision",
        help="Verify against this revision instead of the registered pin",
    )
    parser.add_argument(
        "--clone",
        action="store_true",
        help="Clone the registered repository when the checkout is missing",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print the command and exit")
    parser.add_argument("--json", action="store_true", help="Print the full report as JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    report = run_pipeline(
        checkout=args.checkout,
        steps=args.steps,
        target=args.target,
        output_dir=args.output_dir,
        interpreter_override=args.python_executable,
        timeout=args.timeout,
        dry_run=args.dry_run,
        require_pin=args.require_pin,
        clone_missing=args.clone,
        revision=args.revision,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(utils.format_report(report))
    status = report.get("status")
    if status == "failed":
        return EXIT_PIPELINE_FAILED
    if status == "refused":
        return EXIT_REFUSED
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
