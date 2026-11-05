# GNN Pipeline Orchestrator (`start-gnn`)

Runs a bounded selection of the
[GNN](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation)
pipeline inside the registered checkout (`src/_clones/gnn`) and reports what the
pipeline actually produced: per-step statuses, artifact counts, artifact
SHA-256 hashes, and the models the pipeline recorded as consumed.

START does not re-implement GNN parsing, type checking, rendering or execution.
This module is a thin orchestrator over the upstream entry point.

## Modules

### `main.py`

Public API and CLI entry point (`start-gnn`).

- `resolve_gnn_checkout(path=None, base_dir=None) -> Path`: locate the checkout
- `registered_revision() -> str`: pinned upstream revision from the clone registration
- `checkout_status(checkout, revision=None) -> dict`: HEAD vs registered revision
- `resolve_interpreter(checkout, override=None) -> (command, source)`: interpreter choice
- `build_pipeline_command(interpreter, steps, target_dir, output_dir) -> list[str]`
- `summarize_outputs(output_dir) -> dict`: read and fingerprint pipeline summaries
- `run_pipeline(...) -> dict`: run the selection and return the full report
- `main(argv=None) -> int`: CLI (`0` ran, `1` pipeline failed, `2` refused)

### `utils.py`

Internal helpers: JSON reading, file hashing, count normalization, step
selection parsing, output tails and terminal report formatting.

### `config.py`

Constants: default steps (3, 5, 11, 12), default target, upstream summary
artifact paths, and the summary field names read from a real pipeline run.

## Usage

```bash
# Bounded default: steps 3,5,11,12 over input/gnn_files/basics
uv run start-gnn

# Full exemplar corpus, machine-readable report
uv run start-gnn --target input/gnn_files --json

# Print the command without running anything
uv run start-gnn --dry-run

# Clone the registered repository first when the checkout is missing
uv run start-gnn --clone

# Fail closed when the checkout is not the registered revision
uv run start-gnn --require-pin
```

Python API:

```python
from src.gnn.main import run_pipeline

report = run_pipeline(steps="3,5", target="input/gnn_files/basics")
print(report["status"], report["artifacts"]["parse"]["counts"])
```

## Where output goes

The default output directory is the upstream default `<checkout>/output`, so the
pipeline writes exactly where it normally does. The interpreter is the
checkout's own `.venv` when present, then `uv run --frozen --no-sync python`
(which never mutates the checkout's environment), then the interpreter running
START.

Pass `--output-dir <path>` to keep a run outside the checkout. Every run writes
three receipts beside the pipeline artifacts:

| Receipt | Content |
|---------|---------|
| `start_gnn_summary.json` | The full run report (checkout revision, command, counts, hashes) |
| `start_gnn_stdout.log` | Raw pipeline stdout |
| `start_gnn_stderr.log` | Raw pipeline stderr (when non-empty) |

## CI conformance check

The repository's `gnn conformance (pinned)` job reads
[`.github/gnn-pin.json`](../../.github/gnn-pin.json), asserts that the registered
GNN revision matches the pin, runs `tests/test_gnn_runner.py`, and parses a
verbatim GNN exemplar fetched from that revision with the pinned parser and type
checker. It does not run the full pipeline; the orchestrator tests cover the
command and receipt path with a real git checkout and a fixture pipeline.

## Reading the report

`checkout_status.relation` is one of:

| Relation | Meaning |
|----------|---------|
| `at_revision` | HEAD is the registered revision |
| `ahead_of_revision` | HEAD descends from the registered revision |
| `diverged` | HEAD neither matches nor descends from it |
| `unknown` | The revision object is absent locally (e.g. a shallow clone) |

Shallow clones from `start-clone` cannot resolve an arbitrary commit, so the
registered revision is reported as provenance. `--require-pin` refuses to run
unless the relation is `at_revision`; `--revision <sha>` verifies against a
different commit than the registered pin.
