# System Utilities

System utilities for reporting, diagnostics, dependency checking, and environment management.

## Overview

This module provides comprehensive system information gathering, dependency validation, and environment setup utilities.

## Modules

### `reporting.py`
System information and diagnostics:
- `SystemInfo`: System information dataclass
- `ResourceUsage`: Resource usage statistics dataclass
- `generate_system_report()`: Generate comprehensive system report
- `format_system_report()`: Format system report for display
- `get_resource_usage()`: Get current resource usage
- `check_system_requirements()`: Check system requirements

### `dependencies.py`
Dependency checking and validation:
- `DependencyCheck`: Dependency check result dataclass
- `DependencyReport`: Complete dependency report dataclass
- `check_python_package()`: Check if Python package is available
- `check_system_tool()`: Check if system tool is available
- `run_comprehensive_dependency_check()`: Run full dependency check
- `format_dependency_report()`: Format dependency report
- `validate_api_keys()`: Validate API keys

### `environment.py`
Environment setup and validation:
- `setup_project_environment()`: Set up complete project environment
- `validate_environment()`: Validate environment configuration
- `get_environment_info()`: Get environment information
- `fix_common_issues()`: Fix common environment issues
- `run_health_check()`: Run comprehensive health check

## Usage Examples

```python
from src.system.reporting import generate_system_report, format_system_report
from src.system.dependencies import run_comprehensive_dependency_check
from src.system.environment import setup_project_environment, validate_environment

# Generate system report
system_info = generate_system_report()
print(format_system_report(system_info, detailed=True))

# Check dependencies
dep_report = run_comprehensive_dependency_check()
print(format_dependency_report(dep_report))

# Setup environment
success, messages = setup_project_environment()
for message in messages:
    print(message)

# Validate environment
is_valid, messages = validate_environment()
```

## Navigation

- [AGENTS.md](AGENTS.md) - Complete function reference
- [../README.md](../README.md) - Source code overview
- [../../docs/environment.md](../../docs/environment.md) - Environment setup guide
