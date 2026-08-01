"""Curriculum translation script for creating multilingual Active Inference content.

This script delegates translation to the canonical pipeline orchestrator
(``generate_custom_curriculum``). It exists as a thin, stable entry point that
forwards translation-specific flags while sharing one execution path with the
CLI and GUI.
"""

import argparse

from src.common.logging_utils import setup_logging as common_setup_logging

logger = common_setup_logging()


def main(argv: list[str] | None = None) -> int:
    """Delegate translation to the canonical pipeline and return its exit code."""
    parser = argparse.ArgumentParser(
        description="Translate curriculum content to multiple languages."
    )
    parser.add_argument(
        "--input",
        help="Path to directory containing curriculum files (default: data/written_curriculums)",
    )
    parser.add_argument(
        "--output", help="Path to save translated files (default: data/translated_curriculums)"
    )
    parser.add_argument(
        "--languages",
        nargs="+",
        help="List of target languages for translation (default: all configured languages)",
    )
    args = parser.parse_args(argv)
    from learning.curriculum_creation.generate_custom_curriculum import main as canonical_main

    delegated = ["--non-interactive", "--stages", "translations"]
    if args.input:
        delegated.extend(["--curriculum-dir", args.input])
    if args.output:
        delegated.extend(["--translation-dir", args.output])
    if args.languages:
        delegated.extend(["--languages", *args.languages])
    logger.info("Delegating translation to the canonical pipeline")
    try:
        return canonical_main(delegated)
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as e:
        logger.error("Translation pipeline failed: %s", e)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
