"""Run manifest persistence and artifact provenance records."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .artifacts import sha256_file, sha256_text, utc_now, write_json_atomic
from .contracts import PipelineResult, StageResult


@dataclass
class ArtifactRecord:
    """Auditable record for one published artifact."""

    path: str
    kind: str
    stage: str
    sha256: str
    size_bytes: int
    status: str = "published"
    item_id: str | None = None
    created_at: str = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_path(
        cls,
        path: str,
        *,
        kind: str,
        stage: str,
        item_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "ArtifactRecord":
        from pathlib import Path

        file_path = Path(path).expanduser()
        if (
            not file_path.is_file()
            or file_path.is_symlink()
            or any(parent.is_symlink() for parent in file_path.parents if parent.exists())
        ):
            raise ValueError(f"artifact path must be a regular file: {file_path}")
        file_path = file_path.resolve()
        return cls(
            path=str(file_path),
            kind=kind,
            stage=stage,
            sha256=sha256_file(file_path),
            size_bytes=file_path.stat().st_size,
            item_id=item_id,
            metadata=dict(metadata or {}),
        )

    @property
    def artifact_id(self) -> str:
        """Return a collision-safe identity for this exact published content."""

        item = self.item_id or "run"
        path_digest = sha256_text(self.path)[:16]
        return f"{self.stage}:{item}:{self.sha256}:{path_digest}"

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "kind": self.kind,
            "stage": self.stage,
            "sha256": self.sha256,
            "artifact_id": self.artifact_id,
            "size_bytes": self.size_bytes,
            "status": self.status,
            "item_id": self.item_id,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }


@dataclass
class RunManifest:
    """Complete, serializable state for one pipeline run."""

    run_id: str
    status: str = "running"
    schema_version: str = "1.0"
    started_at: str = field(default_factory=utc_now)
    finished_at: str | None = None
    config_digest: str | None = None
    stages: list[StageResult] = field(default_factory=list)
    artifacts: list[ArtifactRecord] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)
    quality: dict[str, Any] = field(default_factory=dict)
    usage: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    provider_metadata: dict[str, Any] = field(default_factory=dict)
    prompt_versions: dict[str, Any] = field(default_factory=dict)

    def update_from_result(self, result: PipelineResult, *, final: bool = False) -> None:
        """Copy the current pipeline result into the manifest."""

        self.stages = list(result.stages)
        stage_errors = [
            error
            for stage in result.stages
            if stage.required
            for error in [
                *stage.errors,
                *[f"{item_id}: {message}" for item_id, message in stage.failures.items()],
            ]
        ]
        self.errors = list(dict.fromkeys([*self.errors, *stage_errors, *result.errors]))
        stage_provenance = self.provenance.setdefault("stage_provenance", {})
        item_provenance = self.provenance.setdefault("item_provenance", {})
        for stage in result.stages:
            if stage.provenance:
                stage_provenance[stage.name] = dict(stage.provenance)
            for item_id, item in stage.items.items():
                if item.provenance:
                    item_provenance[f"{stage.name}:{item_id}"] = dict(item.provenance)
                quality = item.provenance.get("quality")
                if quality is not None:
                    self.quality[f"{stage.name}:{item_id}"] = quality
            if stage.provenance.get("quality") is not None:
                self.quality[stage.name] = stage.provenance["quality"]
        if final:
            self.status = "succeeded" if result.ok else "failed"
            self.finished_at = utc_now()
        elif self.status not in {"succeeded", "failed"}:
            self.status = "running"

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "config_digest": self.config_digest,
            "stages": {stage.name: stage.as_dict() for stage in self.stages},
            "artifacts": [artifact.as_dict() for artifact in self.artifacts],
            "provenance": dict(self.provenance),
            "provider_metadata": dict(self.provider_metadata),
            "prompt_versions": dict(self.prompt_versions),
            "quality": dict(self.quality),
            "usage": dict(self.usage),
            "errors": list(self.errors),
        }

    def write(self, path: str) -> str:
        """Atomically publish the manifest and return its path."""

        return str(write_json_atomic(path, self.as_dict()))
