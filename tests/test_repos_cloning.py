from __future__ import annotations

import subprocess

import pytest

from src.repos.cloning import (
    RepoInfo,
    cleanup_failed_clones,
    clone_repository,
    get_cloned_repositories,
    get_repository_status,
    update_repository,
)


def _git(*args: str, cwd=None) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _local_remote(tmp_path):
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
    return bare, source


def test_clone_and_status_use_real_git(tmp_path):
    bare, _ = _local_remote(tmp_path)
    destination = tmp_path / "clones" / "project"
    unsafe_default = clone_repository(RepoInfo("default", str(bare), shallow=False), destination)
    assert not unsafe_default.success
    assert "HTTPS repository sources" in (unsafe_default.error_message or "")
    result = clone_repository(
        RepoInfo("project", str(bare), shallow=False),
        destination,
        allow_unsafe_sources=True,
    )
    assert result.success
    assert (destination / ".git").exists()
    status = get_repository_status(destination)
    assert status["is_git_repo"] is True
    assert status["branch"] == "main"
    assert status["errors"] == []


def test_update_is_fast_forward_only(tmp_path):
    bare, source = _local_remote(tmp_path)
    destination = tmp_path / "clones" / "project"
    assert clone_repository(
        RepoInfo("project", str(bare), shallow=False),
        destination,
        allow_unsafe_sources=True,
    ).success
    (source / "README.md").write_text("updated", encoding="utf-8")
    _git("add", ".", cwd=source)
    _git("commit", "-m", "update", cwd=source)
    _git("push", cwd=source)
    success, message = update_repository(destination)
    assert success, message
    assert (destination / "README.md").read_text(encoding="utf-8") == "updated"


def test_clone_rejects_unsafe_names_and_destinations(tmp_path):
    unsafe = clone_repository(
        RepoInfo("../outside", "https://example.invalid/repo"), tmp_path / "x"
    )
    assert not unsafe.success
    assert "Unsafe repository name" in unsafe.error_message
    bare, _ = _local_remote(tmp_path)
    destination = tmp_path / "clones" / "project"
    destination.mkdir(parents=True)
    result = clone_repository(
        RepoInfo("project", str(bare), shallow=False),
        destination,
        force=False,
        base_dir=tmp_path / "other",
        allow_unsafe_sources=True,
    )
    assert not result.success
    assert "outside clone root" in result.error_message


def test_failed_clone_removes_new_partial_destination(tmp_path):
    destination = tmp_path / "clones" / "missing"
    result = clone_repository(
        RepoInfo("missing", str(tmp_path / "missing-remote.git"), shallow=False), destination
    )
    assert result.success is False
    assert not destination.exists()


def test_cleanup_only_removes_incomplete_children(tmp_path):
    clones = tmp_path / "clones"
    clones.mkdir()
    (clones / "partial").mkdir()
    good = clones / "good"
    (good / ".git").mkdir(parents=True)
    assert cleanup_failed_clones(clones) == ["partial"]
    assert good.exists()


def test_cloned_repositories_are_sorted(tmp_path):
    clones = tmp_path / "clones"
    for name in ("zeta", "alpha"):
        (clones / name / ".git").mkdir(parents=True)
    assert [name for name, _ in get_cloned_repositories(clones)] == ["alpha", "zeta"]


def test_invalid_concurrency_is_rejected():
    from src.repos.cloning import clone_multiple_repositories

    with pytest.raises(ValueError, match="max_concurrent"):
        clone_multiple_repositories([], max_concurrent=0)


def test_update_and_status_refuse_unsafe_repo_config(tmp_path):
    """Post-clone git ops must refuse repos whose config enables hooks/filters."""
    bare, source = _local_remote(tmp_path)
    destination = tmp_path / "clones" / "project"
    assert clone_repository(
        RepoInfo("project", str(bare), shallow=False),
        destination,
        allow_unsafe_sources=True,
    ).success
    config_path = destination / ".git" / "config"
    config_path.write_text(
        (config_path.read_text(encoding="utf-8") + "\n[core]\n\thooksPath = /tmp/evil-hooks\n"),
        encoding="utf-8",
    )
    ok, message = update_repository(destination)
    assert not ok
    assert "refusing" in message.lower()
    status = get_repository_status(destination)
    assert status["errors"] and "refusing" in status["errors"][0].lower()
