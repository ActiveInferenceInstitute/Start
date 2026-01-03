# System Utilities Technical Reference

## Overview

Technical documentation for system utilities, diagnostics, and environment management.

## Module: `reporting.py`

### Classes

#### `SystemInfo`
System information container.

**Attributes**:
- `hostname: str`: System hostname
- `os_name: str`: Operating system name
- `os_version: str`: OS version
- `architecture: str`: System architecture
- `cpu_count: int`: Number of CPU cores
- `memory_total_gb: float`: Total memory in GB
- `disk_usage: Dict[str, Dict[str, float]]`: Disk usage information
- `python_version: str`: Python version
- `python_executable: str`: Python executable path
- `virtual_env: Optional[str]`: Virtual environment path
- `ip_addresses: List[str]`: Network IP addresses
- `internet_connected: bool`: Internet connectivity status
- `project_root: str`: Project root directory
- `git_info: Dict[str, str]`: Git repository information
- `report_time: str`: Report timestamp

#### `ResourceUsage`
Current resource usage statistics.

**Attributes**:
- `cpu_percent: float`: CPU usage percentage
- `memory_percent: float`: Memory usage percentage
- `memory_used_gb: float`: Memory used in GB
- `memory_available_gb: float`: Memory available in GB
- `disk_usage_percent: Dict[str, float]`: Disk usage by mount point

### Functions

#### `generate_system_report() -> SystemInfo`
Generates comprehensive system report.

**Returns**: SystemInfo object containing all system information

#### `format_system_report(system_info: SystemInfo, detailed: bool = True) -> str`
Formats system report for display.

**Parameters**:
- `system_info`: SystemInfo object
- `detailed`: Whether to include detailed information (default: True)

**Returns**: Formatted report string

#### `get_resource_usage() -> ResourceUsage`
Gets current resource usage statistics.

**Returns**: ResourceUsage object

#### `check_system_requirements() -> Dict[str, bool]`
Checks system requirements.

**Returns**: Dictionary mapping requirement names to availability status

## Module: `dependencies.py`

### Classes

#### `DependencyCheck`
Represents the result of a dependency check.

**Attributes**:
- `name: str`: Dependency name
- `required: bool`: Whether dependency is required
- `available: bool`: Whether dependency is available
- `version: Optional[str]`: Dependency version
- `error_message: Optional[str]`: Error message if unavailable
- `install_hint: Optional[str]`: Installation hint

#### `DependencyReport`
Complete dependency check report.

**Attributes**:
- `checks: List[DependencyCheck]`: List of dependency checks
- `all_required_available: bool`: Whether all required dependencies are available
- `missing_required: List[str]`: List of missing required dependencies
- `missing_optional: List[str]`: List of missing optional dependencies

### Functions

#### `run_comprehensive_dependency_check() -> DependencyReport`
Runs comprehensive dependency check.

**Returns**: DependencyReport with all check results

#### `format_dependency_report(report: DependencyReport, show_optional: bool = True) -> str`
Formats dependency report for display.

**Parameters**:
- `report`: DependencyReport object
- `show_optional`: Whether to show optional dependencies (default: True)

**Returns**: Formatted report string

#### `validate_api_keys() -> Dict[str, bool]`
Validates API keys in environment.

**Returns**: Dictionary mapping API key names to validation status

## Module: `environment.py`

### Functions

#### `setup_project_environment() -> Tuple[bool, List[str]]`
Sets up complete project environment.

**Returns**: Tuple of (success, list of messages)

**Behavior**: Creates config files, validates setup, provides feedback

#### `validate_environment() -> Tuple[bool, List[str]]`
Validates environment configuration.

**Returns**: Tuple of (is_valid, list of messages)

#### `get_environment_info() -> Dict[str, any]`
Gets environment information.

**Returns**: Dictionary with environment details

#### `fix_common_issues() -> List[str]`
Fixes common environment issues.

**Returns**: List of fix messages

#### `run_health_check() -> Tuple[bool, Dict[str, any]]`
Runs comprehensive health check.

**Returns**: Tuple of (is_healthy, health check results)

## Cross-References

- [README.md](README.md) - Module overview and usage
- [../README.md](../README.md) - Source code overview
- [../../docs/environment.md](../../docs/environment.md) - Environment setup guide
