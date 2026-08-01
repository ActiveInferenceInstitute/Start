"""Structured contracts shared by command-line, GUI, and pipeline callers."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StageStatus(str, Enum):
    """Stable lifecycle values for a pipeline stage or item."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    SKIPPED = "skipped"
    BLOCKED = "blocked"
    FAILED = "failed"


def status_value(status: StageStatus | str) -> str:
    """Return a JSON-friendly status value across Python versions."""

    return status.value if isinstance(status, StageStatus) else str(status)


@dataclass
class StageItemResult:
    """Outcome and artifact details for one independently processed item."""

    item_id: str
    status: StageStatus | str = StageStatus.SUCCEEDED
    message: str = ""
    output_paths: list[str] = field(default_factory=list)
    input_hashes: dict[str, str] = field(default_factory=dict)
    artifact_hashes: dict[str, str] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    usage: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return status_value(self.status) in {
            StageStatus.SUCCEEDED.value,
            StageStatus.SKIPPED.value,
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "status": status_value(self.status),
            "message": self.message,
            "output_paths": list(self.output_paths),
            "input_hashes": dict(self.input_hashes),
            "artifact_hashes": dict(self.artifact_hashes),
            "provenance": dict(self.provenance),
            "usage": dict(self.usage),
            "errors": list(self.errors),
            "ok": self.ok,
        }


@dataclass(frozen=True)
class StageSpec:
    """Declarative stage definition used by :class:`PipelineRunner`."""

    name: str
    depends_on: tuple[str, ...] = ()
    required: bool = True
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("stage name cannot be empty")
        if self.name in self.depends_on:
            raise ValueError(f"stage cannot depend on itself: {self.name}")


@dataclass(frozen=True)
class RunConfig:
    """Execution policy shared by deterministic and provider-backed runs."""

    run_id: str
    work_dir: str
    offline: bool = False
    max_concurrent_requests: int = 1
    budget_limit_usd: float | None = None
    dry_run: bool = False
    estimate_cost: bool = False
    resume: bool = True
    allowed_output_roots: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.run_id or not self.run_id.strip():
            raise ValueError("run_id cannot be empty")
        if not self.work_dir or not self.work_dir.strip():
            raise ValueError("work_dir cannot be empty")
        if self.max_concurrent_requests < 1:
            raise ValueError("max_concurrent_requests must be at least one")
        if self.budget_limit_usd is not None and (
            not math.isfinite(self.budget_limit_usd) or self.budget_limit_usd < 0
        ):
            raise ValueError("budget_limit_usd must be a finite non-negative number")
        if any(not root or not str(root).strip() for root in self.allowed_output_roots):
            raise ValueError("allowed_output_roots cannot contain empty paths")


@dataclass
class StageResult:
    """Outcome of one pipeline stage."""

    name: str
    successes: list[str] = field(default_factory=list)
    skips: list[str] = field(default_factory=list)
    failures: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    required: bool = True
    status: StageStatus | str = StageStatus.SUCCEEDED
    dependencies: list[str] = field(default_factory=list)
    items: dict[str, StageItemResult] = field(default_factory=dict)
    output_paths: list[str] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)
    usage: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.failures or self.errors:
            if status_value(self.status) == StageStatus.SUCCEEDED.value:
                self.status = StageStatus.FAILED
        if self.items:
            self.output_paths = list(
                dict.fromkeys(
                    [
                        *self.output_paths,
                        *(path for item in self.items.values() for path in item.output_paths),
                    ]
                )
            )
            self.successes = [
                item_id
                for item_id, item in self.items.items()
                if status_value(item.status) == StageStatus.SUCCEEDED.value
            ]
            self.skips = [
                item_id
                for item_id, item in self.items.items()
                if status_value(item.status) == StageStatus.SKIPPED.value
            ]
            self.failures = {
                item_id: "; ".join(item.errors) or item.message or "item failed"
                for item_id, item in self.items.items()
                if not item.ok
            }
            # Item-derived failures are computed only inside this branch, so the
            # status must be re-assessed here: a handler that passes a FAILED
            # item with default status must not silently report success.
            if (self.failures or self.errors) and status_value(self.status) in {
                StageStatus.SUCCEEDED.value,
                StageStatus.PENDING.value,
            }:
                self.status = StageStatus.FAILED
            if not self.usage:
                from .usage import merge_usage

                self.usage = merge_usage(*(item.usage for item in self.items.values()))
            return
        for item_id in self.successes:
            self.items[item_id] = StageItemResult(item_id, StageStatus.SUCCEEDED)
        for item_id in self.skips:
            self.items[item_id] = StageItemResult(item_id, StageStatus.SKIPPED)
        for item_id, message in self.failures.items():
            self.items[item_id] = StageItemResult(
                item_id, StageStatus.FAILED, message=message, errors=[message]
            )

    @property
    def ok(self) -> bool:
        return status_value(self.status) in {
            StageStatus.SUCCEEDED.value,
            StageStatus.SKIPPED.value,
        }

    @property
    def attempted(self) -> int:
        return len(self.items) or len(self.successes) + len(self.skips) + len(self.failures)

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": status_value(self.status),
            "dependencies": list(self.dependencies),
            "success": len(self.successes),
            "skipped": len(self.skips),
            "failed": len(self.failures),
            "errors": [
                *self.errors,
                *[f"{key}: {value}" for key, value in self.failures.items()],
            ],
            "ok": self.ok,
            "required": self.required,
            "output_paths": list(self.output_paths),
            "provenance": dict(self.provenance),
            "usage": dict(self.usage),
            "items": {key: value.as_dict() for key, value in self.items.items()},
        }


@dataclass
class PipelineResult:
    """Outcome of all requested stages."""

    stages: list[StageResult] = field(default_factory=list)
    duration_seconds: float = 0.0
    run_id: str | None = None
    manifest_path: str | None = None
    errors: list[str] = field(default_factory=list)
    usage: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return (
            bool(self.stages)
            and not self.errors
            and all(stage.ok for stage in self.stages if stage.required)
        )

    @property
    def failures(self) -> list[str]:
        return [stage.name for stage in self.stages if stage.required and not stage.ok]

    def __bool__(self) -> bool:
        return self.ok

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "run_id": self.run_id,
            "manifest_path": self.manifest_path,
            "duration_seconds": self.duration_seconds,
            "errors": list(self.errors),
            "usage": dict(self.usage),
            "stages": {stage.name: stage.as_dict() for stage in self.stages},
        }
