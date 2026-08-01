"""Filesystem-backed run history, summaries, and conservative retention."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RunSummary:
    """Small operational summary for one persisted run."""

    run_id: str
    path: str
    status: str
    started_at: str | None
    finished_at: str | None
    artifact_count: int
    error_count: int
    usage: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "path": self.path,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "artifact_count": self.artifact_count,
            "error_count": self.error_count,
            "usage": dict(self.usage),
        }


def _read_manifest(path: Path) -> dict[str, Any] | None:
    try:
        import json

        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def list_runs(work_root: Path | str) -> list[RunSummary]:
    """List valid manifests below a non-symlink run root, newest first."""

    raw_root = Path(work_root).expanduser()
    if raw_root.exists() and raw_root.is_symlink():
        raise ValueError(f"run history root cannot be a symlink: {raw_root}")
    root = raw_root.resolve()
    if not root.is_dir():
        return []
    summaries: list[RunSummary] = []
    for manifest_path in sorted(root.glob("*/manifest.json")):
        if manifest_path.is_symlink():
            continue
        payload = _read_manifest(manifest_path)
        if payload is None or not isinstance(payload.get("run_id"), str):
            continue
        summaries.append(
            RunSummary(
                run_id=payload["run_id"],
                path=str(manifest_path.parent),
                status=str(payload.get("status", "unknown")),
                started_at=payload.get("started_at"),
                finished_at=payload.get("finished_at"),
                artifact_count=len(payload.get("artifacts", [])),
                error_count=len(payload.get("errors", [])),
                usage=dict(payload.get("usage", {})),
            )
        )
    return sorted(summaries, key=lambda item: str(item.started_at or ""), reverse=True)


def summarize_runs(summaries: list[RunSummary]) -> dict[str, Any]:
    """Aggregate status and cost totals without introducing a database."""

    from .usage import aggregate_usage

    usage = aggregate_usage({summary.run_id: summary.usage for summary in summaries})
    return {
        "run_count": len(summaries),
        "status_counts": {
            status: sum(summary.status == status for summary in summaries)
            for status in sorted({summary.status for summary in summaries})
        },
        "artifact_count": sum(summary.artifact_count for summary in summaries),
        "error_count": sum(summary.error_count for summary in summaries),
        "usage": usage,
    }


def retention_candidates(
    summaries: list[RunSummary],
    *,
    keep: int = 10,
    older_than_days: int | None = None,
) -> list[RunSummary]:
    """Return removable runs while retaining the newest ``keep`` entries."""

    if keep < 0:
        raise ValueError("keep cannot be negative")
    if older_than_days is not None and older_than_days < 0:
        raise ValueError("older_than_days cannot be negative")
    ordered = sorted(summaries, key=lambda item: str(item.started_at or ""), reverse=True)
    candidates = ordered[keep:]
    if older_than_days is None:
        return candidates
    cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
    result: list[RunSummary] = []
    for summary in candidates:
        try:
            started = datetime.fromisoformat(str(summary.started_at or "").replace("Z", "+00:00"))
        except (ValueError, TypeError, AttributeError):
            continue
        if started < cutoff:
            result.append(summary)
    return result


def prune_runs(summaries: list[RunSummary], *, apply: bool = False) -> list[str]:
    """Delete only manifest-bearing run directories when explicitly applied."""

    removed: list[str] = []
    for summary in summaries:
        raw_path = Path(summary.path).expanduser()
        if raw_path.is_symlink():
            continue
        if any(parent.exists() and parent.is_symlink() for parent in (raw_path, *raw_path.parents)):
            continue
        manifest = raw_path / "manifest.json"
        if manifest.is_symlink() or not manifest.is_file():
            continue
        path = raw_path.resolve()
        if apply:
            shutil.rmtree(path)
        removed.append(str(path))
    return removed
