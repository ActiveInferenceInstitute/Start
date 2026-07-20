"""Entity research script for analyzing target audiences and creating personalized curricula.

This script processes entities from configuration to:
1. Research target audience backgrounds and learning needs
2. Analyze existing knowledge and learning preferences
3. Generate personalized Active Inference curriculum recommendations
4. Save research reports in structured data directories

Uses Perplexity API for online research and analysis.
Reads entity list from data/config/entities.yaml configuration file.
"""

import argparse
from pathlib import Path
from typing import Any, Dict, List

from src.common.config import load_config
from src.common.logging_utils import setup_logging as common_setup_logging
from src.config.schemas import add_stable_ids, validate_entities_config


def load_entities_config() -> Dict[str, Any]:
    """Load entities configuration from YAML file.

    Returns:
        Dictionary containing entities configuration

    Raises:
        FileNotFoundError: If entities.yaml not found
        ValueError: If configuration is invalid
    """
    try:
        config = load_config("entities")
    except FileNotFoundError:
        # Provide helpful error message and suggest creation
        raise FileNotFoundError(
            "Entities configuration file not found. Please create data/config/entities.yaml "
            "with at least the following structure:\n"
            "entities:\n"
            "  - name: example_entity\n"
            "    description: Example entity description\n"
            "    category: professional\n"
            "    priority: medium"
        ) from None  # FileNotFoundError — no chained exception needed

    if not config or "entities" not in config:
        raise ValueError(
            "Invalid entities configuration. Configuration must contain an 'entities' key "
            "with a list of entity objects."
        )

    validate_entities_config(config)
    return add_stable_ids(config, "entities")


def get_entities_to_process(
    config: Dict[str, Any], priority_filter: str = None
) -> List[Dict[str, Any]]:
    """Get list of entities to process based on configuration.

    Args:
        config: Entities configuration dictionary
        priority_filter: Optional priority filter (high, medium, low)

    Returns:
        List of entity dictionaries to process
    """
    entities = config.get("entities", [])

    if priority_filter:
        entities = [e for e in entities if e.get("priority", "medium") == priority_filter]

    return entities


def check_output_exists(entity_name: str, output_dir: Path) -> bool:
    """Check if research output already exists for an entity.

    Args:
        entity_name: Name of the entity
        output_dir: Output directory path

    Returns:
        True if output file exists, False otherwise
    """
    # Check for JSON output file (standard format)
    json_pattern = f"{entity_name}_research_*.json"
    existing_files = list(output_dir.glob(json_pattern))
    return len(existing_files) > 0


def main(argv: list[str] | None = None) -> int:
    """Main function to orchestrate entity research and audience analysis.

    This function:
    1. Parses command line arguments
    2. Sets up logging and paths
    3. Loads entities configuration
    4. Initializes the Perplexity API client
    5. Processes each configured entity
    6. Saves results to data/audience_research/
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Research target entities for personalized Active Inference curricula"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing research files (default: skip existing)",
    )
    parser.add_argument(
        "--priority",
        choices=["high", "medium", "low"],
        help="Process only entities with specific priority level",
    )
    parser.add_argument("--entity", help="Process only specific entity by name")
    args = parser.parse_args(argv)
    from learning.curriculum_creation.generate_custom_curriculum import main as canonical_main

    delegated = ["--non-interactive", "--stages", "entity-research"]
    if args.entity:
        delegated.extend(["--entities", args.entity])
    if args.priority:
        delegated.extend(["--entity-priority", args.priority])
    if args.overwrite:
        delegated.append("--overwrite")
    logger = common_setup_logging()
    logger.info("Delegating entity research to the canonical pipeline")
    try:
        return canonical_main(delegated)
    except Exception as e:
        logger.error("Canonical entity research failed: %s", e)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
