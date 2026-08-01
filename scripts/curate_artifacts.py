"""Plan and apply explicitly reviewed generated-artifact curation.

The command is intentionally conservative: it never mutates artifacts during
planning, requires an allow-list of retained paths, verifies the audit hashes
again immediately before mutation, and refuses symlink or out-of-root paths.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from src.common.io import ensure_directory, path_within, write_json
from src.pipeline.artifacts import sha256_file


def _load_keep(path: Path) -> set[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    values: Any
    if isinstance(payload, list):
        values = payload
    elif isinstance(payload, dict):
        values = payload.get("keep", payload.get("retained", []))
    else:
        raise ValueError("review manifest must be a JSON list or an object with a keep list")
    if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
        raise ValueError("review manifest keep must be a list of path strings")
    return {Path(value).as_posix() for value in values}


def _load_audit(path: Path) -> tuple[Path, list[dict[str, Any]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("files"), list):
        raise ValueError("audit manifest must contain a files list")
    root = path.parent.parent.parent if path.parent.name == "artifact-manifests" else path.parent
    declared_root = payload.get("root")
    if isinstance(declared_root, str):
        root = Path(declared_root).expanduser()
    return root.resolve(), [record for record in payload["files"] if isinstance(record, dict)]


def _safe_record_path(root: Path, relative: str) -> Path:
    candidate = root / relative
    if candidate.is_symlink() or any(
        parent.exists() and parent.is_symlink() for parent in (candidate, *candidate.parents)
    ):
        raise ValueError(f"Refusing symlink artifact path: {relative}")
    resolved = candidate.resolve()
    if not path_within(resolved, root) or resolved == root:
        raise ValueError(f"Artifact path is outside the audit root: {relative}")
    return resolved


def plan_curation(
    audit_manifest: Path,
    review_manifest: Path,
    *,
    only_duplicates: bool = False,
) -> dict[str, Any]:
    root, records = _load_audit(audit_manifest.expanduser().resolve())
    keep = _load_keep(review_manifest.expanduser().resolve())
    by_path = {
        str(record.get("path")): record
        for record in records
        if isinstance(record.get("path"), str) and record.get("sha256")
    }
    duplicate_paths: set[str] = set()
    if only_duplicates:
        by_hash: dict[str, list[str]] = {}
        for path, record in by_path.items():
            by_hash.setdefault(str(record["sha256"]), []).append(path)
        duplicate_paths = {path for paths in by_hash.values() if len(paths) > 1 for path in paths}

    unknown_keep = sorted(keep - set(by_path))
    candidates = []
    for relative, record in sorted(by_path.items()):
        if relative in keep or (only_duplicates and relative not in duplicate_paths):
            continue
        candidates.append(
            {
                "path": relative,
                "sha256": str(record["sha256"]),
                "size_bytes": int(record.get("size_bytes", 0)),
                "action": "archive",
            }
        )
    return {
        "schema_version": "1.0",
        "root": str(root),
        "audit_manifest": str(audit_manifest.expanduser().resolve()),
        "review_manifest": str(review_manifest.expanduser().resolve()),
        "only_duplicates": only_duplicates,
        "retained_count": len(keep & set(by_path)),
        "unknown_retained_paths": unknown_keep,
        "candidate_count": len(candidates),
        "candidates": candidates,
    }


def apply_curation(plan: dict[str, Any], *, archive_dir: Path | None, remove: bool) -> list[str]:
    if plan.get("unknown_retained_paths"):
        raise ValueError("review manifest contains paths that are absent from the audit manifest")
    root = Path(str(plan["root"])).expanduser().resolve()
    if archive_dir is None and not remove:
        raise ValueError("mutation requires --archive-dir or explicit --remove")
    archive_root = None
    if archive_dir is not None:
        archive_root = archive_dir.expanduser().resolve()
        if archive_root == root or not path_within(archive_root, root.parent):
            raise ValueError("archive directory must be outside the audited data root")
        ensure_directory(archive_root)

    changed: list[str] = []
    for record in plan.get("candidates", []):
        relative = str(record["path"])
        source = _safe_record_path(root, relative)
        if not source.is_file():
            raise FileNotFoundError(f"Audited artifact is missing: {relative}")
        if sha256_file(source) != str(record["sha256"]):
            raise ValueError(f"Artifact changed since audit: {relative}")
        if remove:
            source.unlink()
        else:
            assert archive_root is not None
            destination = archive_root / relative
            if destination.exists() or destination.is_symlink():
                raise FileExistsError(f"Archive destination already exists: {destination}")
            ensure_directory(destination.parent)
            shutil.move(str(source), str(destination))
        changed.append(relative)
    return changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True, help="Artifact audit JSON")
    parser.add_argument(
        "--keep", type=Path, required=True, help="Reviewed JSON list or object of retained paths"
    )
    parser.add_argument("--archive-dir", type=Path, help="Move candidates beneath this directory")
    parser.add_argument(
        "--remove", action="store_true", help="Permanently remove candidates after hash checks"
    )
    parser.add_argument(
        "--only-duplicates", action="store_true", help="Plan only duplicate-content candidates"
    )
    parser.add_argument("--apply", action="store_true", help="Apply the reviewed plan")
    parser.add_argument("--write-plan", type=Path, help="Write the plan JSON to this path")
    parser.add_argument("--json", action="store_true", help="Print the plan/result JSON")
    args = parser.parse_args(argv)
    if args.remove and args.archive_dir:
        parser.error("--remove and --archive-dir are mutually exclusive")
    plan = plan_curation(args.manifest, args.keep, only_duplicates=args.only_duplicates)
    if args.apply:
        plan["applied"] = True
        plan["changed"] = apply_curation(plan, archive_dir=args.archive_dir, remove=args.remove)
    else:
        plan["applied"] = False
        plan["changed"] = []
    if args.write_plan:
        write_json(args.write_plan, plan)
    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        mode = "applied" if args.apply else "planned"
        print(
            f"Curation {mode}: {plan['candidate_count']} candidates, "
            f"{len(plan['changed'])} changed"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
