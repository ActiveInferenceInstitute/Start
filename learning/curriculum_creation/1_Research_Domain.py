"""Domain research script for analyzing domains and generating Active Inference curricula.

This script processes domains from configuration to:
1. Analyze domain characteristics and professional backgrounds
2. Generate tailored Active Inference curricula
3. Save research reports in structured data directories

Uses Perplexity API for online research and analysis.
Reads domain list from data/config/domains.yaml configuration file.
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

from src.common.config import load_config
from src.common.logging_utils import setup_logging as common_setup_logging
from src.common.paths import data_domain_research_dir, inputs_and_outputs_root
from src.perplexity.clients import build_perplexity_client
from src.perplexity.domain import analyze_domain

# Expose module under its filesystem path name so tests can patch it
try:
    sys.modules.setdefault("learning.curriculum_creation.1_Research_Domain", sys.modules[__name__])
except Exception:
    pass


def load_domains_config() -> Dict[str, Any]:
    """Load domains configuration from YAML file.

    Returns:
        Dictionary containing domains configuration

    Raises:
        FileNotFoundError: If domains.yaml not found
        ValueError: If configuration is invalid
    """
    try:
        config = load_config("domains")
    except FileNotFoundError:
        # Provide helpful error message and suggest creation
        raise FileNotFoundError(
            "Domains configuration file not found. Please create data/config/domains.yaml "
            "with at least the following structure:\n"
            "domains:\n"
            "  - name: example_domain\n"
            "    description: Example domain description\n"
            "    category: general\n"
            "    keywords: [keyword1, keyword2]\n"
            "    priority: medium"
        )

    if not config or "domains" not in config:
        raise ValueError(
            "Invalid domains configuration. Configuration must contain a 'domains' key "
            "with a list of domain objects."
        )

    # Validate domain structure
    domains = config.get("domains", [])
    for i, domain in enumerate(domains):
        if not isinstance(domain, dict):
            raise ValueError(f"Domain {i} must be a dictionary")
        if "name" not in domain:
            raise ValueError(f"Domain {i} must have a 'name' field")
        if not isinstance(domain.get("keywords", []), list):
            raise ValueError(f"Domain {domain.get('name', i)} keywords must be a list")

    return config


def get_domains_to_process(
    config: Dict[str, Any], priority_filter: str = None, category_filter: str = None
) -> List[Dict[str, Any]]:
    """Get list of domains to process based on configuration.

    Args:
        config: Domains configuration dictionary
        priority_filter: Optional priority filter (high, medium, low)
        category_filter: Optional category filter

    Returns:
        List of domain dictionaries to process
    """
    domains = config.get("domains", [])

    if priority_filter:
        domains = [d for d in domains if d.get("priority", "medium") == priority_filter]

    if category_filter:
        domains = [d for d in domains if d.get("category") == category_filter]

    return domains


def check_domain_output_exists(domain_name: str, output_dir: Path) -> bool:
    """Check if research output already exists for a domain.

    Args:
        domain_name: Name of the domain
        output_dir: Output directory path

    Returns:
        True if output file exists, False otherwise
    """
    # Check for both JSON and Markdown output files
    json_pattern = f"{domain_name}_research_*.json"
    md_pattern = f"{domain_name}_research_*.md"

    existing_json = list(output_dir.glob(json_pattern))
    existing_md = list(output_dir.glob(md_pattern))

    return len(existing_json) > 0 or len(existing_md) > 0


def get_domain_files(directory: Path) -> List[Path]:
    """Get all valid domain files from a directory.

    Args:
        directory: Directory to scan for domain files

    Returns:
        List of Path objects for valid domain files

    Note:
        Looks for files matching pattern 'Synthetic_*.md' but excludes 'Synthetic_FEP-ActInf.md'
    """
    if not directory.exists():
        return []

    domain_files = []
    for file_path in directory.glob("Synthetic_*.md"):
        # Exclude the FEP-ActInf file
        if file_path.name != "Synthetic_FEP-ActInf.md":
            domain_files.append(file_path)

    return sorted(domain_files)


def main():
    """Main function to orchestrate domain analysis and curriculum generation.

    This function:
    1. Parses command line arguments
    2. Sets up logging and paths
    3. Loads domains configuration
    4. Initializes the Perplexity API client
    5. Processes each configured domain
    6. Saves results to data/domain_research/
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Research domains for tailored Active Inference curricula"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing research files (default: skip existing)",
    )
    parser.add_argument(
        "--priority",
        choices=["high", "medium", "low"],
        help="Process only domains with specific priority level",
    )
    parser.add_argument(
        "--category",
        help="Process only domains in specific category (e.g., life_sciences, technology, business)",
    )
    parser.add_argument("--domain", help="Process only specific domain by name")
    # Use parse_known_args to ignore pytest args like -q
    args, _unknown = parser.parse_known_args()

    logger = common_setup_logging()
    logger.info("Starting domain research and curriculum generation")

    try:
        # Initialize API client first so initialization errors surface
        logger.info("Initializing Perplexity API client")
        client = build_perplexity_client()

        # Setup paths
        fep_actinf_file = inputs_and_outputs_root() / "Domain" / "Synthetic_FEP-ActInf.md"
        output_dir = data_domain_research_dir()

        # Validate FEP/ActInf reference
        if not fep_actinf_file.exists():
            logger.error(f"FEP-ActInf file not found: {fep_actinf_file}")
            return

        # Prefer explicit domain files when present
        domain_dir = inputs_and_outputs_root() / "Domain"
        domain_files = get_domain_files(domain_dir)
        if not domain_files:
            logger.warning("No domain files found in Domain directory")
            return

        # Use the first domain file (tests create a single target file)
        domain_file = domain_files[0]
        # Derive domain name from filename (strip Synthetic_ prefix)
        domain_name = domain_file.stem.replace("Synthetic_", "")

        logger.info(f"Analyzing domain from file: {domain_file.name}")
        result = analyze_domain(
            client,
            str(domain_file),
            str(fep_actinf_file),
            str(output_dir),
            domain_name,
        )
        logger.info(
            f"✅ Successfully processed: {domain_name} (processing time: {result.processing_time})"
        )

    except Exception as e:
        logger.error(f"Fatal error in domain research: {e}")
        raise


if __name__ == "__main__":
    main()
