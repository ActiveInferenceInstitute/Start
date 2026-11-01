"""Constants for the ``start-gnn`` orchestrator.

The GNN project is optional reference material cloned into ``src/_clones/gnn``
(see [docs/clones.md](../../docs/clones.md)).  This module records how START
drives that checkout; the pinned upstream revision belongs to the clone
registration in :mod:`src.repos.cloning`.

Every field name below was read from a real GNN pipeline run (steps 3, 5, 11,
12 over ``input/gnn_files/basics``), so the summary reader reports only keys
the pipeline actually writes.
"""

from __future__ import annotations

#: Registered checkout name in ``src.repos.cloning``.
GNN_REPO_NAME = "gnn"

#: Upstream entry point, relative to the checkout root.
PIPELINE_SCRIPT = "src/gnn/main.py"

#: Parse -> type-check -> render -> execute: the cheapest end-to-end slice.
DEFAULT_STEPS: tuple[int, ...] = (3, 5, 11, 12)

#: Bounded default corpus (two exemplars); ``--target input/gnn_files`` runs all.
DEFAULT_TARGET_SUBDIR = "input/gnn_files/basics"

#: Upstream output directory used when ``--output-dir`` is not given.
DEFAULT_OUTPUT_SUBDIR = "output"

DEFAULT_TIMEOUT_SECONDS = 3600

STEP_DESCRIPTIONS: dict[int, str] = {
    3: "parse GNN specifications and serialize the registered formats",
    5: "type-check the parsed models",
    11: "render models into simulation framework code",
    12: "execute the rendered simulations",
}

#: ``(label, path relative to the pipeline output directory)`` summary files.
SUMMARY_ARTIFACTS: tuple[tuple[str, str], ...] = (
    ("pipeline", "00_pipeline_summary/pipeline_execution_summary.json"),
    ("parse", "3_gnn_output/gnn_processing_summary.json"),
    ("type_check", "5_type_checker_output/type_check_summary.json"),
    ("render", "11_render_output/render_processing_summary.json"),
    ("execute", "12_execute_output/summaries/execution_summary.json"),
)

#: Scalar summary fields reported per artifact label, when present.
SUMMARY_FIELDS: dict[str, tuple[str, ...]] = {
    "pipeline": (
        "overall_status",
        "run_id",
        "total_duration_seconds",
        "planned_steps",
        "unfinished_steps",
    ),
    "parse": (
        "total_files",
        "successful_parses",
        "failed_parses",
        "total_formats_generated",
    ),
    "type_check": (
        "files_processed",
        "success",
        "valid_files",
        "invalid_files",
        "warning_files",
        "total_errors",
        "total_warnings",
    ),
    "render": (
        "total_files",
        "successful_files",
        "failed_files",
        "total_framework_attempts",
        "successful_framework_renderings",
        "unsupported_framework_renderings",
        "framework_success_rate",
    ),
    "execute": (
        "status",
        "success",
        "total_scripts_found",
        "attempted_scripts",
        "successful_executions",
        "failed_executions",
        "skipped_executions",
        "success_rate",
        "outcome_reason",
    ),
}

#: Fields kept from each entry of the pipeline summary's ``steps`` list.
STEP_ENTRY_FIELDS: tuple[str, ...] = (
    "step_number",
    "script_name",
    "status",
    "duration_seconds",
    "exit_code",
)

#: Fields kept from each entry of the pipeline summary's ``model_selection`` list.
MODEL_ENTRY_FIELDS: tuple[str, ...] = (
    "relative_path",
    "model_id",
    "sha256",
    "steps",
)

#: Nested pipeline performance counters reported when present.
PERFORMANCE_FIELDS: tuple[str, ...] = (
    "total_steps",
    "successful_steps",
    "failed_steps",
    "warnings",
    "peak_memory_mb",
)

#: Pipeline statuses that mean "ran, but not cleanly".
STATUS_WITH_WARNINGS = "SUCCESS_WITH_WARNINGS"

#: Names of the receipts ``start-gnn`` writes beside the pipeline outputs.
SUMMARY_RECEIPT_NAME = "start_gnn_summary.json"
STDOUT_RECEIPT_NAME = "start_gnn_stdout.log"
STDERR_RECEIPT_NAME = "start_gnn_stderr.log"

#: Number of trailing process-output lines echoed in the terminal report.
STDOUT_TAIL_LINES = 20
STDERR_TAIL_LINES = 10
