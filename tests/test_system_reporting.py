"""Tests for system reporting module."""

from __future__ import annotations

import os
import platform
import socket
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.system.reporting import (
    ResourceUsage,
    SystemInfo,
    check_system_requirements,
    format_system_report,
    generate_system_report,
    get_basic_system_info,
    get_cpu_info,
    get_disk_usage,
    get_git_info,
    get_memory_info,
    get_network_info,
    get_python_environment_info,
    get_resource_usage,
    run_command_safely,
)


class TestSystemInfo:
    """Test SystemInfo dataclass."""
    
    def test_system_info_creation(self):
        """Test SystemInfo object creation."""
        info = SystemInfo()
        assert info.hostname == ""
        assert info.os_name == ""
        assert info.cpu_count == 0
        assert isinstance(info.disk_usage, dict)
        assert isinstance(info.ip_addresses, list)
        assert isinstance(info.git_info, dict)
    
    def test_system_info_with_data(self):
        """Test SystemInfo with actual data."""
        info = SystemInfo(
            hostname="test-host",
            os_name="Linux",
            cpu_count=4,
            memory_total_gb=16.0,
        )
        assert info.hostname == "test-host"
        assert info.os_name == "Linux"
        assert info.cpu_count == 4
        assert info.memory_total_gb == 16.0


class TestResourceUsage:
    """Test ResourceUsage dataclass."""
    
    def test_resource_usage_creation(self):
        """Test ResourceUsage object creation."""
        usage = ResourceUsage()
        assert usage.cpu_percent == 0.0
        assert usage.memory_percent == 0.0
        assert usage.memory_available_gb == 0.0
        assert isinstance(usage.load_average, list)
    
    def test_resource_usage_with_data(self):
        """Test ResourceUsage with actual data."""
        usage = ResourceUsage(
            cpu_percent=50.0,
            memory_percent=75.0,
            memory_available_gb=4.0,
            load_average=[1.0, 1.5, 2.0],
        )
        assert usage.cpu_percent == 50.0
        assert usage.memory_percent == 75.0
        assert usage.memory_available_gb == 4.0
        assert usage.load_average == [1.0, 1.5, 2.0]


class TestBasicSystemInfo:
    """Test get_basic_system_info function."""
    
    @patch('socket.gethostname', return_value='test-hostname')
    @patch('platform.system', return_value='Linux')
    @patch('platform.release', return_value='5.4.0')
    @patch('platform.platform', return_value='Linux-5.4.0-x86_64')
    @patch('platform.machine', return_value='x86_64')
    @patch('platform.processor', return_value='Intel64 Family')
    def test_get_basic_system_info_success(self, *mocks):
        """Test getting basic system info successfully."""
        info = get_basic_system_info()
        
        assert info["hostname"] == "test-hostname"
        assert info["os_name"] == "Linux"
        assert info["os_version"] == "5.4.0"
        assert info["os_details"] == "Linux-5.4.0-x86_64"
        assert info["architecture"] == "x86_64"
        assert info["processor"] == "Intel64 Family"
    
    @patch('platform.processor', return_value='')
    def test_get_basic_system_info_no_processor(self, mock_processor):
        """Test getting basic system info when processor is empty."""
        info = get_basic_system_info()
        assert info["processor"] == "Unknown"


class TestPythonEnvironmentInfo:
    """Test get_python_environment_info function."""
    
    def test_get_python_environment_info_basic(self):
        """Test getting Python environment info."""
        info = get_python_environment_info()
        
        assert "python_version" in info
        assert "python_implementation" in info
        assert "python_executable" in info
        assert "virtual_env" in info
        assert "sys_path_entries" in info
        
        # Validate actual values
        assert info["python_version"] == platform.python_version()
        assert info["python_executable"] == sys.executable
        assert int(info["sys_path_entries"]) > 0
    
    @patch('sys.prefix', '/venv/path')
    @patch('sys.base_prefix', '/usr')
    def test_get_python_environment_info_venv(self):
        """Test detecting virtual environment."""
        info = get_python_environment_info()
        assert info["virtual_env"] == "/venv/path"
    
    @patch.dict('os.environ', {'CONDA_DEFAULT_ENV': 'test-env'})
    def test_get_python_environment_info_conda(self):
        """Test detecting conda environment."""
        info = get_python_environment_info()
        assert info["virtual_env"] == "test-env"


class TestMemoryInfo:
    """Test get_memory_info function."""
    
    def test_get_memory_info_with_psutil(self):
        """Test getting memory info with psutil available."""
        mock_memory = Mock()
        mock_memory.total = 16 * 1024**3  # 16GB
        mock_memory.available = 8 * 1024**3  # 8GB
        mock_memory.used = 8 * 1024**3  # 8GB
        mock_memory.percent = 50.0
        
        # Mock the local psutil import within the function
        with patch('builtins.__import__') as mock_import:
            mock_psutil = Mock()
            mock_psutil.virtual_memory.return_value = mock_memory
            
            def side_effect(name, *args):
                if name == 'psutil':
                    return mock_psutil
                return __import__(name, *args)
            
            mock_import.side_effect = side_effect
            
            info = get_memory_info()
            
            assert info["total_gb"] == 16.0
            assert info["available_gb"] == 8.0
            assert info["used_gb"] == 8.0
            assert info["percent_used"] == 50.0
    
    def test_get_memory_info_no_psutil(self):
        """Test getting memory info without psutil."""
        with patch.dict('sys.modules', {'psutil': None}):
            # This should trigger ImportError and use fallback
            with patch('builtins.open', side_effect=ImportError()):
                info = get_memory_info()
                
                assert info["total_gb"] == 0.0
                assert info["available_gb"] == 0.0
                assert info["used_gb"] == 0.0
                assert info["percent_used"] == 0.0
    
    @patch('platform.system', return_value='Linux')
    @patch('builtins.open')
    def test_get_memory_info_linux_fallback(self, mock_open):
        """Test Linux fallback for memory info."""
        # Mock /proc/meminfo content
        meminfo_content = """MemTotal:       16777216 kB
MemAvailable:    8388608 kB"""
        
        mock_open.return_value.__enter__.return_value.read.return_value = meminfo_content
        
        # Mock psutil not available
        with patch.dict('sys.modules', {'psutil': None}):
            with patch('importlib.import_module', side_effect=ImportError()):
                info = get_memory_info()
                
                assert info["total_gb"] == pytest.approx(16.0, rel=1e-2)
                assert info["available_gb"] == pytest.approx(8.0, rel=1e-2)


class TestDiskUsage:
    """Test get_disk_usage function."""
    
    @patch('shutil.disk_usage', return_value=(100*1024**3, 60*1024**3, 40*1024**3))
    @patch('pathlib.Path.exists', return_value=True)
    def test_get_disk_usage_success(self, mock_exists, mock_disk_usage):
        """Test getting disk usage successfully."""
        paths = ["/test/path"]
        usage = get_disk_usage(paths)
        
        assert "/test/path" in usage
        path_usage = usage["/test/path"]
        assert path_usage["total_gb"] == pytest.approx(100.0, rel=1e-2)
        assert path_usage["used_gb"] == pytest.approx(60.0, rel=1e-2)
        assert path_usage["free_gb"] == pytest.approx(40.0, rel=1e-2)
        assert path_usage["percent_used"] == 60.0
    
    @patch('pathlib.Path.exists', return_value=False)
    def test_get_disk_usage_nonexistent_path(self, mock_exists):
        """Test getting disk usage for nonexistent path."""
        usage = get_disk_usage(["/nonexistent"])
        assert len(usage) == 0
    
    @patch('shutil.disk_usage', side_effect=Exception("Permission denied"))
    @patch('pathlib.Path.exists', return_value=True)
    def test_get_disk_usage_permission_error(self, mock_exists, mock_disk_usage):
        """Test handling disk usage permission error."""
        usage = get_disk_usage(["/restricted"])
        assert len(usage) == 0
    
    def test_get_disk_usage_default_paths(self):
        """Test getting disk usage with default paths."""
        with patch('shutil.disk_usage', return_value=(100*1024**3, 60*1024**3, 40*1024**3)):
            with patch('pathlib.Path.exists', return_value=True):
                usage = get_disk_usage()
                # Should include at least root, home, and repo paths
                assert len(usage) >= 1


class TestNetworkInfo:
    """Test get_network_info function."""
    
    @patch('socket.getaddrinfo')
    @patch('socket.gethostname', return_value='test-host')
    @patch('socket.create_connection')
    @patch('socket.gethostbyname')
    def test_get_network_info_success(self, mock_gethostbyname, mock_create_connection, mock_gethostname, mock_getaddrinfo):
        """Test getting network info successfully."""
        # Mock IP address resolution
        mock_getaddrinfo.return_value = [
            (None, None, None, None, ('192.168.1.100', None)),
            (None, None, None, None, ('127.0.0.1', None)),
        ]
        
        info = get_network_info()
        
        assert "ip_addresses" in info
        assert "internet_connected" in info
        assert "dns_resolution" in info
        assert info["internet_connected"] is True
        assert info["dns_resolution"] is True
        assert "192.168.1.100" in info["ip_addresses"]
    
    @patch('socket.getaddrinfo', side_effect=Exception("Network error"))
    @patch('socket.create_connection', side_effect=Exception("No connection"))
    @patch('socket.gethostbyname', side_effect=Exception("DNS error"))
    def test_get_network_info_all_failures(self, *mocks):
        """Test network info when all operations fail."""
        info = get_network_info()
        
        assert info["ip_addresses"] == []
        assert info["internet_connected"] is False
        assert info["dns_resolution"] is False


class TestGitInfo:
    """Test get_git_info function."""
    
    @patch('pathlib.Path.exists', return_value=True)
    @patch('subprocess.run')
    def test_get_git_info_success(self, mock_run, mock_exists):
        """Test getting git info successfully."""
        # Mock git command responses
        mock_run.side_effect = [
            Mock(returncode=0, stdout="main\n"),  # branch
            Mock(returncode=0, stdout="abc1234 Initial commit\n"),  # log
            Mock(returncode=0, stdout=""),  # status
            Mock(returncode=0, stdout="https://github.com/user/repo.git\n"),  # remote
        ]
        
        with patch('src.common.paths.repo_root', return_value=Path("/test/repo")):
            info = get_git_info()
        
        assert info["branch"] == "main"
        assert info["last_commit_hash"] == "abc1234"
        assert info["last_commit_message"] == "Initial commit"
        assert info["uncommitted_changes"] is False
        assert info["remote_url"] == "https://github.com/user/repo.git"
    
    @patch('pathlib.Path.exists', return_value=False)
    def test_get_git_info_not_git_repo(self, mock_exists):
        """Test getting git info when not in git repo."""
        with patch('src.common.paths.repo_root', return_value=Path("/test/repo")):
            info = get_git_info()
        
        assert info["status"] == "Not a git repository"
    
    @patch('pathlib.Path.exists', return_value=True)
    @patch('subprocess.run', side_effect=Exception("Git error"))
    def test_get_git_info_git_error(self, mock_run, mock_exists):
        """Test getting git info when git commands fail."""
        with patch('src.common.paths.repo_root', return_value=Path("/test/repo")):
            info = get_git_info()
        
        assert "status" in info
        assert "Error accessing git information" in info["status"]


class TestCpuInfo:
    """Test get_cpu_info function."""
    
    @patch('os.cpu_count', return_value=8)
    @patch('os.getloadavg', return_value=(1.0, 1.5, 2.0))
    def test_get_cpu_info_with_loadavg(self, mock_loadavg, mock_cpu_count):
        """Test getting CPU info with load average."""
        info = get_cpu_info()
        
        assert info["logical_cores"] == 8
        assert info["load_average"] == [1.0, 1.5, 2.0]
    
    @patch('os.cpu_count', return_value=4)
    def test_get_cpu_info_no_loadavg(self, mock_cpu_count):
        """Test getting CPU info without load average support."""
        # Remove getloadavg if it exists
        original_getloadavg = getattr(os, 'getloadavg', None)
        if hasattr(os, 'getloadavg'):
            delattr(os, 'getloadavg')
        
        try:
            info = get_cpu_info()
            assert info["logical_cores"] == 4
            assert info["load_average"] == []
        finally:
            if original_getloadavg:
                setattr(os, 'getloadavg', original_getloadavg)
    
    def test_get_cpu_info_with_psutil(self):
        """Test getting CPU info with psutil available."""
        mock_freq = Mock()
        mock_freq._asdict.return_value = {"current": 2400, "min": 800, "max": 3200}
        
        # Mock the local psutil import within the function
        with patch('builtins.__import__') as mock_import:
            mock_psutil = Mock()
            mock_psutil.cpu_count.return_value = 4
            mock_psutil.cpu_freq.return_value = mock_freq
            mock_psutil.cpu_percent.return_value = 25.0
            
            def side_effect(name, *args):
                if name == 'psutil':
                    return mock_psutil
                return __import__(name, *args)
            
            mock_import.side_effect = side_effect
            
            info = get_cpu_info()
            
            assert "physical_cores" in info
            assert "cpu_freq" in info
            assert "cpu_percent" in info
            assert info["physical_cores"] == 4
            assert info["cpu_percent"] == 25.0


class TestRunCommandSafely:
    """Test run_command_safely function."""
    
    @patch('subprocess.run')
    def test_run_command_safely_success(self, mock_run):
        """Test running command successfully."""
        mock_run.return_value = Mock(returncode=0, stdout="success", stderr="")
        
        success, stdout, stderr = run_command_safely(["echo", "test"])
        
        assert success is True
        assert stdout == "success"
        assert stderr == ""
    
    @patch('subprocess.run')
    def test_run_command_safely_failure(self, mock_run):
        """Test running command that fails."""
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="error")
        
        success, stdout, stderr = run_command_safely(["false"])
        
        assert success is False
        assert stdout == ""
        assert stderr == "error"
    
    @patch('subprocess.run', side_effect=subprocess.TimeoutExpired("cmd", 5))
    def test_run_command_safely_timeout(self, mock_run):
        """Test running command that times out."""
        success, stdout, stderr = run_command_safely(["sleep", "10"], timeout=1)
        
        assert success is False
        assert stdout == ""
        assert stderr == "Command timed out"
    
    @patch('subprocess.run', side_effect=Exception("Command error"))
    def test_run_command_safely_exception(self, mock_run):
        """Test running command that raises exception."""
        success, stdout, stderr = run_command_safely(["invalid-command"])
        
        assert success is False
        assert stdout == ""
        assert "Command error" in stderr


class TestGenerateSystemReport:
    """Test generate_system_report function."""
    
    @patch('src.system.reporting.get_basic_system_info')
    @patch('src.system.reporting.get_python_environment_info')
    @patch('src.system.reporting.get_memory_info')
    @patch('src.system.reporting.get_disk_usage')
    @patch('src.system.reporting.get_network_info')
    @patch('src.system.reporting.get_git_info')
    @patch('src.system.reporting.get_cpu_info')
    @patch('src.common.paths.repo_root', return_value=Path("/test/repo"))
    def test_generate_system_report(self, mock_repo_root, *mocks):
        """Test generating complete system report."""
        # Mock all the info gathering functions
        mock_basic, mock_python, mock_memory, mock_disk, mock_network, mock_git, mock_cpu = mocks
        
        mock_basic.return_value = {
            "hostname": "test-host",
            "os_name": "Linux",
            "os_version": "5.4.0",
            "architecture": "x86_64"
        }
        mock_python.return_value = {
            "python_version": "3.9.0",
            "python_executable": "/usr/bin/python3",
            "virtual_env": "None"
        }
        mock_memory.return_value = {"total_gb": 16.0}
        mock_disk.return_value = {}
        mock_network.return_value = {"ip_addresses": ["127.0.0.1"], "internet_connected": True}
        mock_git.return_value = {"branch": "main"}
        mock_cpu.return_value = {"logical_cores": 8}
        
        report = generate_system_report()
        
        assert isinstance(report, SystemInfo)
        assert report.hostname == "test-host"
        assert report.os_name == "Linux"
        assert report.python_version == "3.9.0"
        assert report.cpu_count == 8
        assert report.memory_total_gb == 16.0
        assert report.internet_connected is True
        assert report.project_root == "/test/repo"


class TestFormatSystemReport:
    """Test format_system_report function."""
    
    def test_format_system_report_basic(self):
        """Test formatting system report."""
        info = SystemInfo(
            hostname="test-host",
            os_name="Linux",
            os_version="5.4.0",
            architecture="x86_64",
            cpu_count=4,
            memory_total_gb=16.0,
            python_version="3.9.0",
            python_executable="/usr/bin/python3",
            virtual_env="None",
            ip_addresses=["127.0.0.1"],
            internet_connected=True,
            project_root="/test/repo",
            git_info={"branch": "main"},
            report_time="2023-01-01T12:00:00",
        )
        
        report = format_system_report(info)
        
        assert "SYSTEM REPORT" in report
        assert "test-host" in report
        assert "Linux" in report
        assert "3.9.0" in report
        assert "127.0.0.1" in report
        assert "/test/repo" in report
        assert "main" in report
    
    def test_format_system_report_detailed(self):
        """Test formatting detailed system report."""
        info = SystemInfo(
            disk_usage={
                "/": {"total_gb": 100.0, "used_gb": 60.0, "free_gb": 40.0, "percent_used": 60.0}
            }
        )
        
        report = format_system_report(info, detailed=True)
        
        assert "DISK USAGE" in report
        assert "100.00 GB" in report
        assert "60.0%" in report


class TestResourceUsageFunctions:
    """Test resource usage functions."""
    
    def test_get_resource_usage_with_psutil(self):
        """Test getting resource usage with psutil."""
        mock_memory = Mock()
        mock_memory.percent = 75.0
        mock_memory.available = 4 * 1024**3  # 4GB
        
        # Mock the local psutil import within the function
        with patch('builtins.__import__') as mock_import:
            mock_psutil = Mock()
            mock_psutil.cpu_percent.return_value = 50.0
            mock_psutil.virtual_memory.return_value = mock_memory
            
            def side_effect(name, *args):
                if name == 'psutil':
                    return mock_psutil
                return __import__(name, *args)
            
            mock_import.side_effect = side_effect
            
            usage = get_resource_usage()
            
            assert usage.cpu_percent == 50.0
            assert usage.memory_percent == 75.0
            assert usage.memory_available_gb == 4.0
    
    def test_get_resource_usage_without_psutil(self):
        """Test getting resource usage without psutil."""
        with patch.dict('sys.modules', {'psutil': None}):
            with patch('importlib.import_module', side_effect=ImportError()):
                usage = get_resource_usage()
                
                assert usage.cpu_percent == 0.0
                assert usage.memory_percent == 0.0
                assert usage.memory_available_gb == 0.0


class TestSystemRequirements:
    """Test check_system_requirements function."""
    
    @patch('sys.version_info', (3, 9, 0))
    @patch('src.system.reporting.get_memory_info', return_value={"total_gb": 8.0})
    @patch('src.system.reporting.get_disk_usage')
    @patch('src.system.reporting.get_network_info', return_value={"internet_connected": True})
    def test_check_system_requirements_all_met(self, mock_network, mock_disk, mock_memory):
        """Test system requirements check when all requirements met."""
        mock_disk.return_value = {"/test": {"free_gb": 5.0}}
        
        checks = check_system_requirements()
        
        assert checks["python_3_8_plus"] is True
        assert checks["sufficient_memory"] is True
        assert checks["sufficient_disk_space"] is True
        assert checks["internet_connected"] is True
    
    @patch('sys.version_info', (3, 7, 0))
    @patch('src.system.reporting.get_memory_info', return_value={"total_gb": 1.0})
    @patch('src.system.reporting.get_disk_usage')
    @patch('src.system.reporting.get_network_info', return_value={"internet_connected": False})
    def test_check_system_requirements_some_failed(self, mock_network, mock_disk, mock_memory):
        """Test system requirements check when some requirements fail."""
        mock_disk.return_value = {"/test": {"free_gb": 0.5}}
        
        checks = check_system_requirements()
        
        assert checks["python_3_8_plus"] is False
        assert checks["sufficient_memory"] is False
        assert checks["sufficient_disk_space"] is False
        assert checks["internet_connected"] is False


@pytest.mark.integration
class TestSystemReportingIntegration:
    """Integration tests for system reporting."""
    
    def test_complete_system_report_generation(self):
        """Test generating a complete system report."""
        # This test uses real system information
        report = generate_system_report()
        
        assert isinstance(report, SystemInfo)
        assert report.hostname != ""
        assert report.os_name != ""
        assert report.python_version != ""
        assert report.cpu_count > 0
        assert report.project_root != ""
        assert report.report_time != ""
        
        # Test formatting
        formatted = format_system_report(report)
        assert len(formatted) > 100
        assert "SYSTEM REPORT" in formatted
    
    def test_system_requirements_real_check(self):
        """Test system requirements with real system."""
        checks = check_system_requirements()
        
        assert isinstance(checks, dict)
        assert "python_3_8_plus" in checks
        assert "sufficient_memory" in checks
        assert "sufficient_disk_space" in checks
        assert "internet_connected" in checks
        
        # Python version should be >= 3.8 for this test to run
        assert checks["python_3_8_plus"] is True
