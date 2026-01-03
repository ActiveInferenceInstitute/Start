# Common Utilities Technical Reference

## Overview

Technical documentation for shared utility functions in `src/common/`.

## Module: `io.py`

### Functions

#### `ensure_parent_dir(file_path: Path) -> None`
Ensures parent directory exists for a file path.

**Parameters**:
- `file_path`: Path to file whose parent directory should be created

**Raises**: None (creates directories silently)

#### `read_text(file_path: os.PathLike | str) -> str`
Reads text file with UTF-8 encoding.

**Parameters**:
- `file_path`: Path to text file

**Returns**: File contents as string

**Raises**: `FileNotFoundError` if file doesn't exist

#### `write_text(file_path: os.PathLike | str, content: str) -> Path`
Writes text to file, creating parent directories if needed.

**Parameters**:
- `file_path`: Path to output file
- `content`: Content to write

**Returns**: Resolved path to written file

#### `read_json(file_path: os.PathLike | str) -> Any`
Reads JSON file and parses contents.

**Parameters**:
- `file_path`: Path to JSON file

**Returns**: Parsed JSON data (dict, list, etc.)

**Raises**: `FileNotFoundError`, `json.JSONDecodeError`

#### `write_json(file_path: os.PathLike | str, data: Any, indent: int = 2) -> Path`
Writes data to JSON file with formatting.

**Parameters**:
- `file_path`: Path to output file
- `data`: Data to serialize (must be JSON-serializable)
- `indent`: Indentation level (default: 2)

**Returns**: Resolved path to written file

#### `list_files(directory: os.PathLike | str, patterns: Optional[Iterable[str]] = None) -> list[Path]`
Lists files in directory, optionally matching patterns.

**Parameters**:
- `directory`: Directory to search
- `patterns`: Optional glob patterns to match

**Returns**: Sorted list of file paths

#### `load_key_from_file(key_file_path: os.PathLike | str, key_name: str) -> str`
Loads key-value pair from configuration file.

**Parameters**:
- `key_file_path`: Path to key file (format: `key=value`)
- `key_name`: Name of key to retrieve

**Returns**: Value associated with key

**Raises**: `FileNotFoundError`, `ValueError` if key not found

#### `list_domain_markdown_files(domain_dir: os.PathLike | str, exclude_stems: Optional[Iterable[str]] = None) -> list[Path]`
Lists markdown files in domain directory, excluding specified stems.

**Parameters**:
- `domain_dir`: Directory containing domain files
- `exclude_stems`: Optional list of file stems to exclude

**Returns**: Sorted list of markdown file paths

## Module: `paths.py`

### Functions

#### `find_repo_root(start: Optional[os.PathLike | str] = None) -> Path`
Finds repository root by searching for `.git` or `README.md`.

**Parameters**:
- `start`: Starting path (default: current file location)

**Returns**: Path to repository root

**Environment**: Respects `START_REPO_ROOT` environment variable

#### `repo_root() -> Path`
Returns repository root path.

**Returns**: Path to repository root

#### `languages_root() -> Path`
Returns path to Languages directory.

**Returns**: `repo_root() / "Languages"`

#### `inputs_and_outputs_root() -> Path`
Returns path to Inputs_and_Outputs directory.

**Returns**: `languages_root() / "Inputs_and_Outputs"`

#### `domain_dir() -> Path`
Returns path to Domain directory.

**Returns**: `inputs_and_outputs_root() / "Domain"`

#### `domain_research_dir() -> Path`
Returns path to Domain_Research directory.

**Returns**: `inputs_and_outputs_root() / "Domain_Research"`

#### `ensure_dir(path: os.PathLike | str) -> Path`
Creates directory if it doesn't exist.

**Parameters**:
- `path`: Directory path to create

**Returns**: Resolved path to directory

#### `data_root() -> Path`
Returns path to data directory.

**Returns**: `repo_root() / "data"`

#### `data_written_curriculums_dir() -> Path`
Returns path to written curriculums directory (creates if needed).

**Returns**: `data_root() / "written_curriculums"`

#### `data_translated_curriculums_dir() -> Path`
Returns path to translated curriculums directory (creates if needed).

**Returns**: `data_root() / "translated_curriculums"`

#### `data_visualizations_dir() -> Path`
Returns path to visualizations directory (creates if needed).

**Returns**: `data_root() / "visualizations"`

#### `data_audience_research_dir() -> Path`
Returns path to audience research directory (creates if needed).

**Returns**: `data_root() / "audience_research"`

#### `data_domain_research_dir() -> Path`
Returns path to domain research directory (creates if needed).

**Returns**: `data_root() / "domain_research"`

#### `config_dir() -> Path`
Returns path to configuration directory (creates if needed).

**Returns**: `data_root() / "config"`

## Module: `logging_utils.py`

### Functions

#### `setup_logging(level: int = logging.INFO, name: str | None = None) -> logging.Logger`
Sets up logger with console handler and formatter.

**Parameters**:
- `level`: Logging level (default: `logging.INFO`)
- `name`: Logger name (default: root logger)

**Returns**: Configured logger instance

**Note**: Only adds handler if logger doesn't already have one

## Module: `env.py`

### Functions

#### `load_project_env(env_path: Optional[os.PathLike | str] = None) -> None`
Loads environment variables from `.env` file.

**Parameters**:
- `env_path`: Optional path to `.env` file. If None, searches for `.env` in current directory and parents.

**Behavior**: Searches up directory tree for `.env` file if path not provided

#### `require_env(key: str) -> str`
Requires environment variable to be set.

**Parameters**:
- `key`: Environment variable name

**Returns**: Environment variable value

**Raises**: `EnvironmentError` if variable not set

## Module: `config.py`

### Functions

#### `config_dir() -> Path`
Returns path to configuration directory.

**Returns**: `data_root() / "config"`

#### `load_yaml_config(name: str) -> Dict[str, Any]`
Loads YAML configuration file.

**Parameters**:
- `name`: Config file name (without `.yaml` extension)

**Returns**: Parsed configuration dictionary

**Raises**: `FileNotFoundError`, `yaml.YAMLError`

#### `load_markdown_config(name: str) -> Dict[str, Any]`
Loads Markdown configuration file with YAML frontmatter.

**Parameters**:
- `name`: Config file name (without `.md` extension)

**Returns**: Parsed YAML frontmatter dictionary

**Raises**: `FileNotFoundError`, `ValueError` if no frontmatter found

#### `validate_config_data(data: Dict[str, Any], name: str) -> Dict[str, Any]`
Validates configuration data structure.

**Parameters**:
- `data`: Configuration data to validate
- `name`: Configuration name for error messages

**Returns**: Validated configuration data

**Raises**: `ValueError` if validation fails

#### `load_config(name: str, prefer_yaml: bool = True, validate: bool = True) -> Dict[str, Any]`
Loads configuration, trying YAML first, then Markdown.

**Parameters**:
- `name`: Config file name (without extension)
- `prefer_yaml`: If True, try YAML first (default: True)
- `validate`: If True, validate loaded data (default: True)

**Returns**: Parsed configuration dictionary

**Raises**: `FileNotFoundError` if neither format exists

#### `save_yaml_config(name: str, data: Dict[str, Any]) -> Path`
Saves configuration data as YAML.

**Parameters**:
- `name`: Config file name (without extension)
- `data`: Configuration data to save

**Returns**: Path to saved file

## Module: `prompts.py`

### Functions

#### `prompts_dir() -> Path`
Returns path to prompts directory.

**Returns**: `data_root() / "prompts"`

#### `load_prompt_template(name: str) -> str`
Loads prompt template from Markdown file.

**Parameters**:
- `name`: Template name (without `.md` extension)

**Returns**: Template content as string

**Raises**: `FileNotFoundError` if template doesn't exist

#### `save_prompt_template(name: str, content: str) -> Path`
Saves prompt template to Markdown file.

**Parameters**:
- `name`: Template name (without extension)
- `content`: Template content

**Returns**: Path to saved template

#### `substitute_variables(template: str, variables: Dict[str, Any], strict: bool = False) -> str`
Substitutes variables in template using `{{variable_name}}` syntax.

**Parameters**:
- `template`: Template string with `{{variable}}` placeholders
- `variables`: Dictionary of variable names to values
- `strict`: If True, raises error for missing variables (default: False)

**Returns**: Template with variables substituted

**Raises**: `ValueError` if strict=True and variables are missing

#### `validate_prompt_template(template: str) -> Dict[str, Any]`
Validates prompt template and extracts metadata.

**Parameters**:
- `template`: Template string to validate

**Returns**: Dictionary with validation results:
  - `valid`: Boolean indicating if template is valid
  - `errors`: List of error messages
  - `warnings`: List of warning messages
  - `variables`: Set of variable names found
  - `word_count`: Number of words
  - `line_count`: Number of lines

#### `render_prompt(name: str, variables: Optional[Dict[str, Any]] = None, strict: bool = False) -> str`
Loads and renders prompt template with variables.

**Parameters**:
- `name`: Template name (without extension)
- `variables`: Optional dictionary of variables to substitute
- `strict`: If True, validates template and raises errors for missing variables

**Returns**: Rendered prompt string

**Raises**: `FileNotFoundError`, `ValueError` if strict=True and validation fails

#### `list_prompt_templates() -> list[str]`
Lists all available prompt template names.

**Returns**: List of template names (without extensions)

## Cross-References

- [README.md](README.md) - Module overview and usage examples
- [../README.md](../README.md) - Source code overview
