# Common Utilities

Shared utilities and helper functions used throughout the START project.

## Modules

### `io.py`
File I/O operations for text and JSON files:
- Read/write text files with UTF-8 encoding
- Read/write JSON files with automatic parent directory creation
- List files with pattern matching
- Load key-value pairs from configuration files
- List domain markdown files with exclusion support

### `paths.py`
Path management and directory resolution:
- Repository root detection
- Data directory paths
- Configuration directory paths
- Language and input/output directory paths
- Directory creation utilities

### `logging_utils.py`
Logging configuration:
- Standardized logger setup with console handler
- Configurable log levels
- Consistent formatting across modules

### `env.py`
Environment variable management:
- Load `.env` files from project root
- Require environment variables with error handling
- Automatic `.env` file discovery

### `config.py`
Configuration file loading:
- YAML configuration loading
- Markdown configuration with YAML frontmatter
- Configuration validation
- Save configuration to YAML

### `prompts.py`
Prompt template management:
- Load prompt templates from Markdown files
- Variable substitution with `{{variable_name}}` syntax
- Template validation
- List available templates

## Usage Examples

```python
from src.common.io import read_text, write_json, read_json
from src.common.paths import repo_root, data_root
from src.common.logging_utils import setup_logging
from src.common.env import load_project_env, require_env
from src.common.config import load_yaml_config
from src.common.prompts import load_prompt_template, render_prompt

# File I/O
content = read_text("data/config/domains.yaml")
write_json("output.json", {"key": "value"})

# Paths
root = repo_root()
data_dir = data_root()

# Logging
logger = setup_logging(level=logging.INFO)

# Environment
load_project_env()
api_key = require_env("PERPLEXITY_API_KEY")

# Configuration
config = load_yaml_config("domains")

# Prompts
template = load_prompt_template("research_domain_analysis")
rendered = render_prompt("research_domain_analysis", {"domain": "biochemistry"})
```

## Navigation

- [AGENTS.md](AGENTS.md) - Complete function reference
- [../README.md](../README.md) - Source code overview
