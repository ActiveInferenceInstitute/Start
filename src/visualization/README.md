# Visualization Utilities

Visualization utilities for curriculum metrics and analysis.

## Overview

This module provides functions to collect curriculum files, generate metrics, and create visualizations.

## Modules

### `runner.py`
Visualization runner:
- `collect_curriculum_files()`: Collect curriculum files from directory
- `generate_curriculum_metrics()`: Generate curriculum metrics
- `run()`: Main visualization runner

## Usage Examples

```python
from src.visualization.runner import (
    collect_curriculum_files,
    generate_curriculum_metrics,
    run
)

# Collect curriculum files
files = collect_curriculum_files("data/written_curriculums")

# Generate metrics
generate_curriculum_metrics(
    curriculum_docs=["content1", "content2"],
    entity_labels=["Entity1", "Entity2"],
    output_dir="data/visualizations"
)

# Run full visualization pipeline
run("data/written_curriculums", "data/visualizations")
```

## Navigation

- [AGENTS.md](AGENTS.md) - Complete function reference
- [../README.md](../README.md) - Source code overview
- [../../docs/visualizations.md](../../docs/visualizations.md) - Visualization documentation
