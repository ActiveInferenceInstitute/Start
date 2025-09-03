"""Tests for repository manager module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.repos.cloning import CloneResult, RepoInfo
from src.repos.manager import (
    RepositoryManager,
    create_repository_manager,
    format_clone_results,
    format_repository_status,
    format_repository_summary,
)


class TestRepositoryManager:
    """Test RepositoryManager class."""
    
    @patch('src.common.paths.repo_root', return_value=Path('/test/repo'))
    def test_repository_manager_init_default(self, mock_repo_root):
        """Test RepositoryManager initialization with defaults."""
        manager = RepositoryManager()
        
        expected_path = Path("/test/repo/src/_clones")
        assert manager.base_dir == expected_path
    
    def test_repository_manager_init_absolute_path(self):
        """Test RepositoryManager initialization with absolute path."""
        custom_path = Path("/custom/clones")
        manager = RepositoryManager(base_dir=custom_path)
        
        assert manager.base_dir == custom_path
    
    @patch('src.common.paths.repo_root', return_value=Path('/test/repo'))
    def test_repository_manager_init_relative_path(self, mock_repo_root):
        """Test RepositoryManager initialization with relative path."""
        manager = RepositoryManager(base_dir=Path("custom/clones"))
        
        expected_path = Path("/test/repo/custom/clones")
        assert manager.base_dir == expected_path
    
    @patch('src.repos.manager.get_predefined_repositories')
    def test_list_available_repositories(self, mock_get_repos):
        """Test listing available repositories."""
        mock_repos = {
            "test-repo": RepoInfo(
                "test-repo", 
                "https://github.com/user/test.git",
                branch="main",
                description="Test repository",
                category="test"
            )
        }
        mock_get_repos.return_value = mock_repos
        
        manager = RepositoryManager()
        available = manager.list_available_repositories()
        
        assert "test-repo" in available
        repo_info = available["test-repo"]
        assert repo_info["name"] == "test-repo"
        assert repo_info["url"] == "https://github.com/user/test.git"
        assert repo_info["branch"] == "main"
        assert repo_info["description"] == "Test repository"
        assert repo_info["category"] == "test"
    
    @patch('src.repos.manager.get_cloned_repositories')
    @patch('src.repos.manager.get_repository_status')
    def test_list_cloned_repositories(self, mock_get_status, mock_get_cloned):
        """Test listing cloned repositories."""
        mock_get_cloned.return_value = [
            ("repo1", Path("/clones/repo1")),
            ("repo2", Path("/clones/repo2")),
        ]
        
        mock_get_status.side_effect = [
            {"name": "repo1", "branch": "main", "size_mb": 10.0},
            {"name": "repo2", "branch": "develop", "size_mb": 5.0},
        ]
        
        manager = RepositoryManager()
        cloned = manager.list_cloned_repositories()
        
        assert len(cloned) == 2
        assert "repo1" in cloned
        assert "repo2" in cloned
        assert cloned["repo1"]["branch"] == "main"
        assert cloned["repo2"]["branch"] == "develop"
    
    @patch('src.repos.manager.get_predefined_repositories')
    def test_get_repository_categories(self, mock_get_repos):
        """Test getting repository categories."""
        mock_repos = {
            "repo1": RepoInfo("repo1", "url1", category="cat1"),
            "repo2": RepoInfo("repo2", "url2", category="cat1"),
            "repo3": RepoInfo("repo3", "url3", category="cat2"),
        }
        mock_get_repos.return_value = mock_repos
        
        manager = RepositoryManager()
        categories = manager.get_repository_categories()
        
        assert "cat1" in categories
        assert "cat2" in categories
        assert len(categories["cat1"]) == 2
        assert len(categories["cat2"]) == 1
        assert "repo1" in categories["cat1"]
        assert "repo2" in categories["cat1"]
        assert "repo3" in categories["cat2"]
    
    @patch('src.repos.manager.clone_multiple_repositories')
    def test_clone_repository_single(self, mock_clone_multiple):
        """Test cloning a single repository."""
        mock_result = CloneResult("test-repo", True)
        mock_clone_multiple.return_value = [mock_result]
        
        manager = RepositoryManager()
        result = manager.clone_repository("test-repo")
        
        assert result.repo_name == "test-repo"
        assert result.success is True
        mock_clone_multiple.assert_called_once_with(
            ["test-repo"], 
            force=False, 
            progress_callback=None
        )
    
    @patch('src.repos.manager.clone_multiple_repositories')
    def test_clone_repositories_multiple(self, mock_clone_multiple):
        """Test cloning multiple repositories."""
        mock_results = [
            CloneResult("repo1", True),
            CloneResult("repo2", False),
        ]
        mock_clone_multiple.return_value = mock_results
        
        manager = RepositoryManager()
        results = manager.clone_repositories(["repo1", "repo2"])
        
        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is False
        mock_clone_multiple.assert_called_once_with(
            ["repo1", "repo2"], 
            force=False, 
            progress_callback=None
        )
    
    @patch('src.repos.manager.clone_all_repositories')
    def test_clone_all(self, mock_clone_all):
        """Test cloning all repositories."""
        mock_results = [CloneResult("repo1", True)]
        mock_clone_all.return_value = mock_results
        
        manager = RepositoryManager()
        results = manager.clone_all(category="test", force=True)
        
        assert len(results) == 1
        mock_clone_all.assert_called_once_with(
            category="test",
            force=True,
            progress_callback=None,
        )
    
    @patch('src.repos.manager.update_repository')
    def test_update_repository(self, mock_update):
        """Test updating a single repository."""
        manager = RepositoryManager(base_dir=Path("/test/clones"))
        mock_update.return_value = (True, "Updated successfully")
        
        success, message = manager.update_repository("test-repo")
        
        assert success is True
        assert "Updated successfully" in message
        mock_update.assert_called_once_with(Path("/test/clones/test-repo"))
    
    def test_update_repository_not_found(self):
        """Test updating non-existent repository."""
        manager = RepositoryManager(base_dir=Path("/test/clones"))
        
        with patch('pathlib.Path.exists', return_value=False):
            success, message = manager.update_repository("test-repo")
        
        assert success is False
        assert "not found" in message
    
    @patch('src.repos.manager.get_cloned_repositories')
    @patch('src.repos.manager.update_repository')
    def test_update_all_repositories(self, mock_update, mock_get_cloned):
        """Test updating all repositories."""
        mock_get_cloned.return_value = [
            ("repo1", Path("/clones/repo1")),
            ("repo2", Path("/clones/repo2")),
        ]
        
        mock_update.side_effect = [
            (True, "repo1 updated"),
            (False, "repo2 failed"),
        ]
        
        manager = RepositoryManager()
        results = manager.update_all_repositories()
        
        assert len(results) == 2
        assert results[0] == ("repo1", True, "repo1 updated")
        assert results[1] == ("repo2", False, "repo2 failed")
    
    @patch('src.repos.manager.get_repository_status')
    def test_get_repository_status(self, mock_get_status):
        """Test getting repository status."""
        manager = RepositoryManager(base_dir=Path("/test/clones"))
        mock_status = {"name": "test-repo", "branch": "main"}
        mock_get_status.return_value = mock_status
        
        with patch('pathlib.Path.exists', return_value=True):
            status = manager.get_repository_status("test-repo")
        
        assert status == mock_status
        mock_get_status.assert_called_once_with(Path("/test/clones/test-repo"))
    
    def test_get_repository_status_not_found(self):
        """Test getting status of non-existent repository."""
        manager = RepositoryManager(base_dir=Path("/test/clones"))
        
        with patch('pathlib.Path.exists', return_value=False):
            status = manager.get_repository_status("test-repo")
        
        assert status is None
    
    @patch('src.repos.manager.cleanup_failed_clones')
    def test_cleanup_failed_clones(self, mock_cleanup):
        """Test cleaning up failed clones."""
        mock_cleanup.return_value = ["failed-repo1", "failed-repo2"]
        
        manager = RepositoryManager()
        cleaned = manager.cleanup_failed_clones()
        
        assert len(cleaned) == 2
        assert "failed-repo1" in cleaned
        assert "failed-repo2" in cleaned
    
    @patch('shutil.rmtree')
    def test_delete_repository_success(self, mock_rmtree):
        """Test deleting repository successfully."""
        manager = RepositoryManager(base_dir=Path("/test/clones"))
        
        with patch('pathlib.Path.exists', return_value=True):
            success, message = manager.delete_repository("test-repo")
        
        assert success is True
        assert "Successfully deleted" in message
        mock_rmtree.assert_called_once_with(Path("/test/clones/test-repo"))
    
    def test_delete_repository_not_found(self):
        """Test deleting non-existent repository."""
        manager = RepositoryManager(base_dir=Path("/test/clones"))
        
        with patch('pathlib.Path.exists', return_value=False):
            success, message = manager.delete_repository("test-repo")
        
        assert success is False
        assert "not found" in message
    
    @patch('shutil.rmtree', side_effect=Exception("Permission denied"))
    def test_delete_repository_error(self, mock_rmtree):
        """Test deleting repository with error."""
        manager = RepositoryManager(base_dir=Path("/test/clones"))
        
        with patch('pathlib.Path.exists', return_value=True):
            success, message = manager.delete_repository("test-repo")
        
        assert success is False
        assert "Permission denied" in message
    
    @patch('src.repos.manager.RepositoryManager.list_available_repositories')
    @patch('src.repos.manager.RepositoryManager.list_cloned_repositories')
    @patch('src.repos.manager.RepositoryManager.get_repository_categories')
    def test_get_summary(self, mock_categories, mock_cloned, mock_available):
        """Test getting repository summary."""
        mock_available.return_value = {"repo1": {}, "repo2": {}, "repo3": {}}
        mock_cloned.return_value = {
            "repo1": {"size_mb": 10.0},
            "repo2": {"size_mb": 5.0},
        }
        mock_categories.return_value = {
            "cat1": ["repo1", "repo2"],
            "cat2": ["repo3"],
        }
        
        manager = RepositoryManager()
        summary = manager.get_summary()
        
        assert summary["available_count"] == 3
        assert summary["cloned_count"] == 2
        assert summary["total_size_mb"] == 15.0
        assert summary["categories"] == ["cat1", "cat2"]
        assert summary["by_category"]["cat1"] == 2
        assert summary["by_category"]["cat2"] == 1
        assert summary["cloned_by_category"]["cat1"] == 2
        assert summary["cloned_by_category"]["cat2"] == 0
    
    @patch('shutil.which', return_value='/usr/bin/git')
    @patch('shutil.disk_usage', return_value=(100*1024**3, 50*1024**3, 50*1024**3))
    def test_validate_setup_success(self, mock_disk_usage, mock_which):
        """Test successful setup validation."""
        manager = RepositoryManager(base_dir=Path("/tmp/test_clones"))
        
        is_valid, issues = manager.validate_setup()
        
        assert is_valid is True
        assert len(issues) == 0
    
    @patch('shutil.which', return_value=None)
    def test_validate_setup_no_git(self, mock_which):
        """Test setup validation without git."""
        manager = RepositoryManager(base_dir=Path("/tmp/test_clones"))
        
        is_valid, issues = manager.validate_setup()
        
        assert is_valid is False
        assert any("Git is not installed" in issue for issue in issues)
    
    @patch('shutil.which', return_value='/usr/bin/git')
    @patch('shutil.disk_usage', return_value=(100*1024**3, 99*1024**3, 1024**2))  # Very low free space
    def test_validate_setup_low_disk_space(self, mock_disk_usage, mock_which):
        """Test setup validation with low disk space."""
        manager = RepositoryManager(base_dir=Path("/tmp/test_clones"))
        
        is_valid, issues = manager.validate_setup()
        
        assert is_valid is False
        assert any("Low disk space" in issue for issue in issues)
    
    @patch('src.repos.manager.RepositoryManager.list_available_repositories')
    @patch('src.repos.manager.RepositoryManager.list_cloned_repositories')
    @patch('src.repos.manager.RepositoryManager.get_summary')
    def test_export_configuration(self, mock_summary, mock_cloned, mock_available):
        """Test exporting configuration."""
        mock_available.return_value = {"repo1": {"url": "url1"}}
        mock_cloned.return_value = {"repo1": {"status": "ok"}}
        mock_summary.return_value = {"total": 1}
        
        manager = RepositoryManager(base_dir=Path("/test/clones"))
        config = manager.export_configuration()
        
        assert config["base_dir"] == "/test/clones"
        assert "repo1" in config["available_repositories"]
        assert config["cloned_repositories"] == ["repo1"]
        assert config["summary"] == {"total": 1}


class TestCreateRepositoryManager:
    """Test create_repository_manager function."""
    
    def test_create_repository_manager_default(self):
        """Test creating repository manager with defaults."""
        manager = create_repository_manager()
        
        assert isinstance(manager, RepositoryManager)
        assert "src/_clones" in str(manager.base_dir)
    
    def test_create_repository_manager_custom_base(self):
        """Test creating repository manager with custom base."""
        custom_base = Path("/custom/repos")
        manager = create_repository_manager(custom_base)
        
        assert isinstance(manager, RepositoryManager)
        assert manager.base_dir == custom_base


class TestFormatRepositorySummary:
    """Test format_repository_summary function."""
    
    def test_format_repository_summary_basic(self):
        """Test formatting basic repository summary."""
        summary = {
            "available_count": 5,
            "cloned_count": 3,
            "total_size_mb": 150.5,
            "categories": ["active_inference", "research"],
            "by_category": {"active_inference": 3, "research": 2},
            "cloned_by_category": {"active_inference": 2, "research": 1},
        }
        
        formatted = format_repository_summary(summary)
        
        assert "REPOSITORY SUMMARY" in formatted
        assert "Available repositories: 5" in formatted
        assert "Cloned repositories: 3" in formatted
        assert "150.5 MB" in formatted
        assert "active_inference: 2/3 cloned" in formatted
        assert "research: 1/2 cloned" in formatted
    
    def test_format_repository_summary_empty(self):
        """Test formatting empty repository summary."""
        summary = {
            "available_count": 0,
            "cloned_count": 0,
            "total_size_mb": 0.0,
            "categories": [],
            "by_category": {},
            "cloned_by_category": {},
        }
        
        formatted = format_repository_summary(summary)
        
        assert "Available repositories: 0" in formatted
        assert "Cloned repositories: 0" in formatted
        assert "0.0 MB" in formatted


class TestFormatCloneResults:
    """Test format_clone_results function."""
    
    def test_format_clone_results_mixed(self):
        """Test formatting mixed clone results."""
        results = [
            CloneResult("success-repo", True, Path("/clones/success"), size_mb=10.5, clone_time=30.2),
            CloneResult("fail-repo", False, error_message="Network error"),
            CloneResult("another-success", True, Path("/clones/another"), size_mb=5.0, clone_time=15.1),
        ]
        
        formatted = format_clone_results(results)
        
        assert "CLONE RESULTS" in formatted
        assert "Successful: 2" in formatted
        assert "Failed: 1" in formatted
        assert "success-repo" in formatted
        assert "another-success" in formatted
        assert "fail-repo" in formatted
        assert "10.5MB" in formatted
        assert "30.2s" in formatted
        assert "Network error" in formatted
    
    def test_format_clone_results_all_success(self):
        """Test formatting all successful clone results."""
        results = [
            CloneResult("repo1", True, size_mb=5.0, clone_time=10.0),
            CloneResult("repo2", True, size_mb=0.0, clone_time=0.0),  # No size/time info
        ]
        
        formatted = format_clone_results(results)
        
        assert "Successful: 2" in formatted
        assert "Failed: 0" in formatted
        assert "SUCCESSFUL CLONES" in formatted
        assert "FAILED CLONES" not in formatted
        assert "repo1 (5.0MB) in 10.0s" in formatted
        assert "repo2" in formatted
    
    def test_format_clone_results_all_failed(self):
        """Test formatting all failed clone results."""
        results = [
            CloneResult("fail1", False, error_message="Error 1"),
            CloneResult("fail2", False, error_message="Error 2"),
        ]
        
        formatted = format_clone_results(results)
        
        assert "Successful: 0" in formatted
        assert "Failed: 2" in formatted
        assert "SUCCESSFUL CLONES" not in formatted
        assert "FAILED CLONES" in formatted
        assert "fail1: Error 1" in formatted
        assert "fail2: Error 2" in formatted
    
    def test_format_clone_results_empty(self):
        """Test formatting empty clone results."""
        results = []
        
        formatted = format_clone_results(results)
        
        assert "Successful: 0" in formatted
        assert "Failed: 0" in formatted


class TestFormatRepositoryStatus:
    """Test format_repository_status function."""
    
    def test_format_repository_status_complete(self):
        """Test formatting complete repository status."""
        status_dict = {
            "repo1": {
                "path": "/clones/repo1",
                "is_git_repo": True,
                "branch": "main",
                "last_commit": "abc123 Initial commit",
                "uncommitted_changes": True,
                "size_mb": 15.5,
            },
            "repo2": {
                "path": "/clones/repo2",
                "is_git_repo": False,
                "size_mb": 0.0,
            },
        }
        
        formatted = format_repository_status(status_dict)
        
        assert "REPOSITORY STATUS" in formatted
        assert "repo1" in formatted
        assert "repo2" in formatted
        assert "/clones/repo1" in formatted
        assert "Branch: main" in formatted
        assert "Initial commit" in formatted
        assert "Uncommitted changes: Yes" in formatted
        assert "Size: 15.5 MB" in formatted
        assert "Not a git repository" in formatted
    
    def test_format_repository_status_minimal(self):
        """Test formatting minimal repository status."""
        status_dict = {
            "minimal-repo": {
                "path": "/clones/minimal",
                "is_git_repo": True,
                "branch": None,
                "last_commit": None,
                "uncommitted_changes": False,
                "size_mb": 0.0,
            }
        }
        
        formatted = format_repository_status(status_dict)
        
        assert "minimal-repo" in formatted
        assert "Branch: unknown" in formatted
        assert "Uncommitted changes: No" in formatted
    
    def test_format_repository_status_empty(self):
        """Test formatting empty repository status."""
        status_dict = {}
        
        formatted = format_repository_status(status_dict)
        
        assert "REPOSITORY STATUS" in formatted
        # Should only contain header


@pytest.mark.integration
class TestRepositoryManagerIntegration:
    """Integration tests for RepositoryManager."""
    
    @patch('src.repos.manager.get_predefined_repositories')
    @patch('src.repos.manager.get_cloned_repositories', return_value=[])
    def test_complete_workflow_list_operations(self, mock_cloned, mock_predefined):
        """Test complete workflow of listing operations."""
        mock_predefined.return_value = {
            "test-repo": RepoInfo(
                "test-repo",
                "https://github.com/test/repo.git",
                category="test",
                description="Test repository"
            )
        }
        
        manager = RepositoryManager()
        
        # Test available repositories
        available = manager.list_available_repositories()
        assert len(available) == 1
        assert "test-repo" in available
        
        # Test categories
        categories = manager.get_repository_categories()
        assert "test" in categories
        assert "test-repo" in categories["test"]
        
        # Test cloned repositories (empty)
        cloned = manager.list_cloned_repositories()
        assert len(cloned) == 0
        
        # Test summary
        summary = manager.get_summary()
        assert summary["available_count"] == 1
        assert summary["cloned_count"] == 0
        assert "test" in summary["categories"]
    
    def test_repository_manager_path_handling(self):
        """Test that RepositoryManager handles paths correctly."""
        # Test with various path types
        path_types = [
            Path("/absolute/path"),
            Path("relative/path"),
            "string/path",
        ]
        
        for path_input in path_types:
            manager = RepositoryManager(base_dir=path_input)
            
            # Should always result in absolute Path
            assert isinstance(manager.base_dir, Path)
            assert manager.base_dir.is_absolute()
    
    @patch('shutil.which')
    @patch('pathlib.Path.mkdir')
    @patch('shutil.disk_usage')
    def test_validate_setup_various_conditions(self, mock_disk_usage, mock_mkdir, mock_which):
        """Test setup validation under various conditions."""
        manager = RepositoryManager(base_dir=Path("/tmp/test_validation"))
        
        # Test with git available and sufficient disk space
        mock_which.return_value = "/usr/bin/git"
        mock_disk_usage.return_value = (100*1024**3, 20*1024**3, 80*1024**3)  # 80GB free
        
        is_valid, issues = manager.validate_setup()
        assert is_valid is True
        assert len(issues) == 0
        
        # Test with no git
        mock_which.return_value = None
        
        is_valid, issues = manager.validate_setup()
        assert is_valid is False
        assert len(issues) >= 1
        assert any("Git" in issue for issue in issues)
        
        # Test with git but low disk space
        mock_which.return_value = "/usr/bin/git"
        mock_disk_usage.return_value = (100*1024**3, 99.5*1024**3, 0.5*1024**3)  # 0.5GB free
        
        is_valid, issues = manager.validate_setup()
        assert is_valid is False
        assert any("disk space" in issue.lower() for issue in issues)
