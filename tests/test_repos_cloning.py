"""Tests for repository cloning module."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.repos.cloning import (
    CloneResult,
    RepoInfo,
    cleanup_failed_clones,
    clone_all_repositories,
    clone_multiple_repositories,
    clone_repository,
    estimate_clone_time,
    get_clone_destination,
    get_cloned_repositories,
    get_predefined_repositories,
    get_repository_status,
    update_repository,
    validate_repository_url,
)


class TestRepoInfo:
    """Test RepoInfo dataclass."""
    
    def test_repo_info_basic(self):
        """Test basic RepoInfo creation."""
        repo = RepoInfo(
            name="test-repo",
            url="https://github.com/user/test-repo.git",
        )
        
        assert repo.name == "test-repo"
        assert repo.url == "https://github.com/user/test-repo.git"
        assert repo.branch is None
        assert repo.description == ""
        assert repo.category == "general"
        assert repo.shallow is True
        assert repo.destination is None
    
    def test_repo_info_complete(self):
        """Test RepoInfo with all fields."""
        repo = RepoInfo(
            name="complex-repo",
            url="https://github.com/user/complex-repo.git",
            branch="develop",
            description="A complex repository",
            category="research",
            shallow=False,
            destination="/custom/path",
        )
        
        assert repo.name == "complex-repo"
        assert repo.branch == "develop"
        assert repo.description == "A complex repository"
        assert repo.category == "research"
        assert repo.shallow is False
        assert repo.destination == "/custom/path"


class TestCloneResult:
    """Test CloneResult dataclass."""
    
    def test_clone_result_basic(self):
        """Test basic CloneResult creation."""
        result = CloneResult(repo_name="test-repo", success=True)
        
        assert result.repo_name == "test-repo"
        assert result.success is True
        assert result.destination is None
        assert result.error_message is None
        assert result.clone_time == 0.0
        assert result.size_mb == 0.0
    
    def test_clone_result_failure(self):
        """Test CloneResult for failure case."""
        result = CloneResult(
            repo_name="failed-repo",
            success=False,
            error_message="Clone failed",
        )
        
        assert result.repo_name == "failed-repo"
        assert result.success is False
        assert result.error_message == "Clone failed"


class TestGetPredefinedRepositories:
    """Test get_predefined_repositories function."""
    
    def test_get_predefined_repositories(self):
        """Test getting predefined repository configurations."""
        repos = get_predefined_repositories()
        
        assert isinstance(repos, dict)
        assert len(repos) > 0
        
        # Check for expected repositories
        assert "cognitive" in repos
        assert "rxinfer" in repos
        assert "pymdp" in repos
        
        # Validate structure
        for name, repo_info in repos.items():
            assert isinstance(repo_info, RepoInfo)
            assert repo_info.name == name
            assert repo_info.url.startswith("https://")
            assert isinstance(repo_info.description, str)
            assert isinstance(repo_info.category, str)
    
    def test_predefined_repositories_structure(self):
        """Test that predefined repositories have correct structure."""
        repos = get_predefined_repositories()
        
        cognitive = repos["cognitive"]
        assert cognitive.url == "https://github.com/ActiveInferenceInstitute/cognitive"
        assert cognitive.category == "active_inference"
        assert cognitive.shallow is True
        
        activeinference = repos["activeinference"]
        assert activeinference.branch == "textbook"
        assert "ActiveInference.jl" in activeinference.url


class TestGetCloneDestination:
    """Test get_clone_destination function."""
    
    def test_get_clone_destination_default(self):
        """Test getting default clone destination."""
        destination = get_clone_destination("test-repo")
        
        # Should end with the expected path structure regardless of repo root
        assert destination.name == "test-repo"
        assert destination.parent.name == "_clones"
        assert destination.parent.parent.name == "src"
    
    def test_get_clone_destination_custom_base(self):
        """Test getting clone destination with custom base."""
        base_dir = Path("/custom/clones")
        destination = get_clone_destination("test-repo", base_dir)
        
        expected = Path("/custom/clones/test-repo")
        assert destination == expected


class TestEstimateCloneTime:
    """Test estimate_clone_time function."""
    
    def test_estimate_clone_time_known_repos(self):
        """Test clone time estimation for known repositories."""
        # Test known repository patterns
        time_str = estimate_clone_time("https://github.com/ActiveInferenceInstitute/cognitive")
        assert isinstance(time_str, str)
        assert "seconds" in time_str
        
        time_str = estimate_clone_time("https://github.com/docxology/RxInferExamples.jl")
        assert isinstance(time_str, str)
        assert "seconds" in time_str
    
    def test_estimate_clone_time_unknown_repo(self):
        """Test clone time estimation for unknown repository."""
        time_str = estimate_clone_time("https://github.com/unknown/repo.git")
        assert isinstance(time_str, str)
        assert "seconds" in time_str
        assert "10-90" in time_str  # Default range


class TestCloneRepository:
    """Test clone_repository function."""
    
    @patch('subprocess.run')
    @patch('pathlib.Path.exists', return_value=False)
    @patch('pathlib.Path.mkdir')
    def test_clone_repository_success(self, mock_mkdir, mock_exists, mock_run):
        """Test successful repository cloning."""
        # Mock successful git clone
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        # Mock file size calculation
        with patch('pathlib.Path.rglob') as mock_rglob:
            mock_file = Mock()
            mock_file.stat.return_value = Mock(st_size=1024)
            mock_file.is_file.return_value = True
            mock_rglob.return_value = [mock_file, mock_file]  # Two files
            
            repo_info = RepoInfo("test-repo", "https://github.com/user/test-repo.git")
            result = clone_repository(repo_info)
        
        assert result.success is True
        assert result.repo_name == "test-repo"
        assert result.destination is not None
        assert result.size_mb > 0
        assert result.clone_time > 0
    
    @patch('subprocess.run')
    @patch('pathlib.Path.exists', return_value=True)
    def test_clone_repository_destination_exists_no_force(self, mock_exists, mock_run):
        """Test cloning when destination exists without force."""
        repo_info = RepoInfo("test-repo", "https://github.com/user/test-repo.git")
        result = clone_repository(repo_info, force=False)
        
        assert result.success is False
        assert "already exists" in result.error_message
        assert mock_run.call_count == 0  # Git should not be called
    
    @patch('subprocess.run')
    @patch('pathlib.Path.exists', return_value=True)
    @patch('shutil.rmtree')
    @patch('pathlib.Path.mkdir')
    def test_clone_repository_destination_exists_with_force(self, mock_mkdir, mock_rmtree, mock_exists, mock_run):
        """Test cloning when destination exists with force."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        with patch('pathlib.Path.rglob', return_value=[]):
            repo_info = RepoInfo("test-repo", "https://github.com/user/test-repo.git")
            progress_calls = []
            
            result = clone_repository(
                repo_info, 
                force=True,
                progress_callback=progress_calls.append
            )
        
        assert result.success is True
        assert mock_rmtree.called
        assert any("Removed existing" in call for call in progress_calls)
    
    @patch('subprocess.run')
    @patch('pathlib.Path.exists', return_value=False)
    @patch('pathlib.Path.mkdir')
    def test_clone_repository_git_failure(self, mock_mkdir, mock_exists, mock_run):
        """Test repository cloning with git failure."""
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="Permission denied")
        
        repo_info = RepoInfo("test-repo", "https://github.com/user/test-repo.git")
        result = clone_repository(repo_info)
        
        assert result.success is False
        assert "Permission denied" in result.error_message
    
    @patch('subprocess.run', side_effect=subprocess.TimeoutExpired(["git"], 300))
    @patch('pathlib.Path.exists', return_value=False)
    @patch('pathlib.Path.mkdir')
    def test_clone_repository_timeout(self, mock_mkdir, mock_exists, mock_run):
        """Test repository cloning with timeout."""
        repo_info = RepoInfo("test-repo", "https://github.com/user/test-repo.git")
        result = clone_repository(repo_info)
        
        assert result.success is False
        assert "timed out" in result.error_message
    
    @patch('subprocess.run', side_effect=Exception("Network error"))
    @patch('pathlib.Path.exists', return_value=False)
    @patch('pathlib.Path.mkdir')
    def test_clone_repository_exception(self, mock_mkdir, mock_exists, mock_run):
        """Test repository cloning with exception."""
        repo_info = RepoInfo("test-repo", "https://github.com/user/test-repo.git")
        result = clone_repository(repo_info)
        
        assert result.success is False
        assert "Network error" in result.error_message
    
    def test_clone_repository_with_branch(self):
        """Test cloning repository with specific branch."""
        with patch('subprocess.run') as mock_run:
            with patch('pathlib.Path.exists', return_value=False):
                with patch('pathlib.Path.mkdir'):
                    with patch('pathlib.Path.rglob', return_value=[]):
                        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
                        
                        repo_info = RepoInfo(
                            "test-repo", 
                            "https://github.com/user/test-repo.git",
                            branch="develop"
                        )
                        result = clone_repository(repo_info)
        
        # Verify git clone was called with branch argument
        args = mock_run.call_args[0][0]
        assert "--branch" in args
        assert "develop" in args
        assert result.success is True
    
    def test_clone_repository_shallow_vs_full(self):
        """Test cloning with shallow vs full clone."""
        with patch('subprocess.run') as mock_run:
            with patch('pathlib.Path.exists', return_value=False):
                with patch('pathlib.Path.mkdir'):
                    with patch('pathlib.Path.rglob', return_value=[]):
                        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
                        
                        # Test shallow clone
                        repo_info = RepoInfo("test-repo", "https://example.com/repo.git", shallow=True)
                        clone_repository(repo_info)
                        
                        shallow_args = mock_run.call_args[0][0]
                        assert "--depth" in shallow_args
                        assert "1" in shallow_args
                        
                        # Test full clone
                        repo_info.shallow = False
                        clone_repository(repo_info)
                        
                        full_args = mock_run.call_args[0][0]
                        assert "--depth" not in full_args


class TestCloneMultipleRepositories:
    """Test clone_multiple_repositories function."""
    
    @patch('src.repos.cloning.get_predefined_repositories')
    @patch('src.repos.cloning.clone_repository')
    def test_clone_multiple_repositories_success(self, mock_clone, mock_get_repos):
        """Test cloning multiple repositories successfully."""
        # Mock predefined repositories
        test_repo = RepoInfo("test-repo", "https://example.com/test.git")
        mock_get_repos.return_value = {"test-repo": test_repo}
        
        # Mock clone results
        mock_clone.return_value = CloneResult("test-repo", True)
        
        results = clone_multiple_repositories(["test-repo"])
        
        assert len(results) == 1
        assert results[0].success is True
        assert results[0].repo_name == "test-repo"
        assert mock_clone.call_count == 1
    
    @patch('src.repos.cloning.get_predefined_repositories')
    def test_clone_multiple_repositories_unknown_repo(self, mock_get_repos):
        """Test cloning unknown repository."""
        mock_get_repos.return_value = {}
        
        results = clone_multiple_repositories(["unknown-repo"])
        
        assert len(results) == 1
        assert results[0].success is False
        assert "Unknown repository" in results[0].error_message
    
    @patch('src.repos.cloning.get_predefined_repositories')
    @patch('src.repos.cloning.clone_repository')
    def test_clone_multiple_repositories_mixed_results(self, mock_clone, mock_get_repos):
        """Test cloning multiple repositories with mixed results."""
        # Mock predefined repositories
        repos = {
            "success-repo": RepoInfo("success-repo", "https://example.com/success.git"),
            "fail-repo": RepoInfo("fail-repo", "https://example.com/fail.git"),
        }
        mock_get_repos.return_value = repos
        
        # Mock clone results
        def mock_clone_side_effect(repo_info, **kwargs):
            if repo_info.name == "success-repo":
                return CloneResult("success-repo", True)
            else:
                return CloneResult("fail-repo", False, error_message="Clone failed")
        
        mock_clone.side_effect = mock_clone_side_effect
        
        results = clone_multiple_repositories(["success-repo", "fail-repo"])
        
        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is False
        assert "Clone failed" in results[1].error_message
    
    @patch('src.repos.cloning.get_predefined_repositories')
    @patch('src.repos.cloning.clone_repository')
    def test_clone_multiple_repositories_with_progress(self, mock_clone, mock_get_repos):
        """Test cloning multiple repositories with progress callback."""
        test_repo = RepoInfo("test-repo", "https://example.com/test.git")
        mock_get_repos.return_value = {"test-repo": test_repo}
        mock_clone.return_value = CloneResult("test-repo", True)
        
        progress_calls = []
        results = clone_multiple_repositories(
            ["test-repo"], 
            progress_callback=progress_calls.append
        )
        
        assert len(results) == 1
        # Verify progress callback was passed to clone_repository
        mock_clone.assert_called_with(test_repo, force=False, progress_callback=progress_calls.append)


class TestCloneAllRepositories:
    """Test clone_all_repositories function."""
    
    @patch('src.repos.cloning.clone_multiple_repositories')
    @patch('src.repos.cloning.get_predefined_repositories')
    def test_clone_all_repositories_no_category(self, mock_get_repos, mock_clone_multiple):
        """Test cloning all repositories without category filter."""
        repos = {
            "repo1": RepoInfo("repo1", "url1", category="cat1"),
            "repo2": RepoInfo("repo2", "url2", category="cat2"),
        }
        mock_get_repos.return_value = repos
        mock_clone_multiple.return_value = []
        
        clone_all_repositories()
        
        # Should clone all repositories
        mock_clone_multiple.assert_called_once_with(
            ["repo1", "repo2"], 
            force=False, 
            progress_callback=None
        )
    
    @patch('src.repos.cloning.clone_multiple_repositories')
    @patch('src.repos.cloning.get_predefined_repositories')
    def test_clone_all_repositories_with_category(self, mock_get_repos, mock_clone_multiple):
        """Test cloning all repositories with category filter."""
        repos = {
            "repo1": RepoInfo("repo1", "url1", category="active_inference"),
            "repo2": RepoInfo("repo2", "url2", category="research"),
            "repo3": RepoInfo("repo3", "url3", category="active_inference"),
        }
        mock_get_repos.return_value = repos
        mock_clone_multiple.return_value = []
        
        clone_all_repositories(category="active_inference")
        
        # Should only clone repositories in specified category
        mock_clone_multiple.assert_called_once_with(
            ["repo1", "repo3"], 
            force=False, 
            progress_callback=None
        )


class TestGetClonedRepositories:
    """Test get_cloned_repositories function."""
    
    @patch('src.common.paths.repo_root', return_value=Path('/test/repo'))
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.iterdir')
    def test_get_cloned_repositories_success(self, mock_iterdir, mock_exists, mock_repo_root):
        """Test getting cloned repositories successfully."""
        # Mock directory structure
        clones_dir = Path("/test/repo/src/_clones")
        repo1_dir = clones_dir / "repo1"
        repo2_dir = clones_dir / "repo2"
        non_git_dir = clones_dir / "not-a-repo"
        
        mock_iterdir.return_value = [repo1_dir, repo2_dir, non_git_dir]
        
        def mock_exists_side_effect(path):
            if path == clones_dir:
                return True
            elif path == repo1_dir / ".git":
                return True
            elif path == repo2_dir / ".git":
                return True
            elif path == non_git_dir / ".git":
                return False
            return False
        
        mock_exists.side_effect = mock_exists_side_effect
        
        # Mock is_dir
        for dir_path in [repo1_dir, repo2_dir, non_git_dir]:
            dir_path.is_dir = Mock(return_value=True)
        
        cloned = get_cloned_repositories()
        
        assert len(cloned) == 2
        assert ("repo1", repo1_dir) in cloned
        assert ("repo2", repo2_dir) in cloned
        assert ("not-a-repo", non_git_dir) not in cloned
    
    @patch('src.common.paths.repo_root', return_value=Path('/test/repo'))
    @patch('pathlib.Path.exists', return_value=False)
    def test_get_cloned_repositories_no_clones_dir(self, mock_exists, mock_repo_root):
        """Test getting cloned repositories when clones directory doesn't exist."""
        cloned = get_cloned_repositories()
        
        assert len(cloned) == 0


class TestUpdateRepository:
    """Test update_repository function."""
    
    @patch('subprocess.run')
    def test_update_repository_success(self, mock_run):
        """Test successful repository update."""
        repo_path = Path("/test/repo")
        
        # Mock git commands
        mock_run.side_effect = [
            Mock(returncode=0, stdout="main\n", stderr=""),  # get branch
            Mock(returncode=0, stdout="Updated\n", stderr=""),  # pull
        ]
        
        # Mock .git directory exists
        with patch.object(repo_path / ".git", "exists", return_value=True):
            success, message = update_repository(repo_path)
        
        assert success is True
        assert "Successfully updated" in message
        assert mock_run.call_count == 2
    
    def test_update_repository_not_git_repo(self):
        """Test updating non-git repository."""
        repo_path = Path("/test/not-git")
        
        # Mock .git directory doesn't exist
        with patch.object(repo_path / ".git", "exists", return_value=False):
            success, message = update_repository(repo_path)
        
        assert success is False
        assert "Not a git repository" in message
    
    @patch('subprocess.run')
    def test_update_repository_branch_error(self, mock_run):
        """Test repository update with branch detection error."""
        repo_path = Path("/test/repo")
        
        # Mock git branch command failure
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="No branch")
        
        with patch.object(repo_path / ".git", "exists", return_value=True):
            success, message = update_repository(repo_path)
        
        assert success is False
        assert "Could not determine current branch" in message
    
    @patch('subprocess.run')
    def test_update_repository_pull_failure(self, mock_run):
        """Test repository update with pull failure."""
        repo_path = Path("/test/repo")
        
        # Mock git commands
        mock_run.side_effect = [
            Mock(returncode=0, stdout="main\n", stderr=""),  # get branch success
            Mock(returncode=1, stdout="", stderr="Pull failed"),  # pull failure
        ]
        
        with patch.object(repo_path / ".git", "exists", return_value=True):
            success, message = update_repository(repo_path)
        
        assert success is False
        assert "Pull failed" in message
    
    @patch('subprocess.run', side_effect=subprocess.TimeoutExpired(["git"], 60))
    def test_update_repository_timeout(self, mock_run):
        """Test repository update with timeout."""
        repo_path = Path("/test/repo")
        
        with patch.object(repo_path / ".git", "exists", return_value=True):
            success, message = update_repository(repo_path)
        
        assert success is False
        assert "timed out" in message


class TestGetRepositoryStatus:
    """Test get_repository_status function."""
    
    @patch('subprocess.run')
    @patch('pathlib.Path.rglob')
    def test_get_repository_status_complete(self, mock_rglob, mock_run):
        """Test getting complete repository status."""
        repo_path = Path("/test/repo")
        
        # Mock git commands
        mock_run.side_effect = [
            Mock(returncode=0, stdout="main\n", stderr=""),  # branch
            Mock(returncode=0, stdout="abc123 Last commit 2023-01-01\n", stderr=""),  # log
            Mock(returncode=0, stdout=" M file.txt\n", stderr=""),  # status
        ]
        
        # Mock file system
        mock_file = Mock()
        mock_file.stat.return_value = Mock(st_size=1024)
        mock_file.is_file.return_value = True
        mock_rglob.return_value = [mock_file]
        
        with patch.object(repo_path, "exists", return_value=True):
            with patch.object(repo_path / ".git", "exists", return_value=True):
                status = get_repository_status(repo_path)
        
        assert status["name"] == "repo"
        assert status["exists"] is True
        assert status["is_git_repo"] is True
        assert status["branch"] == "main"
        assert status["last_commit"] == "abc123 Last commit 2023-01-01"
        assert status["uncommitted_changes"] is True
        assert status["size_mb"] > 0
    
    def test_get_repository_status_not_exists(self):
        """Test getting status for non-existent repository."""
        repo_path = Path("/test/nonexistent")
        
        with patch.object(repo_path, "exists", return_value=False):
            status = get_repository_status(repo_path)
        
        assert status["name"] == "nonexistent"
        assert status["exists"] is False
        assert status["is_git_repo"] is False
        assert status["branch"] is None
    
    def test_get_repository_status_not_git(self):
        """Test getting status for non-git directory."""
        repo_path = Path("/test/notgit")
        
        with patch.object(repo_path, "exists", return_value=True):
            with patch.object(repo_path / ".git", "exists", return_value=False):
                status = get_repository_status(repo_path)
        
        assert status["exists"] is True
        assert status["is_git_repo"] is False
    
    @patch('subprocess.run', side_effect=Exception("Git error"))
    def test_get_repository_status_git_errors(self, mock_run):
        """Test getting status with git command errors."""
        repo_path = Path("/test/repo")
        
        with patch.object(repo_path, "exists", return_value=True):
            with patch.object(repo_path / ".git", "exists", return_value=True):
                with patch('pathlib.Path.rglob', return_value=[]):
                    status = get_repository_status(repo_path)
        
        assert status["is_git_repo"] is True
        assert status["branch"] is None
        assert status["last_commit"] is None
        assert status["uncommitted_changes"] is False


class TestCleanupFailedClones:
    """Test cleanup_failed_clones function."""
    
    @patch('src.common.paths.repo_root', return_value=Path('/test/repo'))
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.iterdir')
    @patch('shutil.rmtree')
    def test_cleanup_failed_clones_success(self, mock_rmtree, mock_iterdir, mock_exists, mock_repo_root):
        """Test cleaning up failed clones successfully."""
        clones_dir = Path("/test/repo/src/_clones")
        good_repo = clones_dir / "good-repo"
        failed_repo = clones_dir / "failed-repo"
        
        mock_iterdir.return_value = [good_repo, failed_repo]
        
        def mock_exists_side_effect(path):
            if path == clones_dir:
                return True
            elif path == good_repo / ".git":
                return True
            elif path == failed_repo / ".git":
                return False
            return False
        
        mock_exists.side_effect = mock_exists_side_effect
        
        # Mock is_dir
        good_repo.is_dir = Mock(return_value=True)
        failed_repo.is_dir = Mock(return_value=True)
        
        cleaned = cleanup_failed_clones()
        
        assert len(cleaned) == 1
        assert "failed-repo" in cleaned
        mock_rmtree.assert_called_once_with(failed_repo)
    
    @patch('src.common.paths.repo_root', return_value=Path('/test/repo'))
    @patch('pathlib.Path.exists', return_value=False)
    def test_cleanup_failed_clones_no_clones_dir(self, mock_exists, mock_repo_root):
        """Test cleanup when clones directory doesn't exist."""
        cleaned = cleanup_failed_clones()
        
        assert len(cleaned) == 0


class TestValidateRepositoryUrl:
    """Test validate_repository_url function."""
    
    @patch('subprocess.run')
    def test_validate_repository_url_valid(self, mock_run):
        """Test validating valid repository URL."""
        mock_run.return_value = Mock(returncode=0, stdout="refs/heads/main\n")
        
        is_valid = validate_repository_url("https://github.com/user/repo.git")
        
        assert is_valid is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "git" in args
        assert "ls-remote" in args
        assert "https://github.com/user/repo.git" in args
    
    @patch('subprocess.run')
    def test_validate_repository_url_invalid(self, mock_run):
        """Test validating invalid repository URL."""
        mock_run.return_value = Mock(returncode=128, stderr="Repository not found")
        
        is_valid = validate_repository_url("https://github.com/invalid/repo.git")
        
        assert is_valid is False
    
    @patch('subprocess.run', side_effect=Exception("Network error"))
    def test_validate_repository_url_exception(self, mock_run):
        """Test validating repository URL with exception."""
        is_valid = validate_repository_url("https://github.com/user/repo.git")
        
        assert is_valid is False


@pytest.mark.integration
class TestRepositoryCloningIntegration:
    """Integration tests for repository cloning."""
    
    def test_predefined_repositories_are_valid(self):
        """Test that predefined repository configurations are valid."""
        repos = get_predefined_repositories()
        
        for name, repo_info in repos.items():
            assert isinstance(repo_info.name, str)
            assert len(repo_info.name) > 0
            assert isinstance(repo_info.url, str)
            assert repo_info.url.startswith("https://")
            assert isinstance(repo_info.description, str)
            assert isinstance(repo_info.category, str)
            assert isinstance(repo_info.shallow, bool)
            
            if repo_info.branch:
                assert isinstance(repo_info.branch, str)
                assert len(repo_info.branch) > 0
    
    def test_clone_destination_path_creation(self):
        """Test that clone destination paths are created correctly."""
        test_repos = ["test-repo-1", "test-repo-2", "repo_with_underscores"]
        
        for repo_name in test_repos:
            destination = get_clone_destination(repo_name)
            
            assert isinstance(destination, Path)
            assert destination.name == repo_name
            assert "src/_clones" in str(destination)
    
    def test_estimate_clone_time_consistency(self):
        """Test that clone time estimation is consistent."""
        test_urls = [
            "https://github.com/ActiveInferenceInstitute/cognitive",
            "https://github.com/docxology/RxInferExamples.jl",
            "https://github.com/docxology/pymdp",
            "https://github.com/unknown/repository.git",
        ]
        
        for url in test_urls:
            time_estimate = estimate_clone_time(url)
            assert isinstance(time_estimate, str)
            assert "seconds" in time_estimate
            assert "-" in time_estimate  # Should be a range
    
    @patch('subprocess.run')
    @patch('pathlib.Path.exists', return_value=False)
    @patch('pathlib.Path.mkdir')
    def test_clone_repository_command_construction(self, mock_mkdir, mock_exists, mock_run):
        """Test that git clone commands are constructed correctly."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        with patch('pathlib.Path.rglob', return_value=[]):
            # Test basic clone
            repo_info = RepoInfo("basic-repo", "https://github.com/user/repo.git")
            clone_repository(repo_info)
            
            basic_args = mock_run.call_args[0][0]
            assert "git" in basic_args
            assert "clone" in basic_args
            assert "https://github.com/user/repo.git" in basic_args
            
            # Test shallow clone with branch
            repo_info = RepoInfo(
                "complex-repo", 
                "https://github.com/user/repo.git",
                branch="develop",
                shallow=True
            )
            clone_repository(repo_info)
            
            complex_args = mock_run.call_args[0][0]
            assert "--depth" in complex_args
            assert "1" in complex_args
            assert "--single-branch" in complex_args
            assert "--branch" in complex_args
            assert "develop" in complex_args
