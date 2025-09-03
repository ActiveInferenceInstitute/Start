"""Repository cloning utilities with enhanced functionality.

This module provides high-level interfaces for cloning repositories
with progress tracking, error handling, and management features.
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import src.common.paths as paths


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
    if base_dir is None:
        base_dir = paths.repo_root() / "src" / "_clones"
    
    return base_dir / repo_name


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
    progress_callback: Optional[callable] = None,
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
    
    if destination is None:
        destination = get_clone_destination(repo_info.name)
    
    result = CloneResult(repo_name=repo_info.name, success=False)
    
    try:
        # Check if destination exists
        if destination.exists():
            if not force:
                result.error_message = f"Destination already exists: {destination}"
                return result
            else:
                # Remove existing directory
                import shutil
                shutil.rmtree(destination)
                if progress_callback:
                    progress_callback(f"Removed existing directory: {destination}")
        
        # Ensure parent directory exists
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        # Build git clone command
        cmd = ["git", "clone"]
        
        if repo_info.shallow:
            cmd.extend(["--depth", "1", "--single-branch"])
        
        if repo_info.branch:
            cmd.extend(["--branch", repo_info.branch])
        
        cmd.extend([repo_info.url, str(destination)])
        
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
            result.success = True
            result.destination = destination
            
            # Calculate size
            try:
                total_size = sum(
                    f.stat().st_size 
                    for f in destination.rglob('*') 
                    if f.is_file()
                )
                result.size_mb = total_size / (1024 * 1024)
            except Exception:
                result.size_mb = 0.0
            
            if progress_callback:
                progress_callback(f"✅ Successfully cloned {repo_info.name}")
        else:
            result.error_message = f"Git clone failed: {process.stderr}"
            if progress_callback:
                progress_callback(f"❌ Failed to clone {repo_info.name}")
    
    except subprocess.TimeoutExpired:
        result.error_message = "Clone operation timed out"
        if progress_callback:
            progress_callback(f"⏰ Clone timed out: {repo_info.name}")
    
    except Exception as e:
        result.error_message = str(e)
        if progress_callback:
            progress_callback(f"❌ Error cloning {repo_info.name}: {e}")
    
    result.clone_time = time.time() - start_time
    return result


def clone_multiple_repositories(
    repo_names: List[str],
    force: bool = False,
    max_concurrent: int = 3,
    progress_callback: Optional[callable] = None,
) -> List[CloneResult]:
    """Clone multiple repositories.
    
    Args:
        repo_names: List of repository names to clone
        force: Whether to overwrite existing directories
        max_concurrent: Maximum concurrent clones (not implemented yet)
        progress_callback: Optional callback for progress updates
        
    Returns:
        List of CloneResult objects
    """
    predefined_repos = get_predefined_repositories()
    results = []
    
    for repo_name in repo_names:
        if repo_name not in predefined_repos:
            result = CloneResult(
                repo_name=repo_name,
                success=False,
                error_message=f"Unknown repository: {repo_name}",
            )
            results.append(result)
            continue
        
        repo_info = predefined_repos[repo_name]
        result = clone_repository(repo_info, force=force, progress_callback=progress_callback)
        results.append(result)
    
    return results


def clone_all_repositories(
    category: Optional[str] = None,
    force: bool = False,
    progress_callback: Optional[callable] = None,
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
            name for name, info in predefined_repos.items()
            if info.category == category
        ]
    else:
        repos_to_clone = list(predefined_repos.keys())
    
    return clone_multiple_repositories(
        repos_to_clone, 
        force=force, 
        progress_callback=progress_callback
    )


def get_cloned_repositories() -> List[Tuple[str, Path]]:
    """Get list of already cloned repositories.
    
    Returns:
        List of (repo_name, path) tuples for existing clones
    """
    clones_dir = paths.repo_root() / "src" / "_clones"
    
    if not Path.exists(clones_dir):
        return []
    
    cloned = []
    for item in clones_dir.iterdir():
        if item.is_dir() and Path.exists(item / ".git"):
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
    
    try:
        # Check current branch
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        if result.returncode != 0:
            return False, "Could not determine current branch"
        
        current_branch = result.stdout.strip()
        
        # Pull latest changes
        result = subprocess.run(
            ["git", "pull", "origin", current_branch],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=60,
        )
        
        if result.returncode == 0:
            return True, f"Successfully updated {repo_path.name}"
        else:
            return False, f"Failed to update: {result.stderr}"
    
    except subprocess.TimeoutExpired:
        return False, "Update operation timed out"
    except Exception as e:
        return False, str(e)


def get_repository_status(repo_path: Path) -> Dict[str, any]:
    """Get status information for a repository.
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        Dictionary with repository status information
    """
    status = {
        "name": repo_path.name,
        "path": str(repo_path),
        "exists": repo_path.exists(),
        "is_git_repo": False,
        "branch": None,
        "last_commit": None,
        "uncommitted_changes": False,
        "size_mb": 0.0,
    }
    
    if not repo_path.exists():
        return status
    
    # Check if it's a git repository
    if not (repo_path / ".git").exists():
        return status
    
    status["is_git_repo"] = True
    
    try:
        # Get current branch
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            status["branch"] = result.stdout.strip()
    except Exception:
        pass
    
    try:
        # Get last commit
        result = subprocess.run(
            ["git", "log", "-1", "--format=%H %s %ad", "--date=short"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            status["last_commit"] = result.stdout.strip()
    except Exception:
        pass
    
    try:
        # Check for uncommitted changes
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            status["uncommitted_changes"] = bool(result.stdout.strip())
    except Exception:
        pass
    
    try:
        # Calculate size
        total_size = sum(
            f.stat().st_size 
            for f in repo_path.rglob('*') 
            if f.is_file()
        )
        status["size_mb"] = total_size / (1024 * 1024)
    except Exception:
        pass
    
    return status


def cleanup_failed_clones() -> List[str]:
    """Clean up any partially cloned or failed repositories.
    
    Returns:
        List of cleaned up directory names
    """
    clones_dir = paths.repo_root() / "src" / "_clones"
    
    if not Path.exists(clones_dir):
        return []
    
    cleaned = []
    
    for item in clones_dir.iterdir():
        if item.is_dir():
            # Check if it's a proper git repository
            if not Path.exists(item / ".git"):
                # Remove incomplete clone
                try:
                    import shutil
                    shutil.rmtree(item)
                    cleaned.append(item.name)
                except Exception:
                    continue
    
    return cleaned


def validate_repository_url(url: str) -> bool:
    """Validate that a repository URL is accessible.
    
    Args:
        url: Repository URL to validate
        
    Returns:
        True if URL appears valid and accessible
    """
    try:
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
