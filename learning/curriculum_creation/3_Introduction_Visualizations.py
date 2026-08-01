"""Visualization generation script for curriculum structure.

This script delegates visualization generation to the canonical pipeline
orchestrator (``generate_custom_curriculum.py``). It is a thin, stable entry
point that forwards visualization-specific flags and shares one execution path
with the CLI and GUI. The canonical ``src/visualization`` runner owns the real
chart/metric/manifest logic.
"""

import argparse


def main(input_folder: str | None = None, output_folder: str | None = None) -> int:
    """Delegate curriculum visualization to the canonical pipeline."""
    from learning.curriculum_creation.generate_custom_curriculum import main as canonical_main

    delegated = ["--non-interactive", "--stages", "visualizations"]
    if input_folder:
        delegated.extend(["--curriculum-dir", input_folder])
    if output_folder:
        delegated.extend(["--visualizations-dir", output_folder])
    return canonical_main(delegated)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate PNG charts and Mermaid diagrams for curriculum visualization."
    )
    parser.add_argument(
        "--input",
        help="Path to directory containing curriculum files (default: data/written_curriculums)",
    )
    parser.add_argument(
        "--output", help="Path to save visualization outputs (default: data/visualizations)"
    )
    args = parser.parse_args()

    raise SystemExit(main(args.input, args.output))
