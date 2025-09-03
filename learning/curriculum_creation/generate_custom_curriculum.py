"""Comprehensive orchestrator for Active Inference curriculum generation pipeline.

This script provides a unified interface for the complete curriculum generation workflow:
1. Domain research using Perplexity API
2. Entity/audience research using Perplexity API
3. Curriculum content generation using OpenRouter API
4. Visualization creation (PNG charts and Mermaid diagrams)
5. Multi-language translation using OpenRouter API

Features:
- Configurable domain and entity selection
- Parallel processing where possible
- Comprehensive error handling and progress tracking
- Reuses existing modular components
- Supports custom output directories and processing options
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to Python path for src imports
script_dir = Path(__file__).parent
project_root = (
    script_dir.parent.parent
)  # Go up two levels: curriculum_creation -> learning -> start
sys.path.insert(0, str(project_root))

from src.common.logging_utils import setup_logging as common_setup_logging
from src.common.paths import (
    data_audience_research_dir,
    data_domain_research_dir,
    data_translated_curriculums_dir,
    data_visualizations_dir,
    data_written_curriculums_dir,
    inputs_and_outputs_root,
)
from src.config.languages import get_target_languages
from src.perplexity.clients import build_openrouter_client, build_perplexity_client
from src.perplexity.domain import analyze_domain
from src.perplexity.entity import research_target_audience
from src.perplexity.translation import process_translations


# Import functions from the existing scripts by loading them as modules
def _import_script_functions():
    """Import functions from existing curriculum scripts."""
    script_dir = Path(__file__).parent

    # Import domain research functions
    spec = importlib.util.spec_from_file_location(
        "research_domain", script_dir / "1_Research_Domain.py"
    )
    domain_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(domain_module)

    # Import entity research functions
    spec = importlib.util.spec_from_file_location(
        "research_entity", script_dir / "1_Research_Entity.py"
    )
    entity_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(entity_module)

    # Import curriculum functions
    spec = importlib.util.spec_from_file_location(
        "write_introduction", script_dir / "2_Write_Introduction.py"
    )
    curriculum_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(curriculum_module)

    # Import visualization functions
    spec = importlib.util.spec_from_file_location(
        "visualizations", script_dir / "3_Introduction_Visualizations.py"
    )
    viz_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(viz_module)

    # Import translation functions
    spec = importlib.util.spec_from_file_location(
        "translations", script_dir / "4_Translate_Introductions.py"
    )
    trans_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(trans_module)

    return domain_module, entity_module, curriculum_module, viz_module, trans_module


# Load the script modules
_domain_mod, _entity_mod, _curriculum_mod, _viz_mod, _trans_mod = _import_script_functions()


###################################################################################
# CONFIGURATION BLOCK - CUSTOMIZE HERE
###################################################################################

# Default values for interactive mode
DEFAULT_DOMAIN = "biochemistry"
DEFAULT_ENTITY = "karl_friston"
DEFAULT_LANGUAGE = "Spanish"


@dataclass
class CurriculumConfig:
    """Configuration for curriculum generation pipeline.

    This configuration block allows easy customization of the entire pipeline
    without modifying the core logic. Adjust these settings to control:
    - Which domains and entities to process
    - Target languages for translation
    - Processing behavior (overwrite, skip existing, etc.)
    - Output directories and API models
    """

    # === DOMAIN SELECTION ===
    # Specify which domains to process from data/config/domains.yaml
    target_domains: List[str] = field(
        default_factory=lambda: [
            "biochemistry",
            "neuroscience",
            "artificial_intelligence",
            "psychology",
        ]
    )
    # "high", "medium", "low", or None for all
    domain_priority_filter: Optional[str] = None
    # "life_sciences", "technology", etc., or None for all
    domain_category_filter: Optional[str] = None

    # === ENTITY SELECTION ===
    # Specify which entities/audiences to process from data/config/entities.yaml
    target_entities: List[str] = field(
        default_factory=lambda: [
            "karl_friston",
            "tulsi_gabbard",
        ]
    )
    # "high", "medium", "low", or None for all
    entity_priority_filter: Optional[str] = None

    # === LANGUAGE SELECTION ===
    # Specify target languages for translation
    # (must exist in data/config/languages.yaml)
    target_languages: List[str] = field(
        default_factory=lambda: [
            "Spanish",
            "French",
            "Chinese",
            "Arabic",
        ]
    )

    # === PROCESSING OPTIONS ===
    # Skip domains/entities with existing research files
    skip_existing_research: bool = True
    # Skip if curriculum already exists
    skip_existing_curricula: bool = True
    # Skip if translation already exists
    skip_existing_translations: bool = True
    # Always regenerate visualizations
    overwrite_visualizations: bool = True

    # === PIPELINE CONTROL ===
    # Control which stages of the pipeline to run
    run_domain_research: bool = True
    run_entity_research: bool = True
    run_curriculum_generation: bool = True
    run_visualizations: bool = True
    run_translations: bool = True

    # === OUTPUT DIRECTORIES ===
    # Leave None to use default data/ directories
    custom_output_dir: Optional[Path] = None
    domain_research_dir: Optional[Path] = None
    entity_research_dir: Optional[Path] = None
    curriculum_output_dir: Optional[Path] = None
    visualization_output_dir: Optional[Path] = None
    translation_output_dir: Optional[Path] = None

    # === API CONFIGURATION ===
    # Override default models (or set via environment variables)
    # For research tasks
    perplexity_model: Optional[str] = None
    # For content generation and translation
    openrouter_model: Optional[str] = None

    # === PERFORMANCE OPTIONS ===
    # Limit concurrent API requests
    max_concurrent_requests: int = 3
    # Seconds delay between API calls
    delay_between_requests: float = 1.0
    # Number of retries for failed requests
    retry_attempts: int = 3

    # === LOGGING OPTIONS ===
    # Enable detailed progress logging
    verbose_logging: bool = True
    # Log individual API requests (for debugging)
    log_api_calls: bool = False
    # Save results after each stage
    save_intermediate_results: bool = True


###################################################################################
# ORCHESTRATOR IMPLEMENTATION
###################################################################################


class CurriculumOrchestrator:
    """Main orchestrator for the curriculum generation pipeline."""

    def __init__(self, config: CurriculumConfig):
        """Initialize the orchestrator with configuration.

        Args:
            config: Configuration object controlling pipeline behavior
        """
        self.config = config
        self.logger = common_setup_logging()
        self.results = {
            "domain_research": {"success": 0, "failed": 0, "skipped": 0},
            "entity_research": {"success": 0, "failed": 0, "skipped": 0},
            "curriculum_generation": {"success": 0, "failed": 0},
            "visualizations": {"success": False, "error": None},
            "translations": {"success": 0, "failed": 0},
        }

    def setup_directories(self) -> None:
        """Create output directories if they don't exist."""
        directories = [
            self.config.domain_research_dir or data_domain_research_dir(),
            self.config.entity_research_dir or data_audience_research_dir(),
            self.config.curriculum_output_dir or data_written_curriculums_dir(),
            self.config.visualization_output_dir or data_visualizations_dir(),
            self.config.translation_output_dir or data_translated_curriculums_dir(),
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def validate_inputs(self) -> bool:
        """Validate that required input files and configurations exist.

        Returns:
            True if all required inputs are available, False otherwise
        """
        # Check FEP-ActInf base file exists - use synthetic knowledge file
        fep_file = project_root / "data" / "domain_research" / "Synthetic_FEP-ActInf.md"
        if not fep_file.exists():
            self.logger.error(f"Required FEP-ActInf file not found: {fep_file}")
            return False

        # Validate domain configuration
        try:
            domains_config = _domain_mod.load_domains_config()
            available_domains = [d["name"] for d in domains_config.get("domains", [])]
            invalid_domains = [d for d in self.config.target_domains if d not in available_domains]
            if invalid_domains:
                self.logger.warning(f"Invalid domains specified: {invalid_domains}")
                self.logger.info(f"Available domains: {available_domains}")
        except Exception as e:
            self.logger.error(f"Failed to load domains configuration: {e}")
            return False

        # Validate entity configuration
        try:
            entities_config = _entity_mod.load_entities_config()
            available_entities = [e["name"] for e in entities_config.get("entities", [])]
            invalid_entities = [
                e for e in self.config.target_entities if e not in available_entities
            ]
            if invalid_entities:
                self.logger.warning(f"Invalid entities specified: {invalid_entities}")
                self.logger.info(f"Available entities: {available_entities}")
        except Exception as e:
            self.logger.error(f"Failed to load entities configuration: {e}")
            return False

        # Validate language configuration
        try:
            available_languages = get_target_languages()
            valid_languages = _trans_mod.validate_languages(
                self.config.target_languages, available_languages
            )
            if len(valid_languages) != len(self.config.target_languages):
                self.logger.warning("Some target languages are not available")
                self.config.target_languages = valid_languages
        except Exception as e:
            self.logger.error(f"Failed to load language configuration: {e}")
            return False

        return True

    def run_domain_research_stage(self) -> bool:
        """Execute domain research stage of the pipeline.

        Returns:
            True if stage completed successfully, False otherwise
        """
        if not self.config.run_domain_research:
            self.logger.info("Skipping domain research stage (disabled in config)")
            return True

        self.logger.info("=== STARTING DOMAIN RESEARCH STAGE ===")

        try:
            # Load configuration and get domains to process
            domains_config = _domain_mod.load_domains_config()
            domains_to_process = _domain_mod.get_domains_to_process(
                domains_config,
                self.config.domain_priority_filter,
                self.config.domain_category_filter,
            )

            # Filter to only target domains if specified, and add custom domains
            if self.config.target_domains:
                existing_domains = [
                    d for d in domains_to_process if d.get("name") in self.config.target_domains
                ]

                # Add custom domains that don't exist in config
                config_domain_names = [d.get("name") for d in domains_to_process]
                for domain_name in self.config.target_domains:
                    if domain_name not in config_domain_names:
                        # Create a custom domain entry
                        custom_domain = {
                            "name": domain_name,
                            "description": f"Custom domain: {domain_name}",
                            "category": "custom",
                            "keywords": [],
                            "priority": "medium",
                        }
                        existing_domains.append(custom_domain)
                        self.logger.info(f"Added custom domain: {domain_name}")

                domains_to_process = existing_domains

            if not domains_to_process:
                self.logger.warning("No domains found to process")
                return True

            self.logger.info(f"Processing {len(domains_to_process)} domains")

            # Initialize Perplexity client for research
            client = build_perplexity_client()
            output_dir = self.config.domain_research_dir or data_domain_research_dir()
            fep_file = project_root / "data" / "domain_research" / "Synthetic_FEP-ActInf.md"

            # Process each domain
            for domain in domains_to_process:
                domain_name = domain.get("name")

                try:
                    # Check if output already exists
                    if (
                        self.config.skip_existing_research
                        and _domain_mod.check_domain_output_exists(domain_name, output_dir)
                    ):
                        self.logger.info(f"Skipping {domain_name}: research already exists")
                        self.results["domain_research"]["skipped"] += 1
                        continue

                    self.logger.info(f"Processing domain: {domain_name}")

                    # Create domain content for analysis
                    domain_content = self._create_domain_content(domain)

                    # Analyze domain
                    analyze_domain(
                        client, domain_content, str(fep_file), str(output_dir), domain_name
                    )
                    self.results["domain_research"]["success"] += 1
                    self.logger.info(f"Successfully processed domain: {domain_name}")

                    # Add delay between requests
                    time.sleep(self.config.delay_between_requests)

                except Exception as e:
                    self.logger.error(f"Failed to process domain {domain_name}: {e}")
                    self.results["domain_research"]["failed"] += 1
                    continue

            return True

        except Exception as e:
            self.logger.error(f"Domain research stage failed: {e}")
            return False

    def run_entity_research_stage(self) -> bool:
        """Execute entity research stage of the pipeline.

        Returns:
            True if stage completed successfully, False otherwise
        """
        if not self.config.run_entity_research:
            self.logger.info("Skipping entity research stage (disabled in config)")
            return True

        self.logger.info("=== STARTING ENTITY RESEARCH STAGE ===")

        try:
            # Load configuration and get entities to process
            entities_config = _entity_mod.load_entities_config()
            entities_to_process = _entity_mod.get_entities_to_process(
                entities_config, self.config.entity_priority_filter
            )

            # Filter to only target entities if specified, and add custom entities
            if self.config.target_entities:
                existing_entities = [
                    e for e in entities_to_process if e.get("name") in self.config.target_entities
                ]

                # Add custom entities that don't exist in config
                config_entity_names = [e.get("name") for e in entities_to_process]
                for entity_name in self.config.target_entities:
                    if entity_name not in config_entity_names:
                        # Create a custom entity entry
                        entity_description = (
                            getattr(self.config, "_custom_entity_description", "")
                            or f"Custom target audience: {entity_name}"
                        )
                        custom_entity = {
                            "name": entity_name,
                            "description": entity_description,
                            "category": "custom",
                            "priority": "medium",
                        }
                        existing_entities.append(custom_entity)
                        self.logger.info(f"Added custom entity: {entity_name}")

                entities_to_process = existing_entities

            if not entities_to_process:
                self.logger.warning("No entities found to process")
                return True

            self.logger.info(f"Processing {len(entities_to_process)} entities")

            # Initialize Perplexity client for research
            client = build_perplexity_client()
            output_dir = self.config.entity_research_dir or data_audience_research_dir()
            fep_file = project_root / "data" / "domain_research" / "Synthetic_FEP-ActInf.md"

            # Process each entity
            for entity in entities_to_process:
                entity_name = entity.get("name")

                try:
                    # Check if output already exists
                    if self.config.skip_existing_research and _entity_mod.check_output_exists(
                        entity_name, output_dir
                    ):
                        self.logger.info(f"Skipping {entity_name}: research already exists")
                        self.results["entity_research"]["skipped"] += 1
                        continue

                    self.logger.info(f"Processing entity: {entity_name}")

                    # Create entity data for research - include entity name
                    entity_data = (
                        f"Entity Name: {entity_name}\n"
                        f"Description: {entity.get('description', '')}\n"
                        f"Category: {entity.get('category', 'unknown')}"
                    )

                    # Research entity
                    research_target_audience(
                        client, entity_data, str(fep_file), str(output_dir), entity_name
                    )
                    self.results["entity_research"]["success"] += 1
                    self.logger.info(f"Successfully processed entity: {entity_name}")

                    # Add delay between requests
                    time.sleep(self.config.delay_between_requests)

                except Exception as e:
                    self.logger.error(f"Failed to process entity {entity_name}: {e}")
                    self.results["entity_research"]["failed"] += 1
                    continue

            return True

        except Exception as e:
            self.logger.error(f"Entity research stage failed: {e}")
            return False

    def run_curriculum_generation_stage(self) -> bool:
        """Execute curriculum generation stage of the pipeline.

        Returns:
            True if stage completed successfully, False otherwise
        """
        if not self.config.run_curriculum_generation:
            self.logger.info("Skipping curriculum generation stage (disabled in config)")
            return True

        self.logger.info("=== STARTING CURRICULUM GENERATION STAGE ===")

        try:
            # Initialize OpenRouter client for content generation
            client = build_openrouter_client()

            # Setup paths
            io_root = inputs_and_outputs_root()
            audience_research_dir = self.config.entity_research_dir or data_audience_research_dir()
            domain_research_dir = self.config.domain_research_dir or data_domain_research_dir()
            fep_actinf_file = project_root / "data" / "domain_research" / "Synthetic_FEP-ActInf.md"
            output_dir = self.config.curriculum_output_dir or data_written_curriculums_dir()

            total_success = 0
            total_error = 0

            # Process audience research files
            if audience_research_dir.exists():
                success, error = _curriculum_mod.process_research_directory(
                    client, audience_research_dir, fep_actinf_file, output_dir, "audience"
                )
                total_success += success
                total_error += error

            # Process domain research files
            if domain_research_dir.exists():
                success, error = _curriculum_mod.process_research_directory(
                    client, domain_research_dir, fep_actinf_file, output_dir, "domain"
                )
                total_success += success
                total_error += error

            self.results["curriculum_generation"]["success"] = total_success
            self.results["curriculum_generation"]["failed"] = total_error

            self.logger.info(
                f"Curriculum generation completed: {total_success} successful, {total_error} failed"
            )
            return True

        except Exception as e:
            self.logger.error(f"Curriculum generation stage failed: {e}")
            return False

    def run_visualization_stage(self) -> bool:
        """Execute visualization generation stage of the pipeline.

        Returns:
            True if stage completed successfully, False otherwise
        """
        if not self.config.run_visualizations:
            self.logger.info("Skipping visualization stage (disabled in config)")
            return True

        self.logger.info("=== STARTING VISUALIZATION STAGE ===")

        try:
            input_dir = self.config.curriculum_output_dir or data_written_curriculums_dir()
            output_dir = self.config.visualization_output_dir or data_visualizations_dir()

            _viz_mod.main(str(input_dir), str(output_dir))

            self.results["visualizations"]["success"] = True
            self.logger.info("Visualization generation completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Visualization stage failed: {e}")
            self.results["visualizations"]["error"] = str(e)
            return False

    def run_translation_stage(self) -> bool:
        """Execute translation stage of the pipeline.

        Returns:
            True if stage completed successfully, False otherwise
        """
        if not self.config.run_translations:
            self.logger.info("Skipping translation stage (disabled in config)")
            return True

        self.logger.info("=== STARTING TRANSLATION STAGE ===")

        try:
            # Initialize OpenRouter client for translation
            client = build_openrouter_client()

            input_dir = self.config.curriculum_output_dir or data_written_curriculums_dir()
            output_dir = self.config.translation_output_dir or data_translated_curriculums_dir()

            # Process translations
            success_count, failed_count = process_translations(
                client, str(input_dir), str(output_dir), self.config.target_languages
            )

            self.results["translations"]["success"] = success_count
            self.results["translations"]["failed"] = failed_count

            self.logger.info(
                f"Translation completed: {success_count} successful, {failed_count} failed"
            )
            return True

        except Exception as e:
            self.logger.error(f"Translation stage failed: {e}")
            return False

    def _create_domain_content(self, domain: Dict[str, Any]) -> str:
        """Create formatted domain content for analysis.

        Args:
            domain: Domain configuration dictionary

        Returns:
            Formatted domain content string
        """
        domain_name = domain.get("name", "Unknown")
        domain_description = domain.get("description", "")
        domain_keywords = ", ".join(domain.get("keywords", []))

        return f"""# {domain_name.title()} Domain

## Description
{domain_description}

## Category
{domain.get('category', 'unknown')}

## Keywords
{domain_keywords}

## Priority
{domain.get('priority', 'medium')}

This domain will be analyzed for Active Inference curriculum development targeting 
professionals in this field.
"""

    def run_complete_pipeline(self) -> bool:
        """Execute the complete curriculum generation pipeline.

        Returns:
            True if pipeline completed successfully, False otherwise
        """
        self.logger.info("🚀 Starting Complete Active Inference Curriculum Generation Pipeline")
        self.logger.info(f"Target domains: {self.config.target_domains}")
        self.logger.info(f"Target entities: {self.config.target_entities}")
        self.logger.info(f"Target languages: {self.config.target_languages}")

        start_time = time.time()

        # Setup and validation
        if not self.validate_inputs():
            self.logger.error("Input validation failed")
            return False

        self.setup_directories()

        # Execute pipeline stages
        stages = [
            ("Domain Research", self.run_domain_research_stage),
            ("Entity Research", self.run_entity_research_stage),
            ("Curriculum Generation", self.run_curriculum_generation_stage),
            ("Visualization", self.run_visualization_stage),
            ("Translation", self.run_translation_stage),
        ]

        failed_stages = []
        for stage_name, stage_func in stages:
            try:
                self.logger.info(f"\n{'='*60}")
                self.logger.info(f"EXECUTING STAGE: {stage_name}")
                self.logger.info(f"{'='*60}")

                if not stage_func():
                    failed_stages.append(stage_name)
                    self.logger.error(f"❌ Stage failed: {stage_name}")
                else:
                    self.logger.info(f"✅ Stage completed: {stage_name}")

            except Exception as e:
                failed_stages.append(stage_name)
                self.logger.error(f"❌ Stage error: {stage_name} - {e}")

        # Final results
        duration = time.time() - start_time
        self.logger.info(f"\n{'='*60}")
        self.logger.info("🏁 PIPELINE EXECUTION COMPLETE")
        self.logger.info(f"{'='*60}")
        self.logger.info(f"Total execution time: {duration:.2f} seconds")
        self.logger.info(f"Failed stages: {failed_stages if failed_stages else 'None'}")

        # Detailed results
        self.logger.info("\n📊 DETAILED RESULTS:")
        for stage, results in self.results.items():
            if isinstance(results, dict) and "success" in results:
                if stage == "visualizations":
                    status = (
                        "✅ Success"
                        if results["success"]
                        else f"❌ Failed: {results.get('error', 'Unknown error')}"
                    )
                    self.logger.info(f"  {stage.replace('_', ' ').title()}: {status}")
                else:
                    self.logger.info(
                        f"  {stage.replace('_', ' ').title()}: "
                        f"{results.get('success', 0)} successful, "
                        f"{results.get('failed', 0)} failed, "
                        f"{results.get('skipped', 0)} skipped"
                    )

        return len(failed_stages) == 0


def get_interactive_inputs() -> tuple[str, str, str, str]:
    """Get user inputs interactively with default values.

    Returns:
        Tuple of (domain, entity, language, entity_description) selected by user
    """
    print("🎯 Active Inference Curriculum Generator")
    print("=" * 50)
    print("Press Enter to use default values, or type your custom choice.")
    print()

    # Load available options
    try:
        domains_config = _domain_mod.load_domains_config()
        available_domains = [d["name"] for d in domains_config.get("domains", [])]
    except Exception:
        available_domains = [
            "biochemistry",
            "neuroscience",
            "artificial_intelligence",
            "psychology",
        ]

    try:
        entities_config = _entity_mod.load_entities_config()
        available_entities = [e["name"] for e in entities_config.get("entities", [])]
    except Exception:
        available_entities = ["karl_friston", "tulsi_gabbard", "elon_musk"]

    try:
        available_languages = get_target_languages()
    except Exception:
        available_languages = ["Spanish", "French", "Chinese", "Arabic", "Hindi"]

    # Get domain input with validation and option to create new
    print(f"📚 Select Domain (default: {DEFAULT_DOMAIN})")
    print(
        f"Available domains: {', '.join(available_domains[:5])}{'...' if len(available_domains) > 5 else ''}"
    )
    print("💡 Tip: You can also enter a new domain name to create a custom domain!")

    while True:
        domain_input = input(f"Domain [{DEFAULT_DOMAIN}]: ").strip()
        domain = domain_input if domain_input else DEFAULT_DOMAIN

        if domain in available_domains:
            break
        else:
            # Ask if user wants to create a new domain
            print(f"🆕 '{domain}' is not in the existing domains.")
            create_new = input("Create this as a new custom domain? [y/N]: ").strip().lower()
            if create_new in ["y", "yes"]:
                print(f"✅ Created custom domain: '{domain}'")
                break
            else:
                print(f"Please choose from existing domains: {', '.join(available_domains)}")
                continue

    # Get entity input with validation and option to create new
    print(f"\n👤 Select Target Entity (default: {DEFAULT_ENTITY})")
    print(
        f"Available entities: {', '.join(available_entities[:5])}{'...' if len(available_entities) > 5 else ''}"
    )
    print("💡 Tip: You can also enter a new entity name to create a custom target audience!")

    entity_description = ""  # Track custom description
    while True:
        entity_input = input(f"Entity [{DEFAULT_ENTITY}]: ").strip()
        entity = entity_input if entity_input else DEFAULT_ENTITY

        if entity in available_entities:
            break
        else:
            # Ask if user wants to create a new entity
            print(f"🆕 '{entity}' is not in the existing entities.")
            create_new = input("Create this as a new custom entity? [y/N]: ").strip().lower()
            if create_new in ["y", "yes"]:
                # Ask for a brief description of the new entity
                entity_description = input(f"Enter a brief description for '{entity}': ").strip()
                if not entity_description:
                    entity_description = f"Custom target audience: {entity}"
                print(f"✅ Created custom entity: '{entity}' - {entity_description}")
                break
            else:
                print(f"Please choose from existing entities: {', '.join(available_entities)}")
                continue

    # Get language input with validation and option to create new
    print(f"\n🌍 Select Target Language (default: {DEFAULT_LANGUAGE})")
    print(
        f"Available languages: {', '.join(available_languages[:5])}{'...' if len(available_languages) > 5 else ''}"
    )
    print("💡 Tip: You can also enter a new language name to create a custom translation target!")

    while True:
        language_input = input(f"Language [{DEFAULT_LANGUAGE}]: ").strip()
        language = language_input if language_input else DEFAULT_LANGUAGE

        if language in available_languages:
            break
        else:
            # Ask if user wants to create a new language
            print(f"🆕 '{language}' is not in the existing languages.")
            create_new = input("Create this as a new custom language? [y/N]: ").strip().lower()
            if create_new in ["y", "yes"]:
                print(f"✅ Created custom language: '{language}'")
                print(
                    "🔤 Note: Translation quality may vary for custom languages not in the AI model's training."
                )
                break
            else:
                print(f"Please choose from existing languages: {', '.join(available_languages)}")
                continue

    print("\n✅ Selected Configuration:")
    print(f"   Domain: {domain}")
    print(f"   Entity: {entity}")
    print(f"   Language: {language}")

    # Show any custom entries
    if entity_description and entity not in available_entities:
        print(f"   📝 Custom Entity Description: {entity_description}")
    if domain not in available_domains:
        print("   🆕 This is a custom domain")
    if language not in available_languages:
        print("   🆕 This is a custom language")

    # Confirm with user
    confirm = input("\nProceed with this configuration? [Y/n]: ").strip().lower()
    if confirm and confirm not in ["y", "yes"]:
        print("❌ Configuration cancelled.")
        sys.exit(0)

    return domain, entity, language, entity_description


def create_default_config() -> CurriculumConfig:
    """Create a default configuration for the pipeline.

    Returns:
        Default configuration object
    """
    return CurriculumConfig()


def create_interactive_config() -> CurriculumConfig:
    """Create configuration based on interactive user input.

    Returns:
        Configuration object based on user selections
    """
    domain, entity, language, entity_description = get_interactive_inputs()

    config = CurriculumConfig(
        target_domains=[domain],
        target_entities=[entity],
        target_languages=[language],
        skip_existing_research=False,  # Usually want fresh research for interactive runs
        skip_existing_curricula=False,
        skip_existing_translations=False,
        verbose_logging=True,
    )

    # Store custom entity description for later use if needed
    if entity_description:
        config._custom_entity_description = entity_description

    return config


def main():
    """Main function to run the curriculum generation orchestrator.

    This function:
    1. Parses command line arguments
    2. Creates configuration object (interactive or command-line)
    3. Initializes and runs the orchestrator
    4. Reports final results
    """
    parser = argparse.ArgumentParser(
        description="Comprehensive Active Inference curriculum generation orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run interactively (default behavior)
  python generate_custom_curriculum.py
  
  # Force interactive mode
  python generate_custom_curriculum.py --interactive
  
  # Run only specific stages with command line args
  python generate_custom_curriculum.py --stages research curriculum
  
  # Customize domains and entities via command line
  python generate_custom_curriculum.py --domains biochemistry neuroscience --entities karl_friston
  
  # Custom languages for translation
  python generate_custom_curriculum.py --languages Spanish French Chinese
  
  # Use custom output directory
  python generate_custom_curriculum.py --output-dir /path/to/custom/output
        """,
    )

    # Mode selection
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Force interactive mode (default if no other args provided)",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Force non-interactive mode with default config",
    )

    # Configuration overrides
    parser.add_argument("--domains", nargs="+", help="Target domains to process")
    parser.add_argument("--entities", nargs="+", help="Target entities to process")
    parser.add_argument("--languages", nargs="+", help="Target languages for translation")
    parser.add_argument("--output-dir", type=Path, help="Custom output directory")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    parser.add_argument("--skip-existing", action="store_true", help="Skip existing files")

    # Stage selection
    parser.add_argument(
        "--stages",
        nargs="+",
        choices=[
            "domain-research",
            "entity-research",
            "curriculum",
            "visualizations",
            "translations",
        ],
        help="Run only specific pipeline stages",
    )

    # Performance options
    parser.add_argument("--max-concurrent", type=int, default=3, help="Max concurrent API requests")
    parser.add_argument(
        "--delay", type=float, default=1.0, help="Delay between API requests (seconds)"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Determine if we should run interactively
    # Run interactively if:
    # 1. --interactive flag is used, OR
    # 2. No significant arguments are provided (just script name), OR
    # 3. Only --verbose or minimal args are provided
    non_mode_args = [
        args.domains,
        args.entities,
        args.languages,
        args.output_dir,
        args.overwrite,
        args.skip_existing,
        args.stages,
    ]
    has_config_args = any(arg for arg in non_mode_args)

    should_run_interactive = args.interactive or (not args.non_interactive and not has_config_args)

    # Create configuration
    if should_run_interactive:
        print("\n🎯 Running in Interactive Mode")
        print("=" * 40)
        config = create_interactive_config()
    else:
        print("\n⚙️  Running in Command-Line Mode")
        print("=" * 40)
        config = create_default_config()

        # Apply command line overrides
        if args.domains:
            config.target_domains = args.domains
        if args.entities:
            config.target_entities = args.entities
        if args.languages:
            config.target_languages = args.languages
        if args.output_dir:
            config.custom_output_dir = args.output_dir
        if args.overwrite:
            config.skip_existing_research = False
            config.skip_existing_curricula = False
            config.skip_existing_translations = False
        if args.skip_existing:
            config.skip_existing_research = True
            config.skip_existing_curricula = True
            config.skip_existing_translations = True
        if args.max_concurrent:
            config.max_concurrent_requests = args.max_concurrent
        if args.delay:
            config.delay_between_requests = args.delay
        if args.verbose:
            config.verbose_logging = True

        # Configure stages to run
        if args.stages:
            config.run_domain_research = "domain-research" in args.stages
            config.run_entity_research = "entity-research" in args.stages
            config.run_curriculum_generation = "curriculum" in args.stages
            config.run_visualizations = "visualizations" in args.stages
            config.run_translations = "translations" in args.stages

    # Run orchestrator
    orchestrator = CurriculumOrchestrator(config)
    success = orchestrator.run_complete_pipeline()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
