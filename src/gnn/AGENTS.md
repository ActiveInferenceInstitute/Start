# GNN Orchestrator Technical Reference

## Overview

Technical documentation for `src/gnn/`, the `start-gnn` orchestrator that runs a
bounded selection of the cloned GNN pipeline and reports its artifacts.

The GNN checkout is reference material cloned through `start-clone` into
`src/_clones/gnn`. START never edits it; the run report records the checkout's
HEAD and its relationship to the registered revision.

## Module: `main.py`

### Functions

#### `resolve_gnn_checkout(path=None, base_dir=None) -> Path`
Returns the checkout to use: an explicit `path` when given, otherwise the
registered clone destination.

#### `registered_revision() -> str`
Pinned upstream revision recorded on the `gnn` entry of
`get_predefined_repositories()` (empty when the registration has no revision).

#### `checkout_status(checkout, revision=None) -> Dict[str, Any]`
Reports `exists`, `is_git_repo`, `has_pipeline_script`, `branch`, `head`,
`relation` (`at_revision`, `ahead_of_revision`, `diverged`, `unknown`),
`revision_object_present`, and a human-readable `detail`.

#### `resolve_interpreter(checkout, override=None) -> Tuple[List[str], str]`
Chooses the command prefix and its source label (`explicit`, `checkout-venv`,
`uv-no-sync`, `start-interpreter`). The `checkout-venv` candidate is
`<checkout>/.venv/bin/python` (or `Scripts/python.exe`); `uv run --frozen
--no-sync python` performs no environment mutation.

#### `build_pipeline_command(interpreter, steps, target_dir, output_dir) -> List[str]`
Builds `[... interpreter, "src/gnn/main.py", "--only-steps", ..., "--target-dir", ..., "--output-dir", ...]`.

#### `summarize_outputs(output_dir) -> Dict[str, Any]`
Reads the five upstream summary artifacts (see `config.SUMMARY_ARTIFACTS`) and
returns, per label, `exists`, `path`, `sha256`, `modified_utc`, `top_level_keys`
and `counts` (only fields the artifact actually contains).

#### `run_pipeline(checkout=None, steps=None, target=None, output_dir=None, interpreter_override=None, timeout=None, dry_run=False, require_pin=False, clone_missing=False, base_dir=None, revision=None) -> Dict[str, Any]`
Runs the selection and returns the run report:

- `status`: `ok`, `ok-with-warnings`, `failed`, `refused`, `dry-run`
- `checkout_status`, `steps`, `step_descriptions`, `target_dir`, `output_dir`
- `interpreter` (`command`, `source`), `command`, `execution` (`exit_code`,
  `duration_seconds`, `stdout_lines`, `stdout_tail`, `stderr_tail`)
- `artifacts`, `pipeline_steps`, `model_selection`, `pipeline_status`
- `receipts` (paths of `start_gnn_summary.json`, `start_gnn_stdout.log`, and
  `start_gnn_stderr.log` when stderr was non-empty)
- `reason`, `clone` (when `clone_missing` cloned the repository)

`require_pin=True` refuses unless `relation` is `at_revision`. Nothing is
executed when `dry_run=True`.

#### `main(argv=None) -> int`
CLI entry point (`start-gnn`). Exit codes: `0` ran, `1` pipeline failed,
`2` refused.

#### `parse_args(argv) -> argparse.Namespace`
Flag parsing for the CLI: `--checkout`, `--steps`, `--target`, `--output-dir`,
`--python-executable`, `--timeout`, `--require-pin`, `--revision`, `--clone`,
`--dry-run`, `--json`.

## Module: `utils.py`

Internal helpers: `normalize_counts`, `select_fields`, `read_json_object`,
`sha256_file`, `file_modified_utc`, `parse_step_selection`, `tail_lines`,
`format_report`.

## Module: `config.py`

`DEFAULT_STEPS` (3, 5, 11, 12), `DEFAULT_TARGET_SUBDIR`
(`input/gnn_files/basics`), `DEFAULT_OUTPUT_SUBDIR` (`output`),
`DEFAULT_TIMEOUT_SECONDS`, `STEP_DESCRIPTIONS`, `SUMMARY_ARTIFACTS`,
`SUMMARY_FIELDS`, `STEP_ENTRY_FIELDS`, `MODEL_ENTRY_FIELDS`,
`PERFORMANCE_FIELDS`, `STATUS_WITH_WARNINGS`, and the receipt file names.

## Cross-References

- [README.md](README.md) - Module overview and usage
- [../repos/AGENTS.md](../repos/AGENTS.md) - Clone registration and revision checks
- [../../docs/clones.md](../../docs/clones.md) - Clone management and `start-gnn`
