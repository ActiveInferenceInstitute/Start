from __future__ import annotations

import subprocess
from pathlib import Path


def _git(*args: str, cwd: Path | None = None) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def test_clone_repository_uses_real_local_repository(tmp_path: Path):
    bare = tmp_path / "remote.git"
    source = tmp_path / "source"
    _git("init", "--bare", str(bare))
    _git("init", "-b", "main", str(source))
    _git("config", "user.email", "tests@example.invalid", cwd=source)
    _git("config", "user.name", "START tests", cwd=source)
    (source / "README.md").write_text("initial", encoding="utf-8")
    _git("add", ".", cwd=source)
    _git("commit", "-m", "initial", cwd=source)
    _git("remote", "add", "origin", str(bare), cwd=source)
    _git("push", "-u", "origin", "main", cwd=source)

    from src.repos.clone_repo import clone_repository

    try:
        clone_repository(str(bare), tmp_path / "unsafe-default")
    except ValueError as exc:
        assert "HTTPS repository sources" in str(exc)
    else:
        raise AssertionError("local repository was accepted without explicit opt-in")

    destination = tmp_path / "clones" / "project"
    path = clone_repository(str(bare), destination, branch="main", allow_unsafe_sources=True)
    assert path == destination.resolve()
    assert (path / ".git").exists()
    assert (path / "README.md").read_text(encoding="utf-8") == "initial"


def test_clone_repository_rejects_invalid_url_and_protected_destination(tmp_path: Path):
    from src.repos.clone_repo import clone_repository

    try:
        clone_repository("not-a-valid-git-url", tmp_path / "invalid")
    except ValueError as exc:
        assert "HTTPS repository sources" in str(exc)
    else:
        raise AssertionError("invalid repository URL was accepted")

    try:
        clone_repository("https://example.invalid/repo", Path.cwd())
    except ValueError as exc:
        assert "destructive clone destination" in str(exc)
    else:
        raise AssertionError("protected clone destination was accepted")
