# Visualization Utilities Technical Reference

## Overview

Technical documentation for visualization and metrics generation functions.

## Module: `runner.py`

### Functions

#### `collect_curriculum_files(base_dir: str) -> List[Tuple[str, str]]`
Collects curriculum files from directory.

**Parameters**:
- `base_dir`: Base directory to search

**Returns**: List of (entity_name, file_path) tuples

**Behavior**: Searches for `complete_curriculum_*.md` files recursively

#### `generate_curriculum_metrics(curriculum_docs: List[str], entity_labels: List[str], output_dir: str) -> None`
Generates curriculum metrics and saves to CSV.

**Parameters**:
- `curriculum_docs`: List of curriculum content strings
- `entity_labels`: List of entity/curriculum names
- `output_dir`: Output directory for metrics CSV

**Output**: Saves `curriculum_metrics.csv` to `{output_dir}/metrics/` subdirectory

**Metrics**: Total words, sections, paragraphs, words per section, words per paragraph

**Note**: The CSV file is saved in a `metrics/` subdirectory within the output directory.

#### `run(input_root: str, output_root: str) -> None`
Main visualization runner.

**Parameters**:
- `input_root`: Input directory containing curricula
- `output_root`: Output directory for visualizations

**Behavior**: Collects curricula, generates metrics, saves to output directory

## Cross-References

- [README.md](README.md) - Module overview and usage
- [../README.md](../README.md) - Source code overview
- [../../docs/visualizations.md](../../docs/visualizations.md) - Visualization documentation
