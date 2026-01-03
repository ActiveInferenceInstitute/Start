# Repository Management Technical Reference

## Overview

Technical documentation for repository cloning and management functions.

## Module: `manager.py`

### Classes

#### `RepositoryManager`
High-level repository management interface.

**Attributes**:
- `base_dir: Union[Path, str]`: Base directory for cloned repositories (default: "src/_clones")

**Methods**:
- `list_available_repositories() -> Dict[str, Dict[str, any]]`: Get all available repositories
- `list_cloned_repositories() -> Dict[str, Dict[str, any]]`: Get cloned repositories with status
- `get_repository_categories() -> Dict[str, List[str]]`: Get repositories by category
- `clone_repository(repo_name: str, force: bool = False, progress_callback: Optional[callable] = None) -> CloneResult`: Clone single repository
- `clone_repositories(repo_names: List[str], force: bool = False, progress_callback: Optional[callable] = None) -> List[CloneResult]`: Clone multiple repositories
- `clone_all(category: Optional[str] = None, force: bool = False, progress_callback: Optional[callable] = None) -> List[CloneResult]`: Clone all repositories
- `update_repository(repo_name: str) -> Tuple[bool, str]`: Update single repository
- `update_all_repositories() -> List[Tuple[str, bool, str]]`: Update all cloned repositories
- `get_repository_status(repo_name: str) -> Optional[Dict[str, any]]`: Get repository status
- `get_summary() -> Dict[str, any]`: Get summary of all repositories

### Functions

#### `create_repository_manager(base_dir: Optional[Path] = None) -> RepositoryManager`
Creates a RepositoryManager instance.

**Parameters**:
- `base_dir`: Optional base directory (default: "src/_clones")

**Returns**: RepositoryManager instance

#### `format_repository_summary(summary: Dict[str, any]) -> str`
Formats repository summary for display.

**Parameters**:
- `summary`: Summary dictionary

**Returns**: Formatted string

#### `format_clone_results(results: List[CloneResult]) -> str`
Formats cloning results for display.

**Parameters**:
- `results`: List of CloneResult objects

**Returns**: Formatted string

#### `format_repository_status(status_dict: Dict[str, Dict[str, any]]) -> str`
Formats repository status information for display.

**Parameters**:
- `status_dict`: Dictionary mapping repo names to status

**Returns**: Formatted string

## Module: `cloning.py`

### Classes

#### `RepoInfo`
Information about a repository to clone.

**Attributes**:
- `name: str`: Repository name
- `url: str`: Repository URL
- `branch: Optional[str]`: Branch to clone (default: None)
- `description: str`: Repository description (default: "")
- `category: str`: Repository category (default: "general")
- `shallow: bool`: Whether to perform shallow clone (default: True)
- `destination: Optional[str]`: Custom destination path (default: None)

#### `CloneResult`
Result of a repository cloning operation.

**Attributes**:
- `repo_name: str`: Repository name
- `success: bool`: Whether cloning succeeded
- `destination: Optional[Path]`: Path to cloned repository
- `error_message: Optional[str]`: Error message if failed
- `clone_time: float`: Time taken to clone in seconds (default: 0.0)
- `size_mb: float`: Size of cloned repository in MB (default: 0.0)

### Functions

#### `get_predefined_repositories() -> Dict[str, RepoInfo]`
Gets predefined repository configurations.

**Returns**: Dictionary mapping repo names to RepoInfo objects

**Repositories**: Includes cognitive, gnn, cerebrum, rxinfer, activeinference, pymdp, lean_niche, template, axiom

#### `get_clone_destination(repo_name: str, base_dir: Optional[Path] = None) -> Path`
Gets the destination path for cloning a repository.

**Parameters**:
- `repo_name`: Name of the repository
- `base_dir`: Base directory for clones (default: src/_clones)

**Returns**: Path where repository should be cloned

#### `estimate_clone_time(repo_url: str) -> str`
Estimates clone time based on repository characteristics.

**Parameters**:
- `repo_url`: Repository URL

**Returns**: Estimated time range as string

#### `clone_repository(repo_name: str, base_dir: Optional[Path] = None, force: bool = False, progress_callback: Optional[callable] = None) -> CloneResult`
Clones a single repository.

**Parameters**:
- `repo_name`: Name of repository to clone
- `base_dir`: Base directory for clones (default: src/_clones)
- `force`: Whether to overwrite existing directory (default: False)
- `progress_callback`: Optional progress callback function

**Returns**: CloneResult with operation details

**Raises**: Various exceptions if cloning fails

#### `clone_multiple_repositories(repo_names: List[str], base_dir: Optional[Path] = None, force: bool = False, progress_callback: Optional[callable] = None) -> List[CloneResult]`
Clones multiple repositories.

**Parameters**:
- `repo_names`: List of repository names
- `base_dir`: Base directory for clones (default: src/_clones)
- `force`: Whether to overwrite existing directories (default: False)
- `progress_callback`: Optional progress callback function

**Returns**: List of CloneResult objects

#### `clone_all_repositories(category: Optional[str] = None, base_dir: Optional[Path] = None, force: bool = False, progress_callback: Optional[callable] = None) -> List[CloneResult]`
Clones all predefined repositories or all in a category.

**Parameters**:
- `category`: Optional category filter
- `base_dir`: Base directory for clones (default: src/_clones)
- `force`: Whether to overwrite existing directories (default: False)
- `progress_callback`: Optional progress callback function

**Returns**: List of CloneResult objects

#### `get_cloned_repositories(base_dir: Optional[Path] = None) -> List[Tuple[str, Path]]`
Gets list of already cloned repositories.

**Parameters**:
- `base_dir`: Base directory for clones (default: src/_clones)

**Returns**: List of (repo_name, path) tuples

#### `update_repository(repo_path: Path) -> Tuple[bool, str]`
Updates an existing repository by pulling latest changes.

**Parameters**:
- `repo_path`: Path to repository directory

**Returns**: Tuple of (success, message)

**Behavior**: Performs `git pull` operation

#### `get_repository_status(repo_path: Path) -> Dict[str, any]`
Gets status information for a repository.

**Parameters**:
- `repo_path`: Path to repository directory

**Returns**: Dictionary with status information:
  - `name`: Repository name
  - `path`: Repository path
  - `exists`: Whether repository exists
  - `is_git_repo`: Whether it's a valid git repository
  - `current_branch`: Current branch name
  - `last_commit`: Last commit hash
  - `last_commit_date`: Last commit date
  - `remote_url`: Remote repository URL
  - `size_mb`: Repository size in MB

#### `cleanup_failed_clones(base_dir: Optional[Path] = None) -> List[str]`
Cleans up failed clone attempts.

**Parameters**:
- `base_dir`: Base directory for clones (default: src/_clones)

**Returns**: List of cleaned up directory names

**Behavior**: Removes directories that appear to be failed clones

#### `validate_repository_url(url: str) -> bool`
Validates repository URL format.

**Parameters**:
- `url`: Repository URL to validate

**Returns**: True if URL appears valid

## Module: `clone_repo.py`

### Functions

#### `clone_repository(url: str, destination: Path, branch: Optional[str] = None, shallow: bool = False) -> Path`
Performs direct git clone operation.

**Parameters**:
- `url`: Repository URL
- `destination`: Destination path
- `branch`: Optional branch to clone
- `shallow`: Whether to perform shallow clone (default: False)

**Returns**: Path to cloned repository

**Raises**: `FileExistsError` if destination exists and is not empty

**Behavior**: Uses GitPython library for cloning

#### `parse_args(argv: list[str]) -> argparse.Namespace`
Parses command-line arguments.

**Parameters**:
- `argv`: Command-line arguments

**Returns**: Parsed arguments namespace

#### `main(argv: list[str]) -> int`
Command-line entry point.

**Parameters**:
- `argv`: Command-line arguments

**Returns**: Exit code (0 for success)

## Cross-References

- [README.md](README.md) - Module overview and usage examples
- [../README.md](../README.md) - Source code overview
- [../../docs/clones.md](../../docs/clones.md) - Clone management documentation
