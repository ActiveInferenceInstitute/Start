"""Repository cloning utilities with enhanced functionality.

This module provides high-level interfaces for cloning repositories
with progress tracking, error handling, and management features.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import src.common.paths as paths
from src.common.io import path_within


def _redact_credentials(value: object) -> str:
    """Strip userinfo credentials from URLs that appear in error/progress text."""
    text = str(value)

    def _replace(match: re.Match[str]) -> str:
        return f"{match.group('scheme')}//{match.group('host')}"

    return re.sub(
        r"(?P<scheme>[a-z][a-z0-9+.-]*://)(?P<userinfo>[^/@\s]+@)(?P<host>[^/\s]+)",
        _replace,
        text,
        flags=re.IGNORECASE,
    )


_GIT_UNSAFE_CONFIG = re.compile(
    r"\bhookspath\s*=|^\s*fsmonitor\s*=|insteadOf\s*=|" r"^\s*\[\s*filter\b|^\s*\[\s*url\b",
    re.IGNORECASE | re.MULTILINE,
)


def _git_safe_env() -> dict[str, str]:
    """Environment for git commands run inside potentially-untrusted trees."""
    env = dict(os.environ)
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = "/dev/null"
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def _git_safe_command(*args: str) -> list[str]:
    """Git command that disables committed hooks and optional locking."""
    return [
        "git",
        "-c",
        "core.hooksPath=/dev/null",
        "--no-optional-locks",
        *args,
    ]


def _unsafe_repo_config_message(repo_path: Path) -> str | None:
    """Return a refusal reason when a clone's .git/config is unsafe to run."""
    config_path = repo_path / ".git" / "config"
    if not config_path.is_file() or config_path.is_symlink():
        return "repository .git/config missing or is a symlink"
    try:
        content = config_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"repository .git/config unreadable: {exc}"
    if _GIT_UNSAFE_CONFIG.search(content):
        return (
            "repository .git/config enables hooks, filters, fsmonitor, or url rewrites; "
            "refusing to run git inside this tree"
        )
    return None


@dataclass
class RepoInfo:
    """Information about a repository to clone."""

    name: str
    url: str
    branch: Optional[str] = None
    description: str = ""
    category: str = "general"
    shallow: bool = True
    destination: Optional[str] = None


@dataclass
class CloneResult:
    """Result of a repository cloning operation."""

    repo_name: str
    success: bool
    destination: Optional[Path] = None
    error_message: Optional[str] = None
    clone_time: float = 0.0
    size_mb: float = 0.0


def get_predefined_repositories() -> Dict[str, RepoInfo]:
    """Get predefined repository configurations.

    Returns:
        Dictionary mapping repo names to RepoInfo objects
    """
    repos = {
        "cognitive": RepoInfo(
            name="cognitive",
            url="https://github.com/ActiveInferenceInstitute/cognitive",
            description="Active Inference Institute cognitive science repository",
            category="active_inference",
            shallow=True,
        ),
        "gnn": RepoInfo(
            name="gnn",
            url="https://github.com/ActiveInferenceInstitute/GeneralizedNotationNotation/",
            description="Generalized Notation Notation (GNN) by Active Inference Institute",
            category="active_inference",
            shallow=True,
        ),
        "cerebrum": RepoInfo(
            name="cerebrum",
            url="https://github.com/ActiveInferenceInstitute/CEREBRUM",
            description="CEREBRUM project by Active Inference Institute",
            category="active_inference",
            shallow=True,
        ),
        "rxinfer": RepoInfo(
            name="rxinfer",
            url="https://github.com/docxology/RxInferExamples.jl",
            description="RxInfer.jl examples and tutorials",
            category="active_inference",
            shallow=True,
        ),
        "activeinference": RepoInfo(
            name="activeinference",
            url="https://github.com/docxology/ActiveInference.jl",
            branch="textbook",
            description="ActiveInference.jl textbook branch",
            category="active_inference",
            shallow=True,
        ),
        "pymdp": RepoInfo(
            name="pymdp",
            url="https://github.com/docxology/pymdp",
            branch="textbook",
            description="Python implementation of Markov Decision Processes",
            category="active_inference",
            shallow=True,
        ),
        "lean_niche": RepoInfo(
            name="lean_niche",
            url="https://github.com/docxology/lean_niche",
            description="Lean theorem proving and verification environment (LeanNiche)",
            category="formal_methods",
            shallow=True,
        ),
        "template": RepoInfo(
            name="template",
            url="https://github.com/docxology/template",
            description="Thin orchestrator research manuscript template and utilities",
            category="infrastructure",
            shallow=True,
        ),
        "axiom": RepoInfo(
            name="axiom",
            url="https://github.com/VersesTech/axiom",
            description="VERSES AXIOM knowledge operating system components",
            category="infrastructure",
            shallow=True,
        ),
    }

    return repos


def get_clone_destination(repo_name: str, base_dir: Optional[Path] = None) -> Path:
    """Get the destination path for cloning a repository.

    Args:
        repo_name: Name of the repository
        base_dir: Base directory for clones (defaults to src/_clones)

    Returns:
        Path where repository should be cloned
    """
    _validate_repo_name(repo_name)
    return _resolve_clone_root(base_dir) / repo_name


def _resolve_clone_root(base_dir: Optional[Path] = None) -> Path:
    raw_root = (
        Path(base_dir).expanduser()
        if base_dir is not None
        else paths.repo_root() / "src" / "_clones"
    )
    if raw_root.exists() and raw_root.is_symlink():
        raise ValueError(f"Clone root cannot be a symlink: {raw_root}")
    if any(parent.exists() and parent.is_symlink() for parent in (raw_root, *raw_root.parents)):
        raise ValueError(f"Clone root has a symlink boundary: {raw_root}")
    root = raw_root.resolve()
    if root in {Path("/").resolve(), Path.home().resolve()}:
        raise ValueError(f"Refusing destructive clone root: {root}")
    return root


def _validate_repo_name(repo_name: str) -> None:
    if not repo_name or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", repo_name):
        raise ValueError(f"Unsafe repository name: {repo_name!r}")


def _validate_repo_url(url: str, *, allow_unsafe_sources: bool = False) -> None:
    if not url or url.startswith("-") or any(char in url for char in "\n\r\x00"):
        raise ValueError("Unsafe repository URL")
    parsed = urlparse(url)
    if parsed.scheme == "https":
        if parsed.username or parsed.password or not parsed.netloc:
            raise ValueError("HTTPS repository URL must not contain credentials")
        return
    if not allow_unsafe_sources:
        raise ValueError(
            "Only HTTPS repository sources are allowed by default; "
            "pass allow_unsafe_sources=True for local, SSH, HTTP, or git sources"
        )
    if parsed.scheme not in {"http", "ssh", "git", "file"} and not Path(url).is_absolute():
        raise ValueError(f"Unsupported repository URL: {url}")


def estimate_clone_time(repo_url: str) -> str:
    """Estimate clone time based on repository characteristics.

    Args:
        repo_url: Repository URL

    Returns:
        Estimated time range as string
    """
    # Simple heuristics based on known repositories
    if "ActiveInference" in repo_url or "cognitive" in repo_url:
        return "30-60 seconds"
    elif "RxInfer" in repo_url:
        return "10-30 seconds"
    elif "pymdp" in repo_url:
        return "15-45 seconds"
    else:
        return "10-90 seconds"


def clone_repository(
    repo_info: RepoInfo,
    destination: Optional[Path] = None,
    force: bool = False,
    progress_callback: Optional[Callable[..., Any]] = None,
    base_dir: Optional[Path] = None,
    allow_unsafe_sources: bool = False,
) -> CloneResult:
    """Clone a single repository with progress tracking.

    Args:
        repo_info: Repository information
        destination: Destination path (auto-generated if None)
        force: Whether to overwrite existing directory
        progress_callback: Optional callback for progress updates

    Returns:
        CloneResult with operation details
    """
    start_time = time.time()

    try:
        _validate_repo_name(repo_info.name)
        _validate_repo_url(repo_info.url, allow_unsafe_sources=allow_unsafe_sources)
    except ValueError as exc:
        return CloneResult(repo_name=repo_info.name, success=False, error_message=str(exc))

    try:
        if destination is None:
            destination = get_clone_destination(repo_info.name, base_dir)
        else:
            raw_destination = Path(destination).expanduser()
            if raw_destination.is_symlink() or any(
                parent.exists() and parent.is_symlink()
                for parent in (raw_destination, *raw_destination.parents)
            ):
                return CloneResult(
                    repo_name=repo_info.name,
                    success=False,
                    error_message=f"Destination has a symlink boundary: {raw_destination}",
                )
            destination = raw_destination.resolve()
            clone_root = _resolve_clone_root(base_dir) if base_dir else destination.parent
            if not path_within(destination, clone_root):
                return CloneResult(
                    repo_name=repo_info.name,
                    success=False,
                    error_message=f"Destination is outside clone root: {destination}",
                )
            if destination in {Path("/").resolve(), Path.home().resolve()}:
                return CloneResult(
                    repo_name=repo_info.name,
                    success=False,
                    error_message=f"Refusing destructive clone destination: {destination}",
                )
    except ValueError as exc:
        return CloneResult(repo_name=repo_info.name, success=False, error_message=str(exc))

    result = CloneResult(repo_name=repo_info.name, success=False)
    destination_preexisting = destination.exists()
    staging: Optional[Path] = None
    backup: Optional[Path] = None

    try:
        # Check if destination exists
        if destination.exists():
            if not force:
                result.error_message = f"Destination already exists: {destination}"
                return result
            else:
                if (
                    destination.is_symlink()
                    or not destination.is_dir()
                    or destination == destination.parent
                ):
                    raise ValueError(f"Refusing destructive clone destination: {destination}")
                staging = Path(
                    tempfile.mkdtemp(prefix=f".{destination.name}.clone-", dir=destination.parent)
                )
                staging.rmdir()

        # Ensure parent directory exists
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Build git clone command
        cmd = ["git", "clone"]

        if repo_info.branch and (
            repo_info.branch.startswith("-") or any(char in repo_info.branch for char in "\r\n\x00")
        ):
            raise ValueError(f"Unsafe branch name: {repo_info.branch!r}")

        if repo_info.shallow:
            cmd.extend(["--depth", "1", "--single-branch"])

        if repo_info.branch:
            cmd.extend(["--branch", repo_info.branch])

        clone_target = staging or destination
        cmd.extend([repo_info.url, str(clone_target)])

        if progress_callback:
            progress_callback(f"Starting clone: {repo_info.name}")

        # Execute clone command
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        if process.returncode == 0:
            if staging is not None:
                backup = destination.parent / f".{destination.name}.backup-{uuid.uuid4().hex}"
                destination.rename(backup)
                try:
                    staging.rename(destination)
                    staging = None
                except Exception:
                    backup.rename(destination)
                    raise
                try:
                    shutil.rmtree(backup)
                except OSError as exc:
                    result.error_message = (
                        f"Replacement succeeded but old clone cleanup failed: {exc}"
                    )
                backup = None
                if progress_callback:
                    progress_callback(f"Replaced existing directory: {destination}")
            result.success = True
            result.destination = destination

            # Calculate size
            try:
                total_size = sum(f.stat().st_size for f in destination.rglob("*") if f.is_file())
                result.size_mb = total_size / (1024 * 1024)
            except OSError as exc:
                result.size_mb = 0.0
                result.error_message = f"Clone succeeded but size calculation failed: {exc}"

            if progress_callback:
                progress_callback(f"✅ Successfully cloned {repo_info.name}")
        else:
            result.error_message = _redact_credentials(f"Git clone failed: {process.stderr}")
            if progress_callback:
                progress_callback(f"❌ Failed to clone {repo_info.name}")

    except subprocess.TimeoutExpired:
        result.error_message = "Clone operation timed out"
        if progress_callback:
            progress_callback(f"⏰ Clone timed out: {repo_info.name}")

    except Exception as e:
        result.error_message = _redact_credentials(str(e))
        if progress_callback:
            progress_callback(f"❌ Error cloning {repo_info.name}: {_redact_credentials(e)}")

    if staging is not None and staging.exists():
        try:
            if staging.is_dir() and not staging.is_symlink():
                shutil.rmtree(staging)
        except OSError as exc:
            result.error_message = f"{result.error_message}; cleanup failed: {exc}"
    if backup is not None and backup.exists() and not destination.exists():
        try:
            backup.rename(destination)
        except OSError as exc:
            result.error_message = f"{result.error_message}; restore failed: {exc}"
    if not result.success and not destination_preexisting and destination.exists():
        try:
            if destination.is_dir() and not destination.is_symlink():
                shutil.rmtree(destination)
        except OSError as exc:
            result.error_message = f"{result.error_message}; cleanup failed: {exc}"

    result.clone_time = time.time() - start_time
    return result


def clone_multiple_repositories(
    repo_names: List[str],
    force: bool = False,
    max_concurrent: int = 3,
    progress_callback: Optional[Callable[..., Any]] = None,
    base_dir: Optional[Path] = None,
    allow_unsafe_sources: bool = False,
) -> List[CloneResult]:
    """Clone multiple repositories.

    Args:
        repo_names: List of repository names to clone
        force: Whether to overwrite existing directories
        max_concurrent: Maximum number of simultaneous clone processes
        progress_callback: Optional callback for progress updates

    Returns:
        List of CloneResult objects
    """
    if max_concurrent < 1:
        raise ValueError("max_concurrent must be at least one")
    predefined_repos = get_predefined_repositories()

    def clone_one(repo_name: str) -> CloneResult:
        if repo_name not in predefined_repos:
            return CloneResult(
                repo_name=repo_name, success=False, error_message=f"Unknown repository: {repo_name}"
            )
        return clone_repository(
            predefined_repos[repo_name],
            force=force,
            progress_callback=progress_callback,
            base_dir=base_dir,
            allow_unsafe_sources=allow_unsafe_sources,
        )

    with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        return list(executor.map(clone_one, repo_names))


def clone_all_repositories(
    category: Optional[str] = None,
    force: bool = False,
    progress_callback: Optional[Callable[..., Any]] = None,
    max_concurrent: int = 3,
    base_dir: Optional[Path] = None,
    allow_unsafe_sources: bool = False,
) -> List[CloneResult]:
    """Clone all predefined repositories or repositories in a specific category.

    Args:
        category: Optional category filter
        force: Whether to overwrite existing directories
        progress_callback: Optional callback for progress updates

    Returns:
        List of CloneResult objects
    """
    predefined_repos = get_predefined_repositories()

    if category:
        # Filter by category
        repos_to_clone = [
            name for name, info in predefined_repos.items() if info.category == category
        ]
    else:
        repos_to_clone = list(predefined_repos.keys())

    return clone_multiple_repositories(
        repos_to_clone,
        force=force,
        max_concurrent=max_concurrent,
        progress_callback=progress_callback,
        base_dir=base_dir,
        allow_unsafe_sources=allow_unsafe_sources,
    )


def get_cloned_repositories(base_dir: Optional[Path] = None) -> List[Tuple[str, Path]]:
    """Get list of already cloned repositories.

    Returns:
        List of (repo_name, path) tuples for existing clones
    """
    clones_dir = _resolve_clone_root(base_dir)

    if not Path.exists(clones_dir):
        return []

    cloned = []
    for item in clones_dir.iterdir():
        if item.is_dir() and not item.is_symlink() and Path.exists(item / ".git"):
            cloned.append((item.name, item))

    return sorted(cloned)


def update_repository(repo_path: Path) -> Tuple[bool, str]:
    """Update an existing repository by pulling latest changes.

    Args:
        repo_path: Path to the repository

    Returns:
        Tuple of (success, message)
    """
    if not (repo_path / ".git").exists():
        return False, "Not a git repository"

    unsafe = _unsafe_repo_config_message(repo_path)
    if unsafe:
        return False, unsafe

    try:
        # Check current branch
        result = subprocess.run(
            _git_safe_command("branch", "--show-current"),
            cwd=repo_path,
            env=_git_safe_env(),
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return False, "Could not determine current branch"

        current_branch = result.stdout.strip()
        if not current_branch:
            return False, "Repository is detached; refusing to select an update branch"

        # Fetch + fast-forward instead of pull so no repo-committed hook can run.
        fetch = subprocess.run(
            _git_safe_command("fetch", "--force", "--quiet", "origin", current_branch),
            cwd=repo_path,
            env=_git_safe_env(),
            capture_output=True,
            text=True,
            timeout=60,
        )
        if fetch.returncode != 0:
            return False, _redact_credentials(f"Failed to update: {fetch.stderr}")
        merge = subprocess.run(
            _git_safe_command("merge", "--ff-only", f"origin/{current_branch}"),
            cwd=repo_path,
            env=_git_safe_env(),
            capture_output=True,
            text=True,
            timeout=60,
        )
        if merge.returncode == 0:
            return True, f"Successfully updated {repo_path.name}"
        return False, _redact_credentials(f"Failed to update: {merge.stderr}")

    except subprocess.TimeoutExpired:
        return False, "Update operation timed out"
    except Exception as e:
        return False, _redact_credentials(str(e))


def get_repository_status(repo_path: Path) -> Dict[str, Any]:
    """Get status information for a repository.

    Args:
        repo_path: Path to the repository

    Returns:
        Dictionary with repository status information
    """
    status: Dict[str, Any] = {
        "name": repo_path.name,
        "path": str(repo_path),
        "exists": repo_path.exists(),
        "is_git_repo": False,
        "branch": None,
        "last_commit": None,
        "uncommitted_changes": False,
        "size_mb": 0.0,
        "errors": [],
    }

    if not repo_path.exists():
        return status

    if repo_path.is_symlink():
        status["errors"].append("path: symlink repository paths are not inspected")
        return status

    # Check if it's a git repository
    if not (repo_path / ".git").exists():
        return status

    status["is_git_repo"] = True

    unsafe = _unsafe_repo_config_message(repo_path)
    if unsafe:
        status["errors"].append(unsafe)
        return status

    try:
        # Get current branch
        result = subprocess.run(
            _git_safe_command("branch", "--show-current"),
            cwd=repo_path,
            env=_git_safe_env(),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            status["branch"] = result.stdout.strip()
    except Exception as exc:
        status["errors"].append(f"branch: {exc}")

    try:
        # Get last commit
        result = subprocess.run(
            _git_safe_command("log", "-1", "--format=%H %s %ad", "--date=short"),
            cwd=repo_path,
            env=_git_safe_env(),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            status["last_commit"] = result.stdout.strip()
    except Exception as exc:
        status["errors"].append(f"last_commit: {exc}")

    try:
        # Check for uncommitted changes
        result = subprocess.run(
            _git_safe_command("status", "--porcelain"),
            cwd=repo_path,
            env=_git_safe_env(),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            status["uncommitted_changes"] = bool(result.stdout.strip())
    except Exception as exc:
        status["errors"].append(f"working_tree: {exc}")

    try:
        # Calculate size
        total_size = sum(f.stat().st_size for f in repo_path.rglob("*") if f.is_file())
        status["size_mb"] = total_size / (1024 * 1024)
    except OSError as exc:
        status["errors"].append(f"size: {exc}")

    return status


def cleanup_failed_clones(base_dir: Optional[Path] = None) -> List[str]:
    """Clean up any partially cloned or failed repositories.

    Returns:
        List of cleaned up directory names
    """
    clones_dir = _resolve_clone_root(base_dir)

    if not Path.exists(clones_dir):
        return []

    cleaned = []

    for item in clones_dir.iterdir():
        if item.is_dir() and not item.is_symlink():
            # Only remove directories we can identify as our own staging
            # leftovers or that are completely empty.  A non-empty, non-git
            # directory may be user data and is never auto-deleted.
            if Path.exists(item / ".git"):
                continue
            is_staging = item.name.startswith(".") and "clone-" in item.name
            is_empty = not any(item.iterdir())
            if not (is_staging or is_empty):
                continue
            try:
                shutil.rmtree(item)
                cleaned.append(item.name)
            except OSError:
                continue

    return cleaned


def validate_repository_url(url: str, *, allow_unsafe_sources: bool = False) -> bool:
    """Validate that a repository URL is accessible.

    Args:
        url: Repository URL to validate

    Returns:
        True if URL appears valid and accessible
    """
    try:
        _validate_repo_url(
            url,
            allow_unsafe_sources=allow_unsafe_sources,
        )
        # Try git ls-remote to check if repository is accessible
        result = subprocess.run(
            ["git", "ls-remote", "--heads", url],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False
