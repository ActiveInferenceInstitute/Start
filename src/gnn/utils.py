"""Internal helpers for the ``start-gnn`` orchestrator.

These helpers keep the public surface in :mod:`src.gnn.main` small: JSON
reading, evidence fingerprints, count normalization, step parsing and terminal
formatting.  Nothing here invents values — a field is reported only when the
GNN pipeline actually wrote it.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from src.gnn import config
from src.repos.cloning import REVISION_UNKNOWN

MAX_SUMMARY_STEP = 24


def count_of(value: Any) -> int:
    """Return the item count of a collection."""
    return len(value)


def normalize_counts(payload: Mapping[str, Any], fields: Iterable[str]) -> dict[str, Any]:
    """Collect ``fields`` from ``payload`` as plain values or list lengths."""
    counts: dict[str, Any] = {}
    for field in fields:
        if field not in payload:
            continue
        value = payload[field]
        if isinstance(value, (list, tuple, set, frozenset)):
            counts[field] = count_of(value)
        elif isinstance(value, (str, int, float, bool)) or value is None:
            counts[field] = value
    return counts


def select_fields(payload: Mapping[str, Any], fields: Iterable[str]) -> dict[str, Any]:
    """Return the subset of ``fields`` present in ``payload``."""
    return {field: payload[field] for field in fields if field in payload}


def read_json_object(path: Path) -> dict[str, Any] | None:
    """Read a JSON object, returning ``None`` for missing or non-object files."""
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def sha256_file(path: Path) -> str | None:
    """SHA-256 of a file, or ``None`` when it cannot be read."""
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
    except OSError:
        return None
    return digest.hexdigest()


def file_modified_utc(path: Path) -> str | None:
    """ISO-8601 UTC modification time, or ``None`` when unavailable."""
    try:
        stamp = path.stat().st_mtime
    except OSError:
        return None
    return datetime.fromtimestamp(stamp, tz=timezone.utc).isoformat(timespec="seconds")


def parse_step_selection(value: str | Iterable[int] | None) -> tuple[int, ...]:
    """Parse a comma-separated step selection, preserving the given order."""
    if value is None:
        return config.DEFAULT_STEPS
    if isinstance(value, str):
        parts = [part.strip() for part in value.split(",") if part.strip()]
    else:
        parts = [str(part).strip() for part in value]
    if not parts:
        raise ValueError("Step selection is empty")
    steps: list[int] = []
    for part in parts:
        try:
            step = int(part)
        except ValueError:
            raise ValueError(f"Invalid pipeline step: {part!r}") from None
        if not 0 <= step <= MAX_SUMMARY_STEP:
            raise ValueError(f"Pipeline step out of range 0-{MAX_SUMMARY_STEP}: {step}")
        if step not in steps:
            steps.append(step)
    return tuple(steps)


def tail_lines(text: str | bytes, limit: int) -> list[str]:
    """Last ``limit`` non-empty lines of process output.

    A ``subprocess`` exception reports its captured output as ``bytes | str |
    None`` regardless of how the child was started, so both text forms are
    accepted here and bytes are decoded with replacement rather than guessed at.
    """
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="replace")
    lines = [line for line in text.splitlines() if line.strip()]
    return lines[-limit:] if limit > 0 else []


def format_report(report: Mapping[str, Any]) -> str:
    """Render the run report as an operator-readable block of text."""
    lines: list[str] = []
    status = report.get("status", "unknown")
    lines.append(f"start-gnn: {status}")
    lines.append(f"Checkout: {report.get('checkout', 'unknown')}")

    checkout = report.get("checkout_status") or {}
    relation = checkout.get("relation", REVISION_UNKNOWN)
    lines.append(
        "  revision: "
        f"HEAD {checkout.get('head_short') or 'unknown'} "
        f"vs registered {checkout.get('registered_revision_short') or 'none'} ({relation})"
    )
    if checkout.get("detail"):
        lines.append(f"  detail: {checkout['detail']}")

    if report.get("reason"):
        lines.append(f"Reason: {report['reason']}")

    target = report.get("target_dir")
    output = report.get("output_dir")
    lines.append(f"Steps: {','.join(str(step) for step in report.get('steps', ()))}")
    lines.append(f"Target: {target}")
    lines.append(f"Output: {output}")
    interpreter = report.get("interpreter") or {}
    if interpreter.get("command"):
        command_text = " ".join(interpreter["command"])
        lines.append(f"Interpreter ({interpreter.get('source')}): {command_text}")

    if report.get("command"):
        lines.append(f"Command: {' '.join(report['command'])}")
    execution = report.get("execution") or {}
    if execution:
        lines.append(
            f"Exit code: {execution.get('exit_code')} " f"in {execution.get('duration_seconds')}s"
        )

    pipeline = (report.get("artifacts") or {}).get("pipeline") or {}
    counts = pipeline.get("counts") or {}
    if counts:
        lines.append("Pipeline summary:")
        for key in sorted(counts):
            lines.append(f"  {key}: {counts[key]}")
    steps = report.get("pipeline_steps") or []
    for entry in steps:
        lines.append(
            f"  step {entry.get('step_number')} {entry.get('script_name')}: "
            f"{entry.get('status')} ({entry.get('duration_seconds')}s)"
        )

    models = report.get("model_selection") or []
    if models:
        lines.append("Models consumed:")
        for model in models:
            lines.append(
                f"  {model.get('relative_path')} sha256={model.get('sha256')} "
                f"id={model.get('model_id')}"
            )

    for label, artifact in sorted((report.get("artifacts") or {}).items()):
        if label == "pipeline":
            continue
        if not artifact.get("exists"):
            lines.append(f"{label}: summary not written")
            continue
        artifact_counts = artifact.get("counts") or {}
        rendered = ", ".join(f"{key}={value}" for key, value in sorted(artifact_counts.items()))
        lines.append(f"{label}: {rendered}")
        if not artifact_counts:
            lines.append(f"  (no known counters in {artifact.get('path')})")

    receipts = report.get("receipts") or {}
    for label, path in receipts.items():
        lines.append(f"Receipt ({label}): {path}")

    stdout_tail = execution.get("stdout_tail") or []
    if stdout_tail:
        lines.append("Last pipeline output:")
        lines.extend(f"  {line}" for line in stdout_tail)
    stderr_tail = execution.get("stderr_tail") or []
    if stderr_tail:
        lines.append("Last pipeline stderr:")
        lines.extend(f"  {line}" for line in stderr_tail)
    return "\n".join(lines)
