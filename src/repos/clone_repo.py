from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from git import Repo


def clone_repository(
    url: str, destination: Path, branch: Optional[str] = None, shallow: bool = False
) -> Path:
    destination = destination.expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError(f"Destination not empty: {destination}")
    clone_kwargs = {}
    if branch:
        clone_kwargs["branch"] = branch
    if shallow:
        clone_kwargs["depth"] = 1
        clone_kwargs["single_branch"] = True
    repo = Repo.clone_from(url, destination, **clone_kwargs)
    return Path(repo.working_tree_dir)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clone a GitHub repository with optional branch and shallow options"
    )
    parser.add_argument("--url", required=True, help="Git repository URL")
    parser.add_argument("--dest", required=True, help="Destination directory path")
    parser.add_argument("--branch", required=False, help="Branch to checkout after clone")
    parser.add_argument("--shallow", action="store_true", help="Perform a shallow clone (depth=1)")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    dest = Path(args.dest)
    try:
        path = clone_repository(args.url, dest, branch=args.branch, shallow=args.shallow)
        print(str(path))
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
