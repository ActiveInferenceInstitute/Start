"""Curriculum writing script for generating Active Inference introductions.

This script processes research files to:
1. Convert research reports into structured curriculum content
2. Generate comprehensive Active Inference introductions
3. Create modular curriculum sections
4. Save complete curricula in structured data directories

Uses OpenRouter API for content generation.
"""

import argparse
from pathlib import Path
from typing import List

from src.common.logging_utils import setup_logging as common_setup_logging


def get_research_files(research_dir: Path, pattern: str = "*_research_*") -> List[Path]:
    """Get list of research files to process.

    Args:
        research_dir: Directory containing research files
        pattern: File name pattern to match

    Returns:
        List of research file paths to process
    """
    if not research_dir.exists():
        return []

    files: List[Path] = []
    # Support both JSON and Markdown research files
    for ext in (".json", ".md"):
        files.extend(research_dir.glob(f"{pattern}{ext}"))

    # Exclude negative test files such as those starting with 'not_research'
    files = [f for f in files if not f.name.startswith("not_research")]

    return sorted(files)


def main(argv: list[str] | None = None) -> int:
    """Main function to orchestrate curriculum generation.

    This function:
    1. Sets up logging and paths
    2. Initializes the OpenRouter API client
    3. Processes audience research files
    4. Processes domain research files
    5. Generates complete curricula
    6. Saves results to data/written_curriculums/
    """
    parser = argparse.ArgumentParser(
        description="Generate curricula through the canonical pipeline"
    )
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    from learning.curriculum_creation.generate_custom_curriculum import main as canonical_main

    delegated = ["--non-interactive", "--stages", "curriculum"]
    if args.overwrite:
        delegated.append("--overwrite")
    if args.output_dir:
        delegated.extend(["--curriculum-dir", str(args.output_dir)])
    logger = common_setup_logging()
    logger.info("Delegating curriculum generation to the canonical pipeline")
    try:
        return canonical_main(delegated)
    except Exception as e:
        logger.error("Canonical curriculum generation failed: %s", e)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
