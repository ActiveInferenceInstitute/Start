# Repository Management

Repository cloning and management utilities for external repositories.

## Overview

This module provides functionality to clone, update, and manage external repositories, particularly those from the Active Inference Institute ecosystem and related research repositories.

## Modules

### `manager.py`
High-level repository management interface:
- `RepositoryManager`: Main management class
- `create_repository_manager()`: Factory function
- `format_repository_summary()`: Format repository summaries
- `format_clone_results()`: Format cloning results
- `format_repository_status()`: Format repository status

### `cloning.py`
Repository cloning operations:
- `RepoInfo`: Repository information dataclass
- `CloneResult`: Cloning operation result dataclass
- `get_predefined_repositories()`: Get list of predefined repositories
- `clone_repository()`: Clone a single repository
- `clone_multiple_repositories()`: Clone multiple repositories
- `clone_all_repositories()`: Clone all predefined repositories
- `get_cloned_repositories()`: List already cloned repositories
- `update_repository()`: Update an existing repository
- `get_repository_status()`: Get repository status information
- `cleanup_failed_clones()`: Clean up failed clone attempts
- `validate_repository_url()`: Validate repository URL format

### `clone_repo.py`
Low-level git cloning utilities:
- `clone_repository()`: Direct git clone operation
- `parse_args()`: Parse command-line arguments
- `main()`: Command-line entry point

## Predefined Repositories

The module includes predefined repositories from:
- **Active Inference Institute**: cognitive, gnn, cerebrum
- **Active Inference Libraries**: rxinfer, activeinference, pymdp
- **Formal Methods**: lean_niche
- **Infrastructure**: template, axiom

## Usage Examples

```python
from src.repos.manager import create_repository_manager
from src.repos.cloning import clone_repository, get_predefined_repositories

# Create manager
manager = create_repository_manager()

# List available repositories
available = manager.list_available_repositories()

# Clone a single repository
result = manager.clone_repository("pymdp", force=False)

# Clone multiple repositories
results = manager.clone_repositories(["pymdp", "rxinfer"])

# Clone all repositories in a category
results = manager.clone_all(category="active_inference")

# Update a repository
success, message = manager.update_repository("pymdp")

# Get repository status
status = manager.get_repository_status("pymdp")

# Direct cloning (low-level)
from src.repos.clone_repo import clone_repository
destination = clone_repository(
    url="https://github.com/user/repo",
    destination=Path("clones/repo"),
    branch="main",
    shallow=True
)
```

## Repository Categories

- `active_inference`: Core Active Inference repositories
- `formal_methods`: Formal verification and theorem proving
- `infrastructure`: Infrastructure and tooling

## Navigation

- [AGENTS.md](AGENTS.md) - Complete function reference
- [../README.md](../README.md) - Source code overview
- [../../docs/clones.md](../../docs/clones.md) - Clone management documentation
