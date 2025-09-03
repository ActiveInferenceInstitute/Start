"""Curriculum translation script for creating multilingual Active Inference content.

This script processes curriculum files to:
1. Load curriculum content from written curricula
2. Translate to configured target languages
3. Use proper script mappings and cultural adaptations
4. Save translated curricula in structured data directories

Uses OpenRouter API for high-quality translation.
"""

import argparse
from pathlib import Path
from typing import List

from src.common.logging_utils import setup_logging as common_setup_logging
from src.common.paths import data_translated_curriculums_dir, data_written_curriculums_dir
from src.config.languages import get_target_languages
from src.perplexity.clients import build_openrouter_client
from src.perplexity.translation import process_translations


def validate_languages(requested_languages: List[str], available_languages: List[str]) -> List[str]:
    """Validate requested languages against available ones, allowing custom languages.

    Args:
        requested_languages: Languages requested by user
        available_languages: Languages available from config

    Returns:
        List of valid languages to process (includes custom languages)

    Raises:
        ValueError: If no valid languages provided
    """
    if not requested_languages:
        if not available_languages:
            raise ValueError("No languages available and none requested")
        return available_languages

    if not isinstance(requested_languages, list):
        raise ValueError("Requested languages must be provided as a list")

    valid_languages = []
    invalid_languages = []

    for lang in requested_languages:
        if not lang or not isinstance(lang, str):
            invalid_languages.append(f"Invalid language entry: {lang}")
            continue

        lang = lang.strip()
        if not lang:
            invalid_languages.append("Empty language name")
            continue

        if lang in available_languages:
            valid_languages.append(lang)
        else:
            # Allow custom languages through with a warning
            print(f"Warning: Language '{lang}' not in config. Will attempt translation anyway.")
            print("Note: Translation quality may vary for custom languages.")
            valid_languages.append(lang)

    if invalid_languages:
        print(f"Invalid language entries found: {', '.join(invalid_languages)}")

    if not valid_languages:
        raise ValueError(f"No valid languages to process from: {requested_languages}")

    return valid_languages


def main():
    """Main function to orchestrate curriculum translation.

    This function:
    1. Sets up logging and paths
    2. Initializes the OpenRouter API client
    3. Loads target languages from configuration
    4. Processes translations for all curricula
    5. Saves translated content to data/translated_curriculums/
    """
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
    args = parser.parse_args()

    logger = common_setup_logging()
    logger.info("Starting curriculum translation")

    try:
        # Setup paths using data/ structure
        input_dir = Path(args.input) if args.input else data_written_curriculums_dir()
        output_dir = Path(args.output) if args.output else data_translated_curriculums_dir()

        logger.info(f"Input directory: {input_dir}")
        logger.info(f"Output directory: {output_dir}")

        # Load target languages from configuration (before scanning files to surface config issues early)
        try:
            available_languages = get_target_languages()
            if available_languages:
                logger.info(
                    f"Available languages from config: {', '.join(available_languages[:5])}{'...' if len(available_languages) > 5 else ''}"
                )
        except Exception as e:
            logger.error(f"Failed to load language configuration: {e}")
            available_languages = []

        try:
            target_languages = validate_languages(args.languages, available_languages)
        except ValueError:
            logger.error("No valid target languages specified")
            return

        # Validate input directory exists and has content
        if not input_dir.exists():
            logger.error(f"Input directory does not exist: {input_dir}")
            logger.info(f"Expected to find curriculum files in: {input_dir}")
            return

        # Check for curriculum files
        curriculum_files = list(input_dir.glob("*/complete_curriculum_*.md"))
        if not curriculum_files:
            logger.warning(f"No curriculum files found in {input_dir}")
            logger.info("Looking for files matching pattern: */complete_curriculum_*.md")
            return

        logger.info(f"Found {len(curriculum_files)} curriculum files to translate")

        # Initialize API client (using OpenRouter for translation)
        logger.info("Initializing OpenRouter API client")
        try:
            client = build_openrouter_client()
        except Exception as e:
            logger.error(f"Failed to initialize OpenRouter client: {e}")
            logger.info("Please check your OPENROUTER_API_KEY environment variable")
            return

        logger.info(f"Target languages for translation: {', '.join(target_languages)}")

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Process translations
        logger.info("Starting translation processing")
        try:
            success_count, failed_count = process_translations(
                client, str(input_dir), str(output_dir), target_languages
            )
        except Exception as e:
            logger.error(f"Translation processing failed: {e}")
            logger.debug("Full error details", exc_info=True)
            return

        # Report results
        total_attempted = success_count + failed_count
        logger.info("Translation processing completed:")
        logger.info(f"  - Total translations attempted: {total_attempted}")
        logger.info(f"  - Successful translations: {success_count}")
        logger.info(f"  - Failed translations: {failed_count}")

        if success_count > 0:
            success_rate = (success_count / total_attempted) * 100 if total_attempted > 0 else 0
            logger.info(f"  - Success rate: {success_rate:.1f}%")
            logger.info(f"Translated curricula saved to: {output_dir}")

        if failed_count > 0:
            logger.warning(f"{failed_count} translations failed - check logs for details")

        if success_count == 0:
            logger.info("No translations completed successfully")

    except KeyboardInterrupt:
        logger.info("Translation process interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error in curriculum translation: {str(e)}")
        logger.debug("Full error details", exc_info=True)
        raise


if __name__ == "__main__":
    main()
