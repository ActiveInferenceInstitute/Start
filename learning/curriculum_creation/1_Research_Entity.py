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
from typing import List, Dict, Any

from src.common.config import load_config
from src.common.logging_utils import setup_logging as common_setup_logging
from src.common.paths import data_audience_research_dir, inputs_and_outputs_root, config_dir
from src.perplexity.clients import build_perplexity_client
from src.perplexity.entity import research_target_audience


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
        )
    
    if not config or 'entities' not in config:
        raise ValueError(
            "Invalid entities configuration. Configuration must contain an 'entities' key "
            "with a list of entity objects."
        )
    
    # Validate entity structure
    entities = config.get('entities', [])
    for i, entity in enumerate(entities):
        if not isinstance(entity, dict):
            raise ValueError(f"Entity {i} must be a dictionary")
        if 'name' not in entity:
            raise ValueError(f"Entity {i} must have a 'name' field")
        if 'description' not in entity:
            raise ValueError(f"Entity {entity.get('name', i)} must have a 'description' field")
    
    return config


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
    entities = config.get('entities', [])
    
    if priority_filter:
        entities = [e for e in entities if e.get('priority', 'medium') == priority_filter]
    
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


def main():
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
        help="Overwrite existing research files (default: skip existing)"
    )
    parser.add_argument(
        "--priority", 
        choices=["high", "medium", "low"], 
        help="Process only entities with specific priority level"
    )
    parser.add_argument(
        "--entity", 
        help="Process only specific entity by name"
    )
    args = parser.parse_args()
    
    logger = common_setup_logging()
    logger.info("Starting entity research and audience analysis")
    
    try:
        # Load entities configuration
        logger.info("Loading entities configuration")
        config = load_entities_config()
        research_config = config.get('research_config', {})
        
        # Determine if we should skip existing files
        skip_existing = not args.overwrite and research_config.get('skip_existing', True)
        
        # Setup paths
        fep_actinf_file = inputs_and_outputs_root() / "Domain" / "Synthetic_FEP-ActInf.md"
        output_dir = data_audience_research_dir()
        
        # Validate input files exist
        if not fep_actinf_file.exists():
            logger.error(f"FEP-ActInf file not found: {fep_actinf_file}")
            return
        
        # Get entities to process
        entities = get_entities_to_process(config, args.priority)
        
        # Filter by specific entity name if requested
        if args.entity:
            entities = [e for e in entities if e.get('name') == args.entity]
            if not entities:
                logger.error(f"Entity '{args.entity}' not found in configuration")
                return
        
        if not entities:
            logger.warning("No entities found to process based on criteria")
            return
        
        logger.info(f"Found {len(entities)} entities to process")
        if skip_existing:
            logger.info("Will skip entities with existing research files")
        else:
            logger.info("Will overwrite existing research files")
        
        # Initialize API client
        logger.info("Initializing Perplexity API client")
        client = build_perplexity_client()
        
        # Process each entity with progress tracking
        success_count = 0
        skipped_count = 0
        failed_count = 0
        
        for i, entity in enumerate(entities, 1):
            entity_name = entity.get('name', f'unnamed_entity_{i}')
            entity_description = entity.get('description', '')
            
            logger.info(f"Processing entity {i}/{len(entities)}: {entity_name}")
            
            try:
                # Validate required entity fields
                if not entity_name or entity_name.startswith('unnamed_'):
                    logger.warning(f"Entity {i} missing name field, skipping")
                    failed_count += 1
                    continue
                
                if not entity_description:
                    logger.warning(f"Entity {entity_name} missing description field, skipping")
                    failed_count += 1
                    continue
                
                # Check if output already exists
                if skip_existing and check_output_exists(entity_name, output_dir):
                    logger.info(f"Skipping {entity_name}: research file already exists")
                    skipped_count += 1
                    continue
                
                logger.info(f"Analyzing entity: {entity_name}")
                logger.debug(f"Description: {entity_description[:100]}{'...' if len(entity_description) > 100 else ''}")
                
                # Create entity data for research
                entity_data = f"Entity Name: {entity_name}\nDescription: {entity_description}\nCategory: {entity.get('category', 'unknown')}"
                
                # Call the research function with entity data directly
                result = research_target_audience(
                    client, entity_data, str(fep_actinf_file), str(output_dir), entity_name
                )
                success_count += 1
                logger.info(f"✅ Successfully processed: {entity_name} (processing time: {result.processing_time})")
                
            except KeyboardInterrupt:
                logger.info("Processing interrupted by user")
                break
            except Exception as e:
                failed_count += 1
                logger.error(f"❌ Failed to process {entity_name}: {str(e)}")
                logger.debug(f"Full error details for {entity_name}", exc_info=True)
                continue
        
        logger.info(
            f"Entity research completed: {success_count} successful, "
            f"{skipped_count} skipped, {failed_count} failed"
        )
        
    except Exception as e:
        logger.error(f"Fatal error in entity research: {e}")
        raise

if __name__ == "__main__":
    main()
