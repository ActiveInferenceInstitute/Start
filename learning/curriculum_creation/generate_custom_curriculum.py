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
import json
import math
import os
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# Resolve repository-owned data and prompt paths from the installed package root.
project_root = Path(__file__).resolve().parents[2]

from src.common.logging_utils import redact_log_value  # noqa: E402
from src.common.logging_utils import setup_logging as common_setup_logging  # noqa: E402
from src.common.paths import (  # noqa: E402
    data_audience_research_dir,
    data_domain_research_dir,
    data_translated_curriculums_dir,
    data_visualizations_dir,
    data_written_curriculums_dir,
)
from src.common.prompts import list_prompt_templates  # noqa: E402
from src.config.catalog import (  # noqa: E402
    domains_to_process,
    entities_to_process,
    load_domains_config,
    load_entities_config,
    output_exists,
)
from src.config.languages import get_target_languages  # noqa: E402
from src.config.schemas import (  # noqa: E402
    stable_identifier,
    validate_domains_config,
    validate_entities_config,
)
from src.perplexity.clients import (  # noqa: E402
    OpenRouterConfig,
    PerplexityConfig,
    RequestLimiter,
    build_openrouter_client,
    build_perplexity_client,
)
from src.perplexity.domain import analyze_domain  # noqa: E402
from src.perplexity.entity import research_target_audience  # noqa: E402
from src.perplexity.translation import process_translations_detailed  # noqa: E402
from src.pipeline import (  # noqa: E402
    PipelineResult,
    PipelineRunner,
    StageItemResult,
    StageResult,
    StageSpec,
    StageStatus,
    parse_visualization_response,
)
from src.pipeline.artifacts import sha256_file  # noqa: E402
from src.pipeline.stages import (  # noqa: E402
    process_research_directory_detailed,
)
from src.visualization.runner import run as run_visualizations  # noqa: E402

###################################################################################
# CONFIGURATION BLOCK - CUSTOMIZE HERE
###################################################################################


def _configured_domains() -> list[str]:
    return [item["name"] for item in load_domains_config().get("domains", [])]


def _configured_entities() -> list[str]:
    return [item["name"] for item in load_entities_config().get("entities", [])]


def _configured_languages() -> list[str]:
    return list(get_target_languages())


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
    target_domains: List[str] = field(default_factory=_configured_domains)
    # "high", "medium", "low", or None for all
    domain_priority_filter: Optional[str] = None
    # "life_sciences", "technology", etc., or None for all
    domain_category_filter: Optional[str] = None

    # === ENTITY SELECTION ===
    # Specify which entities/audiences to process from data/config/entities.yaml
    target_entities: List[str] = field(default_factory=_configured_entities)
    # "high", "medium", "low", or None for all
    entity_priority_filter: Optional[str] = None

    # === LANGUAGE SELECTION ===
    # Specify target languages for translation
    # (must exist in data/config/languages.yaml)
    target_languages: List[str] = field(default_factory=_configured_languages)

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
    custom_entity_description: Optional[str] = None

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
    provider_timeout_seconds: float = 120.0
    translation_max_chunk_size: int = 4000

    # === LOGGING OPTIONS ===
    # Enable detailed progress logging
    verbose_logging: bool = True
    # Log individual API requests (for debugging)
    log_api_calls: bool = False
    # Save results after each stage
    save_intermediate_results: bool = True

    # === RELEASE CONTROLS ===
    run_id: Optional[str] = None
    resume: bool = True
    offline: bool = False
    dry_run: bool = False
    estimate_cost: bool = False
    budget_limit_usd: Optional[float] = None
    json_output: bool = False
    publication_mode: bool = False
    cancellation_event: threading.Event | None = field(default=None, repr=False, compare=False)

    def validate(self) -> None:
        """Validate all user-controlled execution settings before any writes."""
        for field_name in ("target_domains", "target_entities", "target_languages"):
            values = getattr(self, field_name)
            if not isinstance(values, list) or any(
                not isinstance(value, str) or not value.strip() for value in values
            ):
                raise ValueError(f"{field_name} must be a list of non-empty strings")
            if len({value.casefold() for value in values}) != len(values):
                raise ValueError(f"{field_name} contains duplicate values")
            if any("/" in value or "\\" in value or value in {".", ".."} for value in values):
                raise ValueError(f"{field_name} contains an unsafe path-like value")
        for name in ("domain_priority_filter", "entity_priority_filter"):
            value = getattr(self, name)
            if value is not None and value not in {"high", "medium", "low"}:
                raise ValueError(f"{name} must be high, medium, low, or null")
        if self.max_concurrent_requests < 1:
            raise ValueError("max_concurrent_requests must be at least one")
        if self.retry_attempts < 1:
            raise ValueError("retry_attempts must be at least one")
        if self.delay_between_requests < 0:
            raise ValueError("delay_between_requests cannot be negative")
        if self.provider_timeout_seconds <= 0:
            raise ValueError("provider_timeout_seconds must be greater than zero")
        if self.translation_max_chunk_size < 1:
            raise ValueError("translation_max_chunk_size must be positive")
        if self.budget_limit_usd is not None and (
            not math.isfinite(self.budget_limit_usd) or self.budget_limit_usd < 0
        ):
            raise ValueError("budget_limit_usd must be a finite non-negative number")
        if self.run_id is not None and (
            not self.run_id.strip() or any(char in self.run_id for char in "\r\n/")
        ):
            raise ValueError("run_id must be a non-empty single-line identifier")
        for name in ("perplexity_model", "openrouter_model"):
            value = getattr(self, name)
            if value is not None and (not value.strip() or any(char in value for char in "\r\n")):
                raise ValueError(f"{name} must be a non-empty single-line model name")
        for path_name in (
            "custom_output_dir",
            "domain_research_dir",
            "entity_research_dir",
            "curriculum_output_dir",
            "visualization_output_dir",
            "translation_output_dir",
        ):
            value = getattr(self, path_name)
            if value is not None:
                path = self._safe_output_path(value, path_name)
                if path.exists() and not path.is_dir():
                    raise ValueError(f"{path_name} is not a directory: {value}")

    @staticmethod
    def _safe_output_path(value: Path | str, field_name: str) -> Path:
        path = Path(value).expanduser().resolve()
        protected = {Path("/").resolve(), Path.home().resolve(), project_root.resolve()}
        if path in protected:
            raise ValueError(f"{field_name} points at a protected directory: {path}")
        return path

    def output_directories(self) -> dict[str, Path]:
        self.validate()
        root = (
            self._safe_output_path(self.custom_output_dir, "custom_output_dir")
            if self.custom_output_dir
            else None
        )
        return {
            "domain_research": self._safe_output_path(
                self.domain_research_dir
                or (root / "domain_research" if root else data_domain_research_dir()),
                "domain_research_dir",
            ),
            "entity_research": self._safe_output_path(
                self.entity_research_dir
                or (root / "audience_research" if root else data_audience_research_dir()),
                "entity_research_dir",
            ),
            "curriculum": self._safe_output_path(
                self.curriculum_output_dir
                or (root / "written_curriculums" if root else data_written_curriculums_dir()),
                "curriculum_output_dir",
            ),
            "visualizations": self._safe_output_path(
                self.visualization_output_dir
                or (root / "visualizations" if root else data_visualizations_dir()),
                "visualization_output_dir",
            ),
            "translations": self._safe_output_path(
                self.translation_output_dir
                or (root / "translated_curriculums" if root else data_translated_curriculums_dir()),
                "translation_output_dir",
            ),
        }


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
            "domain_research": {"success": 0, "failed": 0, "skipped": 0, "items": []},
            "entity_research": {"success": 0, "failed": 0, "skipped": 0, "items": []},
            "curriculum_generation": {"success": 0, "failed": 0, "items": []},
            "visualizations": {"success": False, "error": None},
            "translations": {"success": 0, "failed": 0, "skipped": 0, "items": []},
        }
        self.pipeline_result = PipelineResult()
        self.provider_limiter = RequestLimiter(max_concurrent=self.config.max_concurrent_requests)
        self.cancellation_event = self.config.cancellation_event or threading.Event()

    def setup_directories(self) -> None:
        """Create output directories if they don't exist."""
        for directory in self.config.output_directories().values():
            directory.mkdir(parents=True, exist_ok=True)

    def validate_inputs(self) -> bool:
        """Validate that required input files and configurations exist.

        Returns:
            True if all required inputs are available, False otherwise
        """
        try:
            self.config.validate()
        except ValueError as exc:
            self.logger.error("Invalid pipeline configuration: %s", exc)
            return False

        # Check FEP-ActInf base file exists - use the checked-in reference file
        fep_file = project_root / "data" / "domain_research" / "Synthetic_FEP-ActInf.md"
        if not fep_file.exists():
            self.logger.error(f"Required FEP-ActInf file not found: {fep_file}")
            return False

        # Validate domain configuration
        try:
            domains_config = load_domains_config()
            if self.config.publication_mode:
                validate_domains_config(domains_config, require_provenance=True)
            available_domains = [d["name"] for d in domains_config.get("domains", [])]
            invalid_domains = [d for d in self.config.target_domains if d not in available_domains]
            if invalid_domains:
                if self.config.publication_mode:
                    raise ValueError(
                        "Publication mode does not allow unverified custom domains: "
                        f"{invalid_domains}"
                    )
                self.logger.info("Using custom domains: %s", invalid_domains)
        except Exception as e:
            self.logger.error(f"Failed to load domains configuration: {e}")
            return False

        # Validate entity configuration
        try:
            entities_config = load_entities_config()
            if self.config.publication_mode:
                validate_entities_config(entities_config, require_provenance=True)
            available_entities = [e["name"] for e in entities_config.get("entities", [])]
            invalid_entities = [
                e for e in self.config.target_entities if e not in available_entities
            ]
            if invalid_entities:
                if self.config.publication_mode:
                    raise ValueError(
                        "Publication mode does not allow unverified custom entities: "
                        f"{invalid_entities}"
                    )
                self.logger.info("Using custom entities: %s", invalid_entities)
        except Exception as e:
            self.logger.error(f"Failed to load entities configuration: {e}")
            return False

        # Validate language configuration
        try:
            available_languages = get_target_languages()
            valid_languages = [
                language
                for language in self.config.target_languages
                if language in available_languages
            ]
            if len(valid_languages) != len(self.config.target_languages):
                missing = sorted(set(self.config.target_languages) - set(valid_languages))
                raise ValueError(f"Unsupported target languages: {missing}")
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
        if self.config.offline:
            self.results["domain_research"].setdefault("errors", []).append(
                "offline mode refuses live domain research"
            )
            return False

        self.logger.info("=== STARTING DOMAIN RESEARCH STAGE ===")

        try:
            # Load configuration and get domains to process
            domains_config = load_domains_config()
            domain_entries = domains_to_process(
                domains_config,
                self.config.domain_priority_filter,
                self.config.domain_category_filter,
            )

            # Filter to only target domains if specified, and add custom domains
            if self.config.target_domains:
                existing_domains = [
                    d for d in domain_entries if d.get("name") in self.config.target_domains
                ]

                # Add custom domains that don't exist in config
                config_domain_names = [d.get("name") for d in domain_entries]
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

                domain_entries = existing_domains

            if not domain_entries:
                self.logger.warning("No domains found to process")
                return True

            self.logger.info(f"Processing {len(domain_entries)} domains")

            # Initialize Perplexity client for research using the configured policy.
            client = build_perplexity_client(
                PerplexityConfig(
                    api_key=os.environ["PERPLEXITY_API_KEY"],
                    model=self.config.perplexity_model
                    or os.environ.get("PERPLEXITY_MODEL", "llama-3.1-sonar-small-128k-online"),
                    timeout=self.config.provider_timeout_seconds,
                    max_retries=self.config.retry_attempts,
                    backoff_seconds=self.config.delay_between_requests,
                )
            )
            output_dir = self.config.output_directories()["domain_research"]
            fep_file = project_root / "data" / "domain_research" / "Synthetic_FEP-ActInf.md"

            def process_domain(domain: Dict[str, Any]) -> tuple[str, str, Any | None]:
                domain_name = domain.get("name", "")
                item_id = domain.get("id") or stable_identifier(domain_name)
                if self.config.skip_existing_research and output_exists(
                    output_dir, domain_name, kind="research", stable_id=item_id
                ):
                    return "skipped", item_id, None
                try:
                    result = analyze_domain(
                        client,
                        self._create_domain_content(domain),
                        str(fep_file),
                        str(output_dir),
                        domain_name,
                        self.config.perplexity_model,
                        self.config.retry_attempts,
                        self.config.delay_between_requests,
                        self.config.provider_timeout_seconds,
                        self.config.publication_mode,
                        domain_id=item_id,
                        limiter=self.provider_limiter,
                        cancellation_event=self.cancellation_event,
                    )
                    return "success", item_id, result
                except Exception as exc:
                    self.logger.error("Domain research failed for %s: %s", domain_name, exc)
                    return "failed", f"{item_id}: {exc}", None

            with ThreadPoolExecutor(max_workers=self.config.max_concurrent_requests) as executor:
                outcomes = list(executor.map(process_domain, domain_entries))
            for status, message, details in outcomes:
                self.results["domain_research"][status] += 1
                item_id = message.split(":", 1)[0] if status == "failed" else message
                item = {"item_id": item_id, "status": status}
                if details is not None:
                    item.update(
                        {
                            "output_paths": list(details.output_paths),
                            "provenance": dict(details.metadata),
                            "usage": dict(details.metadata.get("usage", {})),
                        }
                    )
                elif status == "failed":
                    item["errors"] = [message.split(":", 1)[1].strip()]
                self.results["domain_research"]["items"].append(item)
                if status == "failed":
                    self.logger.error("Domain research failed: %s", message)

            return self.results["domain_research"]["failed"] == 0

        except Exception as e:
            self.logger.error(f"Domain research stage failed: {e}")
            self.results["domain_research"].setdefault("errors", []).append(str(e))
            return False

    def run_entity_research_stage(self) -> bool:
        """Execute entity research stage of the pipeline.

        Returns:
            True if stage completed successfully, False otherwise
        """
        if not self.config.run_entity_research:
            self.logger.info("Skipping entity research stage (disabled in config)")
            return True
        if self.config.offline:
            self.results["entity_research"].setdefault("errors", []).append(
                "offline mode refuses live entity research"
            )
            return False

        self.logger.info("=== STARTING ENTITY RESEARCH STAGE ===")

        try:
            # Load configuration and get entities to process
            entities_config = load_entities_config()
            entity_entries = entities_to_process(
                entities_config, self.config.entity_priority_filter
            )

            # Filter to only target entities if specified, and add custom entities
            if self.config.target_entities:
                existing_entities = [
                    e for e in entity_entries if e.get("name") in self.config.target_entities
                ]

                # Add custom entities that don't exist in config
                config_entity_names = [e.get("name") for e in entity_entries]
                for entity_name in self.config.target_entities:
                    if entity_name not in config_entity_names:
                        # Create a custom entity entry
                        entity_description = (
                            self.config.custom_entity_description
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

                entity_entries = existing_entities

            if not entity_entries:
                self.logger.warning("No entities found to process")
                return True

            self.logger.info(f"Processing {len(entity_entries)} entities")

            # Initialize Perplexity client for research using the configured policy.
            client = build_perplexity_client(
                PerplexityConfig(
                    api_key=os.environ["PERPLEXITY_API_KEY"],
                    model=self.config.perplexity_model
                    or os.environ.get("PERPLEXITY_MODEL", "llama-3.1-sonar-small-128k-online"),
                    timeout=self.config.provider_timeout_seconds,
                    max_retries=self.config.retry_attempts,
                    backoff_seconds=self.config.delay_between_requests,
                )
            )
            output_dir = self.config.output_directories()["entity_research"]
            fep_file = project_root / "data" / "domain_research" / "Synthetic_FEP-ActInf.md"

            def process_entity(entity: Dict[str, Any]) -> tuple[str, str, Any | None]:
                entity_name = entity.get("name", "")
                item_id = entity.get("id") or stable_identifier(entity_name)
                if self.config.skip_existing_research and output_exists(
                    output_dir, entity_name, kind="research", stable_id=item_id
                ):
                    return "skipped", item_id, None
                entity_data = (
                    f"Entity Name: {entity_name}\n"
                    f"Description: {entity.get('description', '')}\n"
                    f"Category: {entity.get('category', 'unknown')}"
                )
                try:
                    result = research_target_audience(
                        client,
                        entity_data,
                        str(fep_file),
                        str(output_dir),
                        entity_name,
                        self.config.perplexity_model,
                        self.config.retry_attempts,
                        self.config.delay_between_requests,
                        self.config.provider_timeout_seconds,
                        self.config.publication_mode,
                        entity_id=item_id,
                        limiter=self.provider_limiter,
                        cancellation_event=self.cancellation_event,
                    )
                    return "success", item_id, result
                except Exception as exc:
                    self.logger.error("Entity research failed for %s: %s", entity_name, exc)
                    return "failed", f"{item_id}: {exc}", None

            with ThreadPoolExecutor(max_workers=self.config.max_concurrent_requests) as executor:
                outcomes = list(executor.map(process_entity, entity_entries))
            for status, message, details in outcomes:
                self.results["entity_research"][status] += 1
                item_id = message.split(":", 1)[0] if status == "failed" else message
                item = {"item_id": item_id, "status": status}
                if details is not None:
                    item.update(
                        {
                            "output_paths": list(details.output_paths),
                            "provenance": dict(details.metadata),
                            "usage": dict(details.metadata.get("usage", {})),
                        }
                    )
                elif status == "failed":
                    item["errors"] = [message.split(":", 1)[1].strip()]
                self.results["entity_research"]["items"].append(item)
                if status == "failed":
                    self.logger.error("Entity research failed: %s", message)

            return self.results["entity_research"]["failed"] == 0

        except Exception as e:
            self.logger.error(f"Entity research stage failed: {e}")
            self.results["entity_research"].setdefault("errors", []).append(str(e))
            return False

    def run_curriculum_generation_stage(self) -> bool:
        """Execute curriculum generation stage of the pipeline.

        Returns:
            True if stage completed successfully, False otherwise
        """
        if not self.config.run_curriculum_generation:
            self.logger.info("Skipping curriculum generation stage (disabled in config)")
            return True
        if self.config.offline:
            self.results["curriculum_generation"].setdefault("errors", []).append(
                "offline mode refuses live curriculum generation"
            )
            return False

        self.logger.info("=== STARTING CURRICULUM GENERATION STAGE ===")

        try:
            # Initialize OpenRouter client for content generation.
            client = build_openrouter_client(
                OpenRouterConfig(
                    api_key=os.environ["OPENROUTER_API_KEY"],
                    model=self.config.openrouter_model
                    or os.environ.get("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"),
                    timeout=self.config.provider_timeout_seconds,
                    max_retries=self.config.retry_attempts,
                    backoff_seconds=self.config.delay_between_requests,
                )
            )

            # Setup paths
            output_dirs = self.config.output_directories()
            audience_research_dir = output_dirs["entity_research"]
            domain_research_dir = output_dirs["domain_research"]
            fep_actinf_file = project_root / "data" / "domain_research" / "Synthetic_FEP-ActInf.md"
            output_dir = output_dirs["curriculum"]

            total_success = 0
            total_error = 0

            # Process audience research files
            if audience_research_dir.exists():
                success, error, items = process_research_directory_detailed(
                    client,
                    audience_research_dir,
                    fep_actinf_file,
                    output_dir,
                    "audience",
                    skip_existing=self.config.skip_existing_curricula,
                    max_concurrent=self.config.max_concurrent_requests,
                    model=self.config.openrouter_model,
                    max_retries=self.config.retry_attempts,
                    retry_delay=self.config.delay_between_requests,
                    timeout=self.config.provider_timeout_seconds,
                    delay_seconds=self.config.delay_between_requests,
                    save_intermediate_results=self.config.save_intermediate_results,
                    strict_schema=self.config.publication_mode,
                    limiter=self.provider_limiter,
                    cancellation_event=self.cancellation_event,
                )
                total_success += success
                total_error += error
                self.results["curriculum_generation"].setdefault("items", []).extend(items)

            # Process domain research files
            if domain_research_dir.exists():
                success, error, items = process_research_directory_detailed(
                    client,
                    domain_research_dir,
                    fep_actinf_file,
                    output_dir,
                    "domain",
                    skip_existing=self.config.skip_existing_curricula,
                    max_concurrent=self.config.max_concurrent_requests,
                    model=self.config.openrouter_model,
                    max_retries=self.config.retry_attempts,
                    retry_delay=self.config.delay_between_requests,
                    timeout=self.config.provider_timeout_seconds,
                    delay_seconds=self.config.delay_between_requests,
                    save_intermediate_results=self.config.save_intermediate_results,
                    strict_schema=self.config.publication_mode,
                    limiter=self.provider_limiter,
                    cancellation_event=self.cancellation_event,
                )
                total_success += success
                total_error += error
                self.results["curriculum_generation"].setdefault("items", []).extend(items)

            self.results["curriculum_generation"]["success"] = total_success
            self.results["curriculum_generation"]["failed"] = total_error

            self.logger.info(
                f"Curriculum generation completed: {total_success} successful, {total_error} failed"
            )
            return self.results["curriculum_generation"]["failed"] == 0

        except Exception as e:
            self.logger.error(f"Curriculum generation stage failed: {e}")
            self.results["curriculum_generation"].setdefault("errors", []).append(str(e))
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
            output_dirs = self.config.output_directories()
            input_dir = output_dirs["curriculum"]
            output_dir = output_dirs["visualizations"]
            has_visualization_outputs = output_dir.exists() and any(output_dir.iterdir())
            if not self.config.overwrite_visualizations and has_visualization_outputs:
                self.results["visualizations"]["success"] = True
                self.results["visualizations"]["skipped"] = True
                self.logger.info(
                    "Skipping visualizations because overwrite_visualizations is false"
                )
                return True

            self.results["visualizations"]["output_paths"] = run_visualizations(
                str(input_dir), str(output_dir)
            )
            self.results["visualizations"]["provenance"] = {
                "evidence_status": "derived_visualization",
                "input_root": str(input_dir),
                "inputs": (
                    [
                        {"path": str(path), "sha256": sha256_file(path)}
                        for path in sorted(input_dir.rglob("complete_curriculum_*.md"))
                        if path.is_file() and not path.is_symlink()
                    ]
                    if input_dir.exists()
                    else []
                ),
            }

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
        if self.config.offline:
            self.results["translations"].setdefault("errors", []).append(
                "offline mode refuses live translation"
            )
            return False

        self.logger.info("=== STARTING TRANSLATION STAGE ===")

        try:
            # Initialize OpenRouter client for translation.
            client = build_openrouter_client(
                OpenRouterConfig(
                    api_key=os.environ["OPENROUTER_API_KEY"],
                    model=self.config.openrouter_model
                    or os.environ.get("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"),
                    timeout=self.config.provider_timeout_seconds,
                    max_retries=self.config.retry_attempts,
                    backoff_seconds=self.config.delay_between_requests,
                )
            )

            output_dirs = self.config.output_directories()
            input_dir = output_dirs["curriculum"]
            output_dir = output_dirs["translations"]

            # Process translations
            success_count, failed_count, items = process_translations_detailed(
                client,
                str(input_dir),
                str(output_dir),
                self.config.target_languages,
                model=self.config.openrouter_model,
                max_retries=self.config.retry_attempts,
                retry_delay=self.config.delay_between_requests,
                timeout=self.config.provider_timeout_seconds,
                delay_seconds=self.config.delay_between_requests,
                skip_existing=self.config.skip_existing_translations,
                max_concurrent=self.config.max_concurrent_requests,
                max_chunk_size=self.config.translation_max_chunk_size,
                strict_schema=self.config.publication_mode,
                limiter=self.provider_limiter,
                cancellation_event=self.cancellation_event,
            )

            self.results["translations"]["success"] = success_count
            self.results["translations"]["failed"] = failed_count
            self.results["translations"]["items"] = items

            self.logger.info(
                f"Translation completed: {success_count} successful, {failed_count} failed"
            )
            return self.results["translations"]["failed"] == 0

        except Exception as e:
            self.logger.error(f"Translation stage failed: {e}")
            self.results["translations"].setdefault("errors", []).append(str(e))
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

    def _stage_result(self, name: str, result_key: str, required: bool) -> StageResult:
        """Normalize stage counters into stable item-level contracts."""

        data = self.results[result_key]
        items: dict[str, StageItemResult] = {}
        raw_items = data.get("items", [])
        for raw_item in raw_items:
            if isinstance(raw_item, dict):
                item_id = str(raw_item.get("item_id", ""))
                status = raw_item.get("status", "succeeded")
                message = str(raw_item.get("message", ""))
                output_paths = [str(path) for path in raw_item.get("output_paths", [])]
                input_hashes = dict(raw_item.get("input_hashes", {}))
                artifact_hashes = dict(raw_item.get("artifact_hashes", {}))
                if not artifact_hashes:
                    artifact_hashes = {
                        path: sha256_file(path)
                        for path in output_paths
                        if Path(path).is_file() and not Path(path).is_symlink()
                    }
                provenance = dict(raw_item.get("provenance", {}))
                usage = dict(raw_item.get("usage", {}))
                raw_errors = raw_item.get("errors", [])
                item_errors = (
                    [str(error) for error in raw_errors] if isinstance(raw_errors, list) else []
                )
            else:
                item_id = str(raw_item)
                status = "succeeded"
                message = ""
                output_paths = []
                input_hashes = {}
                artifact_hashes = {}
                provenance = {}
                usage = {}
                item_errors = []
            if not item_id:
                continue
            status_value = {
                "success": StageStatus.SUCCEEDED,
                "skipped": StageStatus.SKIPPED,
                "failed": StageStatus.FAILED,
            }.get(str(status), status)
            errors = item_errors or (
                [] if status_value != StageStatus.FAILED else [message or "item failed"]
            )
            items[item_id] = StageItemResult(
                item_id,
                status_value,
                message=message,
                output_paths=output_paths,
                input_hashes=input_hashes,
                artifact_hashes=artifact_hashes,
                provenance=provenance,
                errors=errors,
                usage=usage,
            )
        errors = list(data.get("errors", []))
        if data.get("error"):
            errors.append(str(data["error"]))
        if data.get("failed") and not items:
            errors.append("stage reported failures without item diagnostics")
        stage_ok = not errors and int(data.get("failed", 0)) == 0
        if result_key == "visualizations":
            planning = self.config.dry_run or self.config.estimate_cost
            visualization = parse_visualization_response(
                data.get("output_paths", []),
                require_output=self.config.run_visualizations and not planning,
                require_manifest=self.config.run_visualizations and not planning,
            )
            data["quality"] = visualization.quality.as_dict()
            if self.config.run_visualizations and not planning and not visualization.quality.valid:
                errors.extend(visualization.quality.errors)
            stage_ok = (
                True
                if planning or not self.config.run_visualizations
                else stage_ok and bool(data.get("success")) and visualization.quality.valid
            )
        provenance = dict(data.get("provenance", {}))
        if data.get("quality") is not None:
            provenance["quality"] = data["quality"]
        return StageResult(
            name=name,
            status=(
                StageStatus.SKIPPED
                if result_key == "visualizations"
                and (
                    not self.config.run_visualizations
                    or self.config.dry_run
                    or self.config.estimate_cost
                )
                else StageStatus.SUCCEEDED if stage_ok else StageStatus.FAILED
            ),
            required=required,
            items=items,
            errors=errors,
            output_paths=list(data.get("output_paths", [])),
            provenance=provenance,
            usage=dict(data.get("usage", {})),
        )

    def _planned_stage(self, name: str, result_key: str, required: bool) -> StageResult:
        data = self.results[result_key]
        data["items"] = [
            {"item_id": f"{result_key}:{stable_identifier(item_id)}", "status": "skipped"}
            for item_id in self.config.target_domains + self.config.target_entities
        ]
        return StageResult(
            name=name,
            status=StageStatus.SKIPPED,
            required=required,
            items={
                item["item_id"]: StageItemResult(item["item_id"], StageStatus.SKIPPED)
                for item in data["items"]
            },
            provenance={"mode": "dry-run", "estimate_cost": self.config.estimate_cost},
        )

    def _estimate_cost_usd(self) -> float:
        """Return a conservative preflight estimate without contacting providers."""

        research_requests = (len(self.config.target_domains) * 2) + len(self.config.target_entities)
        output_dirs = self.config.output_directories()
        research_files = sum(
            len(list(output_dirs[key].glob("*_research_*.md")))
            for key in ("domain_research", "entity_research")
        )
        translation_requests = max(1, research_files) * len(self.config.target_languages)
        request_count = research_requests + research_files + translation_requests
        # Planning assumption: 1.5k input and 2.5k output tokens at $1/M and
        # $4/M respectively. The manifest labels this as an estimate.
        return round(request_count * ((1500 * 1.0 + 2500 * 4.0) / 1_000_000), 6)

    def _preflight_failure(
        self,
        run_id: str,
        stage_name: str,
        message: str,
        usage: dict[str, Any] | None = None,
    ) -> PipelineResult:
        """Persist validation and budget failures as first-class run manifests."""

        try:
            output_root = self.config.output_directories()["curriculum"] / ".runs"
            runner = PipelineRunner(
                [StageSpec(stage_name)],
                work_root=output_root,
                run_id=run_id,
                offline=self.config.offline,
                max_concurrent_requests=self.config.max_concurrent_requests,
                dry_run=self.config.dry_run,
                estimate_cost=self.config.estimate_cost,
                cancellation_event=self.cancellation_event,
                metadata={
                    "project": "START",
                    "preflight_failure": True,
                    "publication_mode": self.config.publication_mode,
                },
            )
            result = runner.run(
                {
                    stage_name: lambda _context: StageResult(
                        stage_name,
                        status=StageStatus.FAILED,
                        errors=[message],
                        usage=usage or {},
                    )
                },
                resume=False,
            )
            result.usage = dict(runner.manifest.usage)
            return result
        except Exception:
            # An invalid output configuration may prevent even the diagnostic
            # manifest from being created; preserve the stable CLI failure
            # contract without leaking the secondary filesystem exception.
            return PipelineResult(
                stages=[StageResult(stage_name, status=StageStatus.FAILED, errors=[message])],
                run_id=run_id,
                usage=usage or {},
            )

    def run_complete_pipeline(self) -> PipelineResult:
        """Execute acquire → prepare → process → parse → render with checkpoints."""

        self.logger.info("Starting Active Inference curriculum pipeline")
        started = time.monotonic()
        run_id = (
            self.config.run_id or f"run-{time.strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:8]}"
        )
        if not self.validate_inputs():
            self.pipeline_result = self._preflight_failure(
                run_id,
                "validation",
                "Input validation failed",
            )
            if self.config.json_output:
                print(
                    json.dumps(self.pipeline_result.as_dict(), ensure_ascii=False, sort_keys=True)
                )
            return self.pipeline_result
        # A planning run may create only its own checkpoint/manifest directory;
        # it must not pre-create or mutate the publishable output trees.
        if not (self.config.dry_run or self.config.estimate_cost):
            self.setup_directories()
        output_dirs = self.config.output_directories()
        estimated_cost = self._estimate_cost_usd()
        if (
            self.config.budget_limit_usd is not None
            and estimated_cost > self.config.budget_limit_usd
        ):
            self.pipeline_result = self._preflight_failure(
                run_id,
                "budget",
                f"estimated cost ${estimated_cost:.6f} exceeds budget "
                f"${self.config.budget_limit_usd:.6f}",
                {
                    "estimated_cost_usd": estimated_cost,
                    "budget_limit_usd": self.config.budget_limit_usd,
                },
            )
            if self.config.json_output:
                print(
                    json.dumps(self.pipeline_result.as_dict(), ensure_ascii=False, sort_keys=True)
                )
            return self.pipeline_result
        runner = PipelineRunner(
            [
                StageSpec(
                    "acquire",
                    required=self.config.run_domain_research or self.config.run_entity_research,
                ),
                StageSpec("prepare", depends_on=("acquire",)),
                StageSpec(
                    "process",
                    depends_on=("prepare",),
                    required=self.config.run_curriculum_generation,
                ),
                StageSpec("parse", depends_on=("process",), required=self.config.run_translations),
                StageSpec("render", depends_on=("parse",), required=self.config.run_visualizations),
            ],
            work_root=output_dirs["curriculum"] / ".runs",
            run_id=run_id,
            offline=self.config.offline,
            max_concurrent_requests=self.config.max_concurrent_requests,
            budget_limit_usd=self.config.budget_limit_usd,
            dry_run=self.config.dry_run,
            estimate_cost=self.config.estimate_cost,
            allowed_output_roots=tuple(output_dirs.values()),
            cancellation_event=self.cancellation_event,
            metadata={
                "project": "START",
                "pipeline": ["acquire", "prepare", "process", "parse", "render"],
                "provider_metadata": {
                    "research": {
                        "provider": "perplexity",
                        "model": self.config.perplexity_model
                        or os.environ.get("PERPLEXITY_MODEL", "llama-3.1-sonar-small-128k-online"),
                    },
                    "content": {
                        "provider": "openrouter",
                        "model": self.config.openrouter_model
                        or os.environ.get("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"),
                    },
                },
                "publication_mode": self.config.publication_mode,
                "prompt_versions": {
                    name: sha256_file(project_root / "data" / "prompts" / f"{name}.md")
                    for name in list_prompt_templates()
                    if (project_root / "data" / "prompts" / f"{name}.md").is_file()
                },
            },
        )
        runner.manifest.usage = {
            "estimated_cost_usd": estimated_cost,
            "requests": 0,
            "budget_limit_usd": self.config.budget_limit_usd,
            "estimate_basis": "1500 input + 2500 output tokens per planned request",
        }

        def handler(name: str, key: str, function: Any, required: bool):
            if self.config.dry_run or self.config.estimate_cost:
                return lambda _context: self._planned_stage(name, key, required)

            def execute(_context: Any) -> StageResult:
                function()
                return self._stage_result(name, key, required)

            return execute

        def acquire() -> bool:
            domain_ok = self.run_domain_research_stage()
            entity_ok = self.run_entity_research_stage()
            entity_data = self.results["entity_research"]
            domain_data = self.results["domain_research"]
            for item in entity_data.get("items", []):
                if isinstance(item, dict):
                    copied = dict(item)
                    copied["item_id"] = f"entity:{item.get('item_id', '')}"
                    domain_data["items"].append(copied)
                else:
                    domain_data["items"].append(
                        {"item_id": f"entity:{item}", "status": "succeeded"}
                    )
            domain_data.setdefault("errors", []).extend(entity_data.get("errors", []))
            domain_data["failed"] = int(domain_data.get("failed", 0)) + int(
                entity_data.get("failed", 0)
            )
            return domain_ok and entity_ok

        handlers = {
            "acquire": handler(
                "acquire",
                "domain_research",
                acquire,
                self.config.run_domain_research or self.config.run_entity_research,
            ),
            "prepare": handler("prepare", "curriculum_generation", lambda: None, True),
            "process": handler(
                "process",
                "curriculum_generation",
                self.run_curriculum_generation_stage,
                self.config.run_curriculum_generation,
            ),
            "parse": handler(
                "parse", "translations", self.run_translation_stage, self.config.run_translations
            ),
            "render": handler(
                "render",
                "visualizations",
                self.run_visualization_stage,
                self.config.run_visualizations,
            ),
        }
        result = runner.run(handlers, resume=self.config.resume, continue_independent=True)
        result.duration_seconds = time.monotonic() - started
        result.manifest_path = str(runner.manifest_path)
        result.usage = dict(runner.manifest.usage)
        # Preserve the historical stage-level public API while the manifest
        # and execution graph use acquire/prepare/process/parse/render.
        result.stages.extend(
            [
                self._stage_result(
                    "domain_research", "domain_research", self.config.run_domain_research
                ),
                self._stage_result(
                    "entity_research", "entity_research", self.config.run_entity_research
                ),
                self._stage_result(
                    "curriculum_generation",
                    "curriculum_generation",
                    self.config.run_curriculum_generation,
                ),
                self._stage_result("translations", "translations", self.config.run_translations),
                self._stage_result(
                    "visualizations", "visualizations", self.config.run_visualizations
                ),
            ]
        )
        self.pipeline_result = result
        if self.config.json_output:
            print(json.dumps(result.as_dict(), ensure_ascii=False, sort_keys=True))
        return result


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
    available_domains = _configured_domains()
    available_entities = _configured_entities()
    available_languages = _configured_languages()
    default_domain = available_domains[0]
    default_entity = available_entities[0]
    default_language = available_languages[0]

    # Get domain input with validation and option to create new
    print(f"📚 Select Domain (default: {default_domain})")
    print(
        f"Available domains: {', '.join(available_domains[:5])}{'...' if len(available_domains) > 5 else ''}"  # noqa: E501
    )
    print("💡 Tip: You can also enter a new domain name to create a custom domain!")

    while True:
        domain_input = input(f"Domain [{default_domain}]: ").strip()
        domain = domain_input if domain_input else default_domain

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
    print(f"\n👤 Select Target Entity (default: {default_entity})")
    print(
        f"Available entities: {', '.join(available_entities[:5])}{'...' if len(available_entities) > 5 else ''}"  # noqa: E501
    )
    print("💡 Tip: You can also enter a new entity name to create a custom target audience!")

    entity_description = ""  # Track custom description
    while True:
        entity_input = input(f"Entity [{default_entity}]: ").strip()
        entity = entity_input if entity_input else default_entity

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
    print(f"\n🌍 Select Target Language (default: {default_language})")
    print(
        f"Available languages: {', '.join(available_languages[:5])}{'...' if len(available_languages) > 5 else ''}"  # noqa: E501
    )
    print("Choose a language from the configured translation targets.")

    while True:
        language_input = input(f"Language [{default_language}]: ").strip()
        language = language_input if language_input else default_language

        if language in available_languages:
            break
        else:
            print(f"Please choose from configured languages: {', '.join(available_languages)}")

    print("\n✅ Selected Configuration:")
    print(f"   Domain: {domain}")
    print(f"   Entity: {entity}")
    print(f"   Language: {language}")

    # Show any custom entries
    if entity_description and entity not in available_entities:
        print(f"   📝 Custom Entity Description: {entity_description}")
    if domain not in available_domains:
        print("   🆕 This is a custom domain")

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

    if entity_description:
        config.custom_entity_description = entity_description

    return config


def _cli_failure(value: object, *, json_output: bool) -> int:
    """Emit one bounded CLI error in either human or machine-readable form."""

    message = redact_log_value(value)
    if json_output:
        print(json.dumps({"ok": False, "errors": [message]}, sort_keys=True))
    else:
        print(f"Error: {message}", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
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
  uv run start-curriculum
  
  # Force interactive mode
  uv run start-curriculum --interactive
  
  # Run only specific stages with command line args
  uv run start-curriculum --stages domain-research curriculum
  
  # Customize domains and entities via command line
  uv run start-curriculum --domains biochemistry neuroscience --entities karl_friston
  
  # Custom languages for translation
  uv run start-curriculum --languages Spanish French Chinese
  
  # Use custom output directory
  uv run start-curriculum --output-dir /path/to/custom/output
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
    parser.add_argument(
        "--domain-research-dir", type=Path, help="Override the domain research output directory"
    )
    parser.add_argument(
        "--entity-research-dir", type=Path, help="Override the entity research output directory"
    )
    parser.add_argument(
        "--curriculum-dir",
        "--curriculum-input",
        dest="curriculum_dir",
        type=Path,
        help="Override the curriculum input/output directory",
    )
    parser.add_argument(
        "--visualizations-dir", type=Path, help="Override the visualization output directory"
    )
    parser.add_argument(
        "--translation-dir", type=Path, help="Override the translation output directory"
    )
    parser.add_argument(
        "--domain-priority",
        "--priority",
        dest="domain_priority",
        choices=["high", "medium", "low"],
        help="Process only domains with this priority",
    )
    parser.add_argument(
        "--domain-category",
        "--category",
        dest="domain_category",
        help="Process only domains in this category",
    )
    parser.add_argument(
        "--entity-priority",
        dest="entity_priority",
        choices=["high", "medium", "low"],
        help="Process only entities with this priority",
    )
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    parser.add_argument("--skip-existing", action="store_true", help="Skip existing files")
    parser.add_argument(
        "--dry-run", action="store_true", help="Validate and plan without provider calls"
    )
    parser.add_argument(
        "--estimate-cost", action="store_true", help="Plan the run and include a cost estimate"
    )
    parser.add_argument("--run-id", help="Stable run identifier for resumable execution")
    parser.add_argument(
        "--resume", action="store_true", help="Resume completed stages for --run-id"
    )
    parser.add_argument(
        "--no-resume", action="store_true", help="Do not reuse a prior run manifest"
    )
    parser.add_argument("--offline", action="store_true", help="Refuse all live provider calls")
    parser.add_argument(
        "--publication",
        action="store_true",
        dest="publication_mode",
        help="Require source URLs and verification dates for configured inputs",
    )
    parser.add_argument("--budget-usd", type=float, help="Maximum estimated provider cost")
    parser.add_argument(
        "--json", action="store_true", dest="json_output", help="Print a JSON summary"
    )

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
    parser.add_argument(
        "--max-concurrent", type=int, default=None, help="Max concurrent API requests"
    )
    parser.add_argument(
        "--delay", type=float, default=None, help="Delay between API requests (seconds)"
    )
    parser.add_argument("--perplexity-model", help="Research provider model name")
    parser.add_argument("--openrouter-model", help="Content provider model name")
    parser.add_argument("--timeout", type=float, help="Provider request timeout in seconds")
    parser.add_argument("--translation-chunk-size", type=int, help="Translation chunk size")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args(argv)

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
        args.domain_research_dir,
        args.entity_research_dir,
        args.curriculum_dir,
        args.visualizations_dir,
        args.translation_dir,
        args.domain_priority,
        args.domain_category,
        args.entity_priority,
        args.overwrite,
        args.skip_existing,
        args.stages,
        args.dry_run,
        args.estimate_cost,
        args.run_id,
        args.offline,
        args.publication_mode,
        args.budget_usd,
        args.json_output,
        args.resume,
        args.no_resume,
        args.max_concurrent,
        args.delay,
        args.perplexity_model,
        args.openrouter_model,
        args.timeout,
        args.translation_chunk_size,
        args.verbose,
    ]
    has_config_args = any(arg not in (None, False, []) for arg in non_mode_args)

    should_run_interactive = args.interactive or (not args.non_interactive and not has_config_args)

    # Create configuration
    if should_run_interactive:
        if not args.json_output:
            print("\n🎯 Running in Interactive Mode")
            print("=" * 40)
        try:
            config = create_interactive_config()
        except Exception as exc:
            return _cli_failure(exc, json_output=args.json_output)
    else:
        if not args.json_output:
            print("\n⚙️  Running in Command-Line Mode")
            print("=" * 40)
        try:
            config = create_default_config()
        except Exception as exc:
            return _cli_failure(exc, json_output=args.json_output)

        # Apply command line overrides
        if args.domains:
            config.target_domains = args.domains
        if args.entities:
            config.target_entities = args.entities
        if args.languages:
            config.target_languages = args.languages
        if args.output_dir:
            config.custom_output_dir = args.output_dir
        if args.domain_research_dir:
            config.domain_research_dir = args.domain_research_dir
        if args.entity_research_dir:
            config.entity_research_dir = args.entity_research_dir
        if args.curriculum_dir:
            config.curriculum_output_dir = args.curriculum_dir
        if args.visualizations_dir:
            config.visualization_output_dir = args.visualizations_dir
        if args.translation_dir:
            config.translation_output_dir = args.translation_dir
        config.domain_priority_filter = args.domain_priority
        config.domain_category_filter = args.domain_category
        config.entity_priority_filter = args.entity_priority
        if args.overwrite:
            config.skip_existing_research = False
            config.skip_existing_curricula = False
            config.skip_existing_translations = False
        if args.skip_existing:
            config.skip_existing_research = True
            config.skip_existing_curricula = True
            config.skip_existing_translations = True
        if args.max_concurrent is not None:
            config.max_concurrent_requests = args.max_concurrent
        if args.delay is not None:
            config.delay_between_requests = args.delay
        if args.perplexity_model:
            config.perplexity_model = args.perplexity_model
        if args.openrouter_model:
            config.openrouter_model = args.openrouter_model
        if args.timeout is not None:
            config.provider_timeout_seconds = args.timeout
        if args.translation_chunk_size is not None:
            config.translation_max_chunk_size = args.translation_chunk_size
        if args.verbose:
            config.verbose_logging = True
        config.dry_run = args.dry_run
        config.estimate_cost = args.estimate_cost
        config.offline = args.offline
        config.publication_mode = args.publication_mode
        config.json_output = args.json_output
        if args.run_id:
            config.run_id = args.run_id
        if args.budget_usd is not None:
            config.budget_limit_usd = args.budget_usd
        if args.no_resume:
            config.resume = False
        elif args.resume:
            config.resume = True

        # Configure stages to run
        if args.stages:
            config.run_domain_research = "domain-research" in args.stages
            config.run_entity_research = "entity-research" in args.stages
            config.run_curriculum_generation = "curriculum" in args.stages
            config.run_visualizations = "visualizations" in args.stages
            config.run_translations = "translations" in args.stages

    # Keep failures machine-readable when --json is used; callers should not
    # have to parse a traceback or a logging formatter.
    try:
        orchestrator = CurriculumOrchestrator(config)
        result = orchestrator.run_complete_pipeline()
    except Exception as exc:
        return _cli_failure(exc, json_output=args.json_output)

    return 0 if bool(result) else 1


if __name__ == "__main__":
    raise SystemExit(main())
