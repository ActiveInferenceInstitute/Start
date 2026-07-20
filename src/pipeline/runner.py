"""Dependency-aware, resumable filesystem pipeline runner."""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any

from .artifacts import (
    create_run_directory,
    read_json,
    sha256_file,
    sha256_text,
    utc_now,
    write_stage_checkpoint,
)
from .contracts import (
    PipelineResult,
    RunConfig,
    StageItemResult,
    StageResult,
    StageSpec,
    StageStatus,
)
from .manifest import ArtifactRecord, RunManifest
from .usage import merge_usage

StageHandler = Callable[["RunContext"], StageResult]


class RunContext:
    """Context supplied to each stage handler."""

    def __init__(
        self,
        config: RunConfig,
        run_dir: Path,
        manifest: RunManifest,
        cancellation_event: threading.Event | None = None,
    ):
        self.config = config
        self.run_dir = run_dir
        self.manifest = manifest
        self.cancellation_event = cancellation_event or threading.Event()

    @property
    def cancelled(self) -> bool:
        return self.cancellation_event.is_set()


class PipelineRunner:
    """Run independent stages in dependency order with checkpoints."""

    def __init__(
        self,
        specs: Iterable[StageSpec],
        *,
        work_root: Path | str,
        run_id: str,
        offline: bool = False,
        max_concurrent_requests: int = 1,
        metadata: Mapping[str, Any] | None = None,
        budget_limit_usd: float | None = None,
        dry_run: bool = False,
        estimate_cost: bool = False,
        allowed_output_roots: Iterable[Path | str] | None = None,
        cancellation_event: threading.Event | None = None,
    ) -> None:
        self.specs = list(specs)
        self._validate_specs()
        normalized_output_roots = tuple(
            str(Path(root).expanduser().resolve()) for root in (allowed_output_roots or ())
        )
        self.config = RunConfig(
            run_id=run_id,
            work_dir=str(work_root),
            offline=offline,
            max_concurrent_requests=max_concurrent_requests,
            budget_limit_usd=budget_limit_usd,
            dry_run=dry_run,
            estimate_cost=estimate_cost,
            allowed_output_roots=normalized_output_roots,
            metadata=dict(metadata or {}),
        )
        self.run_dir = create_run_directory(work_root, run_id)
        self.cancellation_event = cancellation_event or threading.Event()
        self.manifest_path = self.run_dir / "manifest.json"
        self._usage_base: dict[str, Any] | None = None
        config_payload = {
            "run_id": run_id,
            "work_dir": str(Path(work_root).expanduser().resolve()),
            "offline": offline,
            "max_concurrent_requests": max_concurrent_requests,
            "budget_limit_usd": budget_limit_usd,
            "dry_run": dry_run,
            "estimate_cost": estimate_cost,
            "allowed_output_roots": normalized_output_roots,
            "metadata": dict(metadata or {}),
        }
        self.manifest = RunManifest(
            run_id=run_id,
            config_digest=sha256_text(
                json.dumps(
                    config_payload,
                    sort_keys=True,
                    default=str,
                    separators=(",", ":"),
                )
            ),
            provenance=dict(metadata or {}),
            provider_metadata=dict((metadata or {}).get("provider_metadata", {})),
            prompt_versions=dict((metadata or {}).get("prompt_versions", {})),
        )

    def _validate_specs(self) -> None:
        names = [spec.name for spec in self.specs]
        if len(set(names)) != len(names):
            raise ValueError("pipeline stage names must be unique")
        known = set(names)
        for spec in self.specs:
            missing = set(spec.depends_on) - known
            if missing:
                raise ValueError(f"stage {spec.name} has unknown dependencies: {sorted(missing)}")
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(name: str) -> None:
            if name in visiting:
                raise ValueError("pipeline stage dependencies contain a cycle")
            if name in visited:
                return
            visiting.add(name)
            spec = next(item for item in self.specs if item.name == name)
            for dependency in spec.depends_on:
                visit(dependency)
            visiting.remove(name)
            visited.add(name)

        for name in names:
            visit(name)

    def _ordered_specs(self) -> list[StageSpec]:
        ordered: list[StageSpec] = []
        remaining = {spec.name: spec for spec in self.specs}
        while remaining:
            ready = [
                spec
                for spec in self.specs
                if spec.name in remaining
                and all(dependency not in remaining for dependency in spec.depends_on)
            ]
            if not ready:
                raise ValueError("unable to order pipeline stages")
            for spec in ready:
                ordered.append(spec)
                remaining.pop(spec.name)
        return ordered

    def _persist(self, result: PipelineResult) -> None:
        self.manifest.update_from_result(result, final=False)
        if self._usage_base is None:
            self._usage_base = dict(self.manifest.usage)
        self.manifest.usage = merge_usage(
            self._usage_base,
            *(stage.usage for stage in result.stages),
        )
        budget_exceeded = self._enforce_budget()
        if budget_exceeded:
            self.manifest.write(str(self.manifest_path))
            return
        for stage in result.stages:
            # A failed or blocked stage may have left temporary files behind;
            # those are never published as authoritative artifacts.
            if not stage.ok:
                continue
            item_for_path = {
                output_path: item
                for item in stage.items.values()
                for output_path in item.output_paths
            }
            output_paths = list(
                dict.fromkeys(
                    [
                        *stage.output_paths,
                        *(path for item in stage.items.values() for path in item.output_paths),
                    ]
                )
            )
            for output_path in output_paths:
                path = Path(output_path)
                if (
                    not path.is_file()
                    or path.is_symlink()
                    or any(parent.is_symlink() for parent in path.parents if parent.exists())
                ):
                    self.manifest.errors.append(
                        f"stage {stage.name} referenced an invalid artifact: {output_path}"
                    )
                    continue
                canonical_path = str(path.expanduser().resolve())
                if not self._within_allowed_output_roots(Path(canonical_path)):
                    self.manifest.errors.append(
                        "stage "
                        f"{stage.name} artifact is outside allowed output roots: {output_path}"
                    )
                    continue
                digest = sha256_file(path)
                item = item_for_path.get(output_path)
                expected_hash = item.artifact_hashes.get(output_path) if item is not None else None
                if item is not None and expected_hash is None:
                    expected_hash = item.artifact_hashes.get(canonical_path)
                if item is not None and expected_hash not in {
                    None,
                    digest,
                }:
                    self.manifest.errors.append(
                        f"artifact hash does not match stage result: {output_path}"
                    )
                    continue
                existing = next(
                    (
                        artifact
                        for artifact in self.manifest.artifacts
                        if artifact.path in {output_path, canonical_path}
                    ),
                    None,
                )
                if existing is not None:
                    if existing.sha256 != digest:
                        self.manifest.errors.append(
                            f"artifact changed after publication: {output_path}"
                        )
                    continue
                self.manifest.artifacts.append(
                    ArtifactRecord.from_path(
                        canonical_path,
                        kind=path.suffix.lstrip(".") or "file",
                        stage=stage.name,
                        item_id=item.item_id if item else None,
                        metadata={
                            **stage.provenance,
                            **(item.provenance if item else {}),
                        },
                    )
                )
        self.manifest.write(str(self.manifest_path))

    def _within_allowed_output_roots(self, path: Path) -> bool:
        """Return whether an artifact is inside a configured publication root."""

        roots = [Path(root) for root in self.config.allowed_output_roots]
        if not roots:
            return True
        resolved = path.expanduser().resolve()
        return any(resolved != root and root in resolved.parents for root in roots)

    def _enforce_budget(self) -> bool:
        """Stop a run once observed provider spend exceeds its hard limit."""

        limit = self.config.budget_limit_usd
        if limit is None:
            return False
        actual = float(self.manifest.usage.get("actual_cost_usd", 0.0) or 0.0)
        if actual > limit:
            error = f"observed provider cost ${actual:.6f} exceeds budget ${limit:.6f}"
            if error not in self.manifest.errors:
                self.manifest.errors.append(error)
            self.cancellation_event.set()
            return True
        return False

    def _restore_artifacts(self, existing: dict[str, Any]) -> set[str]:
        """Restore and verify artifact records before a resumed run can skip work."""

        self.manifest.artifacts = []
        invalid_stages: set[str] = set()
        for artifact in existing.get("artifacts", []):
            record = ArtifactRecord(
                path=artifact["path"],
                kind=artifact.get("kind", "file"),
                stage=artifact.get("stage", "unknown"),
                sha256=artifact["sha256"],
                size_bytes=int(artifact.get("size_bytes", 0)),
                status=artifact.get("status", "published"),
                item_id=artifact.get("item_id"),
                created_at=artifact.get("created_at", utc_now()),
                metadata=dict(artifact.get("metadata", {})),
            )
            self.manifest.artifacts.append(record)
            path = Path(record.path)
            if (
                not path.is_file()
                or path.is_symlink()
                or any(parent.is_symlink() for parent in path.parents if parent.exists())
                or path.stat().st_size != record.size_bytes
                or sha256_file(path) != record.sha256
                or not self._within_allowed_output_roots(path)
            ):
                self.manifest.errors.append(
                    f"published artifact is missing or changed: {record.path}"
                )
                invalid_stages.add(record.stage)
        return invalid_stages

    def _load_existing(self) -> dict[str, Any] | None:
        if not self.manifest_path.exists():
            return None
        return read_json(self.manifest_path)

    def run(
        self,
        handlers: Mapping[str, StageHandler],
        *,
        resume: bool = True,
        continue_independent: bool = True,
    ) -> PipelineResult:
        """Execute handlers and persist a manifest after every stage."""

        started = time.monotonic()
        existing = self._load_existing() if resume else None
        results: dict[str, StageResult] = {}
        if existing:
            if (
                existing.get("config_digest")
                and existing.get("config_digest") != self.manifest.config_digest
            ):
                raise ValueError("run manifest configuration digest does not match this run")
            self.manifest.status = existing.get("status", "running")
            self.manifest.provenance = dict(existing.get("provenance", {}))
            self.manifest.provider_metadata = dict(existing.get("provider_metadata", {}))
            self.manifest.prompt_versions = dict(existing.get("prompt_versions", {}))
            self.manifest.quality = dict(existing.get("quality", {}))
            self.manifest.usage = dict(existing.get("usage", {}))
            # Errors from an earlier attempt are historical state, not a
            # reason to fail a repaired resume.  Current artifact validation
            # and the stages that execute below repopulate active errors.
            self.manifest.errors = []
            invalid_stages = self._restore_artifacts(existing)

            def restore_stage(name: str, payload: dict[str, Any]) -> StageResult:
                items: dict[str, StageItemResult] = {}
                for item_id, item in dict(payload.get("items", {})).items():
                    items[item_id] = StageItemResult(
                        item_id=item_id,
                        status=item.get("status", StageStatus.PENDING),
                        message=str(item.get("message", "")),
                        output_paths=list(item.get("output_paths", [])),
                        input_hashes=dict(item.get("input_hashes", {})),
                        artifact_hashes=dict(item.get("artifact_hashes", {})),
                        provenance=dict(item.get("provenance", {})),
                        errors=list(item.get("errors", [])),
                        usage=dict(item.get("usage", {})),
                    )
                return StageResult(
                    name=name,
                    status=payload.get("status", StageStatus.PENDING),
                    required=payload.get("required", True),
                    dependencies=list(payload.get("dependencies", [])),
                    errors=list(payload.get("errors", [])),
                    output_paths=list(payload.get("output_paths", [])),
                    provenance=dict(payload.get("provenance", {})),
                    usage=dict(payload.get("usage", {})),
                    items=items,
                )

            rebuild = set(invalid_stages)
            # A manifest with overall success may still contain an optional
            # failed stage; preserve that visible result instead of rerunning
            # it on every resume.  Failed required runs, however, rebuild
            # failed stages and their dependents.
            if existing.get("status") != "succeeded":
                for name, payload in existing.get("stages", {}).items():
                    if payload.get("status") not in {
                        StageStatus.SUCCEEDED.value,
                        StageStatus.SKIPPED.value,
                    }:
                        rebuild.add(name)
            # If an upstream result needs repair, all dependents must be
            # rerun as well; otherwise resume could publish outputs derived
            # from a tampered or failed prerequisite.
            changed = True
            while changed:
                changed = False
                for spec in self.specs:
                    if spec.name not in rebuild and any(
                        dependency in rebuild for dependency in spec.depends_on
                    ):
                        rebuild.add(spec.name)
                        changed = True

            for name, payload in existing.get("stages", {}).items():
                if name not in rebuild:
                    results[name] = restore_stage(name, payload)

            if existing.get("status") == "succeeded" and not self.manifest.errors and not rebuild:
                result = PipelineResult(
                    stages=list(results.values()),
                    duration_seconds=0.0,
                    run_id=self.config.run_id,
                    manifest_path=str(self.manifest_path),
                    usage=dict(self.manifest.usage),
                )
                return result

        for spec in self._ordered_specs():
            if spec.name in results:
                continue
            context = RunContext(self.config, self.run_dir, self.manifest, self.cancellation_event)
            if context.cancelled:
                stage = StageResult(
                    name=spec.name,
                    status=StageStatus.BLOCKED if spec.required else StageStatus.SKIPPED,
                    required=spec.required,
                    dependencies=list(spec.depends_on),
                    errors=["run cancelled before stage started"],
                )
                results[spec.name] = stage
                write_stage_checkpoint(self.run_dir, spec.name, stage.as_dict())
                continue
            dependencies = [results.get(name) for name in spec.depends_on]
            blocked: list[str] = []
            for dependency_name, dependency in zip(spec.depends_on, dependencies, strict=True):
                if dependency is None or not dependency.ok:
                    blocked.append(dependency_name)
            if not spec.enabled:
                stage = StageResult(
                    name=spec.name,
                    status=StageStatus.SKIPPED,
                    required=False,
                    dependencies=list(spec.depends_on),
                )
            elif blocked:
                stage = StageResult(
                    name=spec.name,
                    status=StageStatus.BLOCKED,
                    required=spec.required,
                    dependencies=list(spec.depends_on),
                    errors=[f"blocked by failed prerequisite: {', '.join(blocked)}"],
                )
            elif spec.name not in handlers:
                stage = StageResult(
                    name=spec.name,
                    status=StageStatus.FAILED,
                    required=spec.required,
                    dependencies=list(spec.depends_on),
                    errors=[f"no handler registered for stage: {spec.name}"],
                )
            else:
                try:
                    stage = handlers[spec.name](context)
                    if not isinstance(stage, StageResult):
                        raise TypeError("stage handler must return StageResult")
                    if stage.name != spec.name:
                        raise ValueError(
                            f"stage handler returned {stage.name!r}; expected {spec.name!r}"
                        )
                    stage.dependencies = list(spec.depends_on)
                    stage.required = spec.required
                    if not stage.status:
                        stage.status = StageStatus.SUCCEEDED if stage.ok else StageStatus.FAILED
                except Exception as exc:  # stage boundaries must be recorded
                    stage = StageResult(
                        name=spec.name,
                        status=StageStatus.FAILED,
                        required=spec.required,
                        dependencies=list(spec.depends_on),
                        errors=[f"{type(exc).__name__}: {exc}"],
                    )
            results[spec.name] = stage
            result = PipelineResult(
                stages=list(results.values()),
                duration_seconds=time.monotonic() - started,
                run_id=self.config.run_id,
                manifest_path=str(self.manifest_path),
                usage=dict(self.manifest.usage),
            )
            write_stage_checkpoint(self.run_dir, spec.name, stage.as_dict())
            self._persist(result)
            if not continue_independent and not stage.ok:
                break

        result = PipelineResult(
            stages=list(results.values()),
            duration_seconds=time.monotonic() - started,
            run_id=self.config.run_id,
            manifest_path=str(self.manifest_path),
            errors=list(self.manifest.errors),
            usage=dict(self.manifest.usage),
        )
        self.manifest.update_from_result(result, final=True)
        self.manifest.write(str(self.manifest_path))
        return result
