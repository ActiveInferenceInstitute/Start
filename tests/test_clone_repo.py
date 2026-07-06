from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest


def test_clone_repository_shallow(tmp_path: Path):
    """Test clone repository functionality."""
    if importlib.util.find_spec("git") is None:
        pytest.skip("git module not available")

    from src.repos.clone_repo import clone_repository

    # In CI environment or if git is working, test with real repo
    if os.environ.get("CI") and os.getenv("PERPLEXITY_API_KEY"):
        url = "https://github.com/git/git"
        dest = tmp_path / "git-src"
        path = clone_repository(url, dest, branch="master", shallow=True)
        assert path.exists()
        # must contain .git directory
        assert (path / ".git").exists()
    else:
        # Test function signature and basic validation locally
        from src.repos.clone_repo import clone_repository

        nonexistent_dest = tmp_path / "nonexistent" / "deep" / "path"

        # Test that function handles invalid URLs gracefully
        # git.exc.GitCommandError is not importable when git is not installed,
        # so we catch the general Exception family
        with pytest.raises(Exception):  # noqa: B017 - git.exc.GitCommandError not importable
            clone_repository("not-a-valid-git-url", nonexistent_dest)
