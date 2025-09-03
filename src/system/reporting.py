"""System information reporting and diagnostics.

This module provides comprehensive system reporting including:
- Hardware specifications
- Operating system information
- Python environment details
- Disk usage and memory statistics
- Network connectivity checks
"""

from __future__ import annotations

import os
import platform
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.common.paths import repo_root


@dataclass
class SystemInfo:
    """System information container."""
    
    # Basic system info
    hostname: str = ""
    os_name: str = ""
    os_version: str = ""
    architecture: str = ""
    
    # Hardware info
    cpu_count: int = 0
    memory_total_gb: float = 0.0
    disk_usage: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Python environment
    python_version: str = ""
    python_executable: str = ""
    virtual_env: Optional[str] = None
    
    # Network info
    ip_addresses: List[str] = field(default_factory=list)
    internet_connected: bool = False
    
    # Project info
    project_root: str = ""
    git_info: Dict[str, str] = field(default_factory=dict)
    
    # Timestamp
    report_time: str = ""


@dataclass
class ResourceUsage:
    """Current resource usage statistics."""
    
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_available_gb: float = 0.0
    load_average: List[float] = field(default_factory=list)


def get_basic_system_info() -> Dict[str, str]:
    """Get basic system information.
    
    Returns:
        Dictionary containing basic system information
    """
    return {
        "hostname": socket.gethostname(),
        "os_name": platform.system(),
        "os_version": platform.release(),
        "os_details": platform.platform(),
        "architecture": platform.machine(),
        "processor": platform.processor() or "Unknown",
    }


def get_python_environment_info() -> Dict[str, str]:
    """Get Python environment information.
    
    Returns:
        Dictionary containing Python environment details
    """
    # Check for virtual environment
    venv = None
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        venv = sys.prefix
    
    # Check for conda environment
    conda_env = os.environ.get('CONDA_DEFAULT_ENV')
    if conda_env:
        venv = conda_env
    
    return {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "python_executable": sys.executable,
        "virtual_env": venv or "None",
        "sys_path_entries": str(len(sys.path)),
    }


def get_memory_info() -> Dict[str, float]:
    """Get memory information.
    
    Returns:
        Dictionary containing memory statistics in GB
    """
    try:
        # Try using psutil if available
        import psutil
        
        memory = psutil.virtual_memory()
        return {
            "total_gb": memory.total / (1024**3),
            "available_gb": memory.available / (1024**3),
            "used_gb": memory.used / (1024**3),
            "percent_used": memory.percent,
        }
    except ImportError:
        # Fallback to system commands
        try:
            if platform.system() == "Linux":
                # Parse /proc/meminfo
                with open("/proc/meminfo", "r") as f:
                    meminfo = f.read()
                
                total_kb = int([line for line in meminfo.split("\n") if "MemTotal" in line][0].split()[1])
                available_kb = int([line for line in meminfo.split("\n") if "MemAvailable" in line][0].split()[1])
                
                total_gb = total_kb / (1024**2)
                available_gb = available_kb / (1024**2)
                used_gb = total_gb - available_gb
                
                return {
                    "total_gb": total_gb,
                    "available_gb": available_gb,
                    "used_gb": used_gb,
                    "percent_used": (used_gb / total_gb) * 100,
                }
        except Exception:
            pass
        
        # Ultimate fallback
        return {
            "total_gb": 0.0,
            "available_gb": 0.0,
            "used_gb": 0.0,
            "percent_used": 0.0,
        }


def get_disk_usage(paths: List[str] = None) -> Dict[str, Dict[str, float]]:
    """Get disk usage information for specified paths.
    
    Args:
        paths: List of paths to check (defaults to common system paths)
        
    Returns:
        Dictionary mapping path to usage statistics in GB
    """
    if paths is None:
        paths = ["/", str(Path.home()), str(repo_root())]
    
    usage = {}
    
    for path in paths:
        try:
            path_obj = Path(path)
            if path_obj.exists():
                total, used, free = shutil.disk_usage(path)
                
                usage[str(path_obj)] = {
                    "total_gb": total / (1024**3),
                    "used_gb": used / (1024**3),
                    "free_gb": free / (1024**3),
                    "percent_used": (used / total) * 100,
                }
        except Exception:
            continue
    
    return usage


def get_network_info() -> Dict[str, any]:
    """Get network connectivity information.
    
    Returns:
        Dictionary containing network information
    """
    info = {
        "ip_addresses": [],
        "internet_connected": False,
        "dns_resolution": False,
    }
    
    # Get local IP addresses
    try:
        hostname = socket.gethostname()
        ip_addresses = socket.getaddrinfo(hostname, None, socket.AF_INET)
        info["ip_addresses"] = list(set(ip[4][0] for ip in ip_addresses))
    except Exception:
        pass
    
    # Test internet connectivity
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        info["internet_connected"] = True
    except Exception:
        pass
    
    # Test DNS resolution
    try:
        socket.gethostbyname("google.com")
        info["dns_resolution"] = True
    except Exception:
        pass
    
    return info


def get_git_info() -> Dict[str, str]:
    """Get Git repository information.
    
    Returns:
        Dictionary containing Git information
    """
    info = {}
    
    try:
        root = repo_root()
        
        # Check if it's a git repository
        git_dir = root / ".git"
        if not git_dir.exists():
            return {"status": "Not a git repository"}
        
        # Get current branch
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                info["branch"] = result.stdout.strip()
        except Exception:
            pass
        
        # Get last commit
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%H %s"],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                commit_line = result.stdout.strip()
                if commit_line:
                    commit_hash, commit_msg = commit_line.split(" ", 1)
                    info["last_commit_hash"] = commit_hash[:8]
                    info["last_commit_message"] = commit_msg
        except Exception:
            pass
        
        # Check for uncommitted changes
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                info["uncommitted_changes"] = bool(result.stdout.strip())
            
        except Exception:
            pass
        
        # Get remote URL
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                info["remote_url"] = result.stdout.strip()
        except Exception:
            pass
            
    except Exception:
        info = {"status": "Error accessing git information"}
    
    return info


def get_cpu_info() -> Dict[str, any]:
    """Get CPU information.
    
    Returns:
        Dictionary containing CPU details
    """
    info = {
        "logical_cores": os.cpu_count(),
        "load_average": [],
    }
    
    try:
        # Get load average on Unix systems
        if hasattr(os, 'getloadavg'):
            info["load_average"] = list(os.getloadavg())
    except Exception:
        pass
    
    try:
        # Try to get more detailed CPU info
        import psutil
        info["physical_cores"] = psutil.cpu_count(logical=False)
        info["cpu_freq"] = psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        info["cpu_percent"] = psutil.cpu_percent(interval=1)
    except ImportError:
        pass
    
    return info


def run_command_safely(cmd: List[str], timeout: int = 10) -> Tuple[bool, str, str]:
    """Run a command safely with timeout.
    
    Args:
        cmd: Command to run as list
        timeout: Timeout in seconds
        
    Returns:
        Tuple of (success, stdout, stderr)
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)


def generate_system_report() -> SystemInfo:
    """Generate comprehensive system report.
    
    Returns:
        SystemInfo object containing all system information
    """
    # Gather all information
    basic_info = get_basic_system_info()
    python_info = get_python_environment_info()
    memory_info = get_memory_info()
    disk_info = get_disk_usage()
    network_info = get_network_info()
    git_info = get_git_info()
    cpu_info = get_cpu_info()
    
    # Create SystemInfo object
    system_info = SystemInfo(
        hostname=basic_info["hostname"],
        os_name=basic_info["os_name"],
        os_version=basic_info["os_version"],
        architecture=basic_info["architecture"],
        
        cpu_count=cpu_info["logical_cores"],
        memory_total_gb=memory_info["total_gb"],
        disk_usage=disk_info,
        
        python_version=python_info["python_version"],
        python_executable=python_info["python_executable"],
        virtual_env=python_info["virtual_env"],
        
        ip_addresses=network_info["ip_addresses"],
        internet_connected=network_info["internet_connected"],
        
        project_root=str(repo_root()),
        git_info=git_info,
        
        report_time=datetime.now().isoformat(),
    )
    
    return system_info


def format_system_report(system_info: SystemInfo, detailed: bool = True) -> str:
    """Format system information as a readable report.
    
    Args:
        system_info: System information object
        detailed: Whether to include detailed information
        
    Returns:
        Formatted report string
    """
    lines = []
    
    # Header
    lines.append("=" * 60)
    lines.append(f"SYSTEM REPORT - {system_info.report_time[:19]}")
    lines.append("=" * 60)
    
    # Basic System Information
    lines.append("\n🖥️  SYSTEM INFORMATION")
    lines.append(f"Hostname: {system_info.hostname}")
    lines.append(f"OS: {system_info.os_name} {system_info.os_version}")
    lines.append(f"Architecture: {system_info.architecture}")
    lines.append(f"CPU Cores: {system_info.cpu_count}")
    lines.append(f"Memory: {system_info.memory_total_gb:.2f} GB")
    
    # Python Environment
    lines.append("\n🐍 PYTHON ENVIRONMENT")
    lines.append(f"Python Version: {system_info.python_version}")
    lines.append(f"Python Executable: {system_info.python_executable}")
    lines.append(f"Virtual Environment: {system_info.virtual_env}")
    
    # Project Information
    lines.append("\n📁 PROJECT INFORMATION")
    lines.append(f"Project Root: {system_info.project_root}")
    
    if system_info.git_info:
        lines.append("\n🔧 GIT INFORMATION")
        for key, value in system_info.git_info.items():
            lines.append(f"{key.replace('_', ' ').title()}: {value}")
    
    # Network Information
    lines.append("\n🌐 NETWORK INFORMATION")
    lines.append(f"IP Addresses: {', '.join(system_info.ip_addresses) or 'None found'}")
    lines.append(f"Internet Connected: {'Yes' if system_info.internet_connected else 'No'}")
    
    # Disk Usage (if detailed)
    if detailed and system_info.disk_usage:
        lines.append("\n💾 DISK USAGE")
        for path, usage in system_info.disk_usage.items():
            lines.append(f"{path}:")
            lines.append(f"  Total: {usage['total_gb']:.2f} GB")
            lines.append(f"  Used: {usage['used_gb']:.2f} GB ({usage['percent_used']:.1f}%)")
            lines.append(f"  Free: {usage['free_gb']:.2f} GB")
    
    lines.append("\n" + "=" * 60)
    
    return "\n".join(lines)


def get_resource_usage() -> ResourceUsage:
    """Get current resource usage statistics.
    
    Returns:
        ResourceUsage object with current statistics
    """
    usage = ResourceUsage()
    
    try:
        import psutil
        
        # CPU usage
        usage.cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        usage.memory_percent = memory.percent
        usage.memory_available_gb = memory.available / (1024**3)
        
    except ImportError:
        # Fallback methods
        try:
            if hasattr(os, 'getloadavg'):
                usage.load_average = list(os.getloadavg())
        except Exception:
            pass
    
    return usage


def check_system_requirements() -> Dict[str, bool]:
    """Check if system meets minimum requirements.
    
    Returns:
        Dictionary of requirement checks
    """
    checks = {}
    
    # Python version check
    version = sys.version_info
    checks["python_3_8_plus"] = version >= (3, 8)
    
    # Memory check (minimum 2GB)
    memory_info = get_memory_info()
    checks["sufficient_memory"] = memory_info["total_gb"] >= 2.0
    
    # Disk space check (minimum 1GB free)
    disk_info = get_disk_usage([str(repo_root())])
    project_disk = list(disk_info.values())[0] if disk_info else {"free_gb": 0}
    checks["sufficient_disk_space"] = project_disk["free_gb"] >= 1.0
    
    # Internet connectivity
    network_info = get_network_info()
    checks["internet_connected"] = network_info["internet_connected"]
    
    return checks
