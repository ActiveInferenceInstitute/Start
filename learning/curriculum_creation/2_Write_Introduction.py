"""Curriculum writing script for generating Active Inference introductions.

This script processes research files to:
1. Convert research reports into structured curriculum content
2. Generate comprehensive Active Inference introductions
3. Create modular curriculum sections
4. Save complete curricula in structured data directories

Uses OpenRouter API for content generation.
"""

import glob
import os
from pathlib import Path
from typing import List, Optional

from src.common.logging_utils import setup_logging as common_setup_logging
from src.common.paths import data_written_curriculums_dir, data_audience_research_dir, data_domain_research_dir, inputs_and_outputs_root
from src.perplexity.clients import build_openrouter_client
from src.perplexity.curriculum import process_research_file


def get_research_files(research_dir: Path, pattern: str = "*_research_*.md") -> List[Path]:
    """Get list of research files to process.
    
    Args:
        research_dir: Directory containing research files
        pattern: File name pattern to match
        
    Returns:
        List of research file paths to process
    """
    if not research_dir.exists():
        return []
    
    return list(research_dir.glob(pattern))


def process_research_directory(
    client,
    research_dir: Path,
    fep_actinf_file: Path,
    output_dir: Path,
    dir_type: str
) -> tuple[int, int]:
    """Process all research files in a directory.
    
    Args:
        client: API client for content generation
        research_dir: Directory containing research files
        fep_actinf_file: Path to FEP-ActInf source material
        output_dir: Output directory for curricula
        dir_type: Type of directory (for logging)
        
    Returns:
        Tuple of (success_count, error_count)
    """
    logger = common_setup_logging()
    
    # Validate input directory exists
    if not research_dir.exists():
        logger.warning(f"Research directory does not exist: {research_dir}")
        return 0, 0
    
    research_files = get_research_files(research_dir)
    
    if not research_files:
        logger.warning(f"No research files found in {research_dir}")
        logger.info(f"Looking for files matching pattern: *_research_*.md in {research_dir}")
        return 0, 0
    
    logger.info(f"Processing {len(research_files)} {dir_type} research files")
    
    # Validate FEP-ActInf file exists
    if not fep_actinf_file.exists():
        logger.error(f"FEP-ActInf source file not found: {fep_actinf_file}")
        return 0, len(research_files)
    
    success_count = 0
    error_count = 0
    
    for i, research_file in enumerate(research_files, 1):
        try:
            logger.info(f"Processing {dir_type} research {i}/{len(research_files)}: {research_file.name}")
            
            # Validate file has content
            try:
                file_size = research_file.stat().st_size
                if file_size == 0:
                    logger.warning(f"Skipping empty file: {research_file.name}")
                    error_count += 1
                    continue
                logger.debug(f"File size: {file_size} bytes")
            except Exception as e:
                logger.warning(f"Could not check file size for {research_file.name}: {e}")
            
            result = process_research_file(client, str(research_file), str(fep_actinf_file), str(output_dir))
            if result:
                success_count += 1
                logger.info(f"✅ Successfully processed: {research_file.name}")
                logger.debug(f"Generated curriculum saved to: {result}")
            else:
                error_count += 1
                logger.warning(f"⚠️  No output generated for: {research_file.name}")
                
        except KeyboardInterrupt:
            logger.info("Processing interrupted by user")
            break
        except Exception as e:
            error_count += 1
            logger.error(f"❌ Failed to process {research_file.name}: {str(e)}")
            logger.debug(f"Full error details for {research_file.name}", exc_info=True)
            continue
    
    logger.info(f"Completed processing {dir_type} directory: {success_count} successful, {error_count} failed")
    return success_count, error_count


def main():
    """Main function to orchestrate curriculum generation.
    
    This function:
    1. Sets up logging and paths
    2. Initializes the OpenRouter API client
    3. Processes audience research files
    4. Processes domain research files
    5. Generates complete curricula
    6. Saves results to data/written_curriculums/
    """
    logger = common_setup_logging()
    logger.info("Starting curriculum generation from research files")
    
    try:
        # Setup paths - using data/ structure
        io_root = inputs_and_outputs_root()
        audience_research_dir = data_audience_research_dir()
        domain_research_dir = data_domain_research_dir()
        fep_actinf_file = io_root / "Domain" / "Synthetic_FEP-ActInf.md"
        output_dir = data_written_curriculums_dir()
        
        # Validate input files exist
        if not fep_actinf_file.exists():
            logger.error(f"FEP-ActInf file not found: {fep_actinf_file}")
            return
        
        # Initialize API client (using OpenRouter for content generation)
        logger.info("Initializing OpenRouter API client")
        client = build_openrouter_client()
        
        total_success = 0
        total_error = 0
        
        # Process audience research files
        success, error = process_research_directory(
            client, audience_research_dir, fep_actinf_file, output_dir, "audience"
        )
        total_success += success
        total_error += error
        
        # Process domain research files
        success, error = process_research_directory(
            client, domain_research_dir, fep_actinf_file, output_dir, "domain"
        )
        total_success += success
        total_error += error
        
        logger.info("Curriculum generation completed:")
        logger.info(f"  - Total successful: {total_success}")
        logger.info(f"  - Total failed: {total_error}")
        
        if total_success == 0 and total_error > 0:
            logger.error("No curricula were generated successfully")
        elif total_success > 0:
            logger.info(f"Generated curricula saved to: {output_dir}")
        
    except Exception as e:
        logger.error(f"Fatal error in curriculum generation: {e}")
        raise


if __name__ == "__main__":
    main()
