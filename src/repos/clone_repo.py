from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Any, Optional

from git import Repo

from src.repos.cloning import _validate_repo_url


def _validate_destination(destination: Path) -> Path:
    destination = destination.expanduser()
    if destination.is_symlink() or any(
        parent.exists() and parent.is_symlink() for parent in (destination, *destination.parents)
    ):
        raise ValueError(f"Refusing symlink clone destination: {destination}")
    resolved = destination.resolve()
    protected = {Path("/").resolve(), Path.home().resolve(), Path.cwd().resolve()}
    if resolved in protected:
        raise ValueError(f"Refusing destructive clone destination: {resolved}")
    if destination.exists() and not destination.is_dir():
        raise ValueError(f"Clone destination is not a directory: {destination}")
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError(f"Destination not empty: {destination}")
    return resolved


def clone_repository(
    url: str,
    destination: Path,
    branch: Optional[str] = None,
    shallow: bool = False,
    allow_unsafe_sources: bool = False,
) -> Path:
    # Local, SSH, HTTP, git, and file sources require an explicit opt-in;
    # HTTPS is the safe default.
    _validate_repo_url(url, allow_unsafe_sources=allow_unsafe_sources)
    if branch and (branch.startswith("-") or any(char in branch for char in "\r\n\x00")):
        raise ValueError("Unsafe branch name")
    destination = _validate_destination(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    created_by_call = not destination.exists()
    clone_kwargs: dict[str, Any] = {}
    if branch:
        clone_kwargs["branch"] = branch
    if shallow:
        clone_kwargs["depth"] = 1
        clone_kwargs["single_branch"] = True
    try:
        repo = Repo.clone_from(url, destination, **clone_kwargs)
        if not repo.working_tree_dir:
            raise RuntimeError("Git clone returned no working tree")
        return Path(repo.working_tree_dir)
    except Exception:
        if created_by_call and destination.exists() and destination.is_dir():
            shutil.rmtree(destination)
        raise


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clone a GitHub repository with optional branch and shallow options"
    )
    parser.add_argument("--url", required=True, help="Git repository URL")
    parser.add_argument("--dest", required=True, help="Destination directory path")
    parser.add_argument("--branch", required=False, help="Branch to checkout after clone")
    parser.add_argument("--shallow", action="store_true", help="Perform a shallow clone (depth=1)")
    parser.add_argument(
        "--allow-unsafe-sources",
        action="store_true",
        help="Allow HTTP, SSH, git, and file:// sources (HTTPS is the default)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(argv)
    dest = Path(args.dest)
    try:
        path = clone_repository(
            args.url,
            dest,
            branch=args.branch,
            shallow=args.shallow,
            allow_unsafe_sources=args.allow_unsafe_sources,
        )
        print(str(path))
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
