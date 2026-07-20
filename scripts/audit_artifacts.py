"""Inventory generated artifacts and surface provenance/duplication debt.

The audit is deliberately non-destructive. It reports what can be retained,
what is duplicated by content hash, and which artifacts need provenance before
public release; curation remains an explicit human-reviewed operation.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from src.common.io import ensure_parent_dir, write_text
from src.pipeline.artifacts import sha256_file

DEFAULT_ROOTS = (
    "data/audience_research",
    "data/domain_research",
    "data/entity_research",
    "data/translated_curriculums",
    "data/visualizations",
    "data/written_curriculums",
)
_NON_ARTIFACT_FILENAMES = {"README.md", "AGENTS.md"}


def _is_ignored_path(path: Path) -> bool:
    """Exclude repository guidance and operational run state from content audits."""

    return path.name in _NON_ARTIFACT_FILENAMES or ".runs" in path.parts


def _has_provenance(path: Path) -> bool:
    if path.name.startswith("Synthetic_FEP-ActInf"):
        return True
    if path.suffix.lower() == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return False
        metadata = payload.get("metadata", {}) if isinstance(payload, dict) else {}
        top_level = payload if isinstance(payload, dict) else {}
        return bool(
            (
                isinstance(metadata, dict)
                and (metadata.get("evidence_status") or metadata.get("provider"))
            )
            or top_level.get("evidence_status")
            or top_level.get("provenance")
        )
    try:
        prefix = path.read_text(encoding="utf-8")[:4000]
    except (OSError, UnicodeDecodeError):
        return False
    return any(
        marker in prefix
        for marker in ("evidence_status:", "provider:", "provenance:", "synthetic_foundation")
    )


def _has_symlink_boundary(path: Path, root: Path) -> bool:
    """Return whether an artifact reaches its root through a symlink."""

    return any(parent != root and parent.is_symlink() for parent in path.parents)


def audit_artifacts(root: Path) -> dict[str, Any]:
    """Return a deterministic, JSON-serializable artifact inventory."""

    files: list[Path] = []
    missing: list[str] = []
    errors: list[str] = []
    visual_manifest_paths: set[str] = set()
    visual_manifest = root / "data" / "visualizations" / "visualization_manifest.json"
    if visual_manifest.is_file() and not visual_manifest.is_symlink():
        try:
            payload = json.loads(visual_manifest.read_text(encoding="utf-8"))
            visual_manifest_paths = {
                (Path("data/visualizations") / str(record["path"])).as_posix()
                for record in payload.get("artifacts", [])
                if isinstance(record, dict) and isinstance(record.get("path"), str)
            }
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError):
            errors.append("data/visualizations/visualization_manifest.json: invalid manifest")
    for relative in DEFAULT_ROOTS:
        directory = root / relative
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*")):
            relative_path = path.relative_to(root).as_posix()
            if _is_ignored_path(path):
                continue
            if path.is_symlink() or _has_symlink_boundary(path, root):
                errors.append(f"{relative_path}: symlink boundary")
                continue
            if not path.is_file():
                continue
            files.append(path)
            try:
                has_provenance = _has_provenance(path) or relative_path in visual_manifest_paths
            except OSError as exc:
                errors.append(f"{relative_path}: {exc}")
                has_provenance = False
            if not has_provenance:
                missing.append(relative_path)

    by_hash: dict[str, list[str]] = defaultdict(list)
    by_kind: dict[str, int] = defaultdict(int)
    records: list[dict[str, Any]] = []
    for path in files:
        try:
            digest = sha256_file(path)
        except OSError as exc:
            errors.append(f"{path.relative_to(root).as_posix()}: {exc}")
            continue
        relative = path.relative_to(root).as_posix()
        kind = path.suffix.lower().lstrip(".") or "file"
        by_hash[digest].append(relative)
        by_kind[kind] += 1
        records.append(
            {
                "path": relative,
                "kind": kind,
                "sha256": digest,
                "size_bytes": path.stat().st_size,
                "has_provenance": relative not in missing,
            }
        )
    duplicate_groups = [sorted(paths) for paths in by_hash.values() if len(paths) > 1]
    return {
        "schema_version": "1.0",
        "roots": list(DEFAULT_ROOTS),
        "summary": {
            "file_count": len(files),
            "by_extension": dict(sorted(by_kind.items())),
            "duplicate_group_count": len(duplicate_groups),
            "unprovenanced_count": len(missing),
            "error_count": len(errors),
        },
        "duplicate_groups": sorted(duplicate_groups, key=lambda group: group[0]),
        "unprovenanced": sorted(missing),
        "errors": sorted(errors),
        "files": records,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--write", type=Path, help="Write the inventory manifest to this path")
    parser.add_argument("--json", action="store_true", help="Print the complete inventory JSON")
    parser.add_argument(
        "--check", action="store_true", help="Fail on unreadable or unsafe artifacts"
    )
    parser.add_argument(
        "--fail-on-unprovenanced",
        action="store_true",
        help="Treat missing provenance as a release failure",
    )
    args = parser.parse_args(argv)
    root = args.root.expanduser().resolve()
    report = audit_artifacts(root)
    if args.write:
        destination = args.write.expanduser()
        ensure_parent_dir(destination)
        write_text(destination, json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        summary = report["summary"]
        print(
            f"Audited {summary['file_count']} artifacts; "
            f"{summary['duplicate_group_count']} duplicate groups; "
            f"{summary['unprovenanced_count']} without provenance"
        )
    if args.check and report["errors"]:
        return 1
    if args.fail_on_unprovenanced and report["unprovenanced"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
