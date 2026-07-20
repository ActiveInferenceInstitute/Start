from __future__ import annotations

from pathlib import Path

import pytest

from src.repos.manager import RepositoryManager


def test_manager_keeps_custom_base_directory(tmp_path: Path) -> None:
    manager = RepositoryManager(base_dir=tmp_path / "clones")
    assert manager.base_dir == tmp_path / "clones"
    assert manager.get_repository_status("missing") is None


def test_manager_delete_refuses_outside_path(tmp_path: Path) -> None:
    manager = RepositoryManager(base_dir=tmp_path / "clones")
    path = manager.base_dir / "repo"
    path.mkdir(parents=True)
    success, message = manager.delete_repository("repo")
    assert success
    assert "Successfully deleted" in message


def test_manager_rejects_protected_base_directory() -> None:
    with pytest.raises(ValueError, match="unsafe repository manager base"):
        RepositoryManager(base_dir=Path("/"))
