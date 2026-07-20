"""Curriculum generation using OpenRouter for content creation.

This module handles curriculum generation tasks using OpenRouter,
which is optimized for content creation rather than research.
"""

from __future__ import annotations

import json
import os
import re
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from openai import OpenAI

from src.common.io import (
    ensure_directory,
    next_available_bundle,
    next_available_path,
    read_text,
    safe_name,
    write_text,
    write_text_bundle,
)
from src.common.paths import data_written_curriculums_dir
from src.common.prompts import render_prompt
from src.config.schemas import stable_identifier
from src.perplexity.clients import ChatPolicy, CompletionResult, ProviderAdapter, RequestLimiter
from src.pipeline import (
    file_input_record,
    generation_metadata,
    parse_curriculum_response,
    parse_structured_response,
    payload_markdown,
    validate_generated_text,
)

SYSTEM = (
    "You are an expert researcher and educator specializing in creating comprehensive, "
    "high-quality technical content. Your goal is to provide the most thorough, accurate, "
    "and well-structured information possible, with extensive references and "
    "practical applications."
)


def chat_result(
    client: OpenAI,
    prompt: str,
    system: str,
    model: Optional[str] = None,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    timeout: float = 120.0,
    delay_seconds: float = 0.0,
    strict_schema: bool = False,
    limiter: RequestLimiter | None = None,
    cancellation_event: threading.Event | None = None,
) -> CompletionResult:
    """Send chat completion request to OpenRouter for content generation.

    Args:
        client: OpenAI client configured for OpenRouter
        prompt: User prompt for content generation
        system: System prompt defining the AI's role
        model: Optional model override (defaults to OPENROUTER_MODEL)

    Returns:
        Generated content from the model
    """
    return ProviderAdapter(
        client,
        provider="openrouter",
        policy=ChatPolicy(
            model=model or os.environ.get("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"),
            timeout=timeout,
            max_retries=max_retries,
            backoff_seconds=retry_delay,
            min_content_length=20,
            delay_seconds=delay_seconds,
            response_format={"type": "json_object"} if strict_schema else None,
        ),
        limiter=limiter,
        cancellation_event=cancellation_event,
    ).complete([{"role": "system", "content": system}, {"role": "user", "content": prompt}])


def validate_curriculum_content(content: str, min_word_count: int = 100) -> Dict[str, Any]:
    """Validate curriculum content for quality and completeness.

    Args:
        content: Curriculum content to validate
        min_word_count: Minimum word count for content

    Returns:
        Dictionary with validation results
    """
    validation = {"valid": True, "errors": [], "warnings": [], "metrics": {}}

    if not content or not content.strip():
        validation["valid"] = False
        validation["errors"].append("Content is empty")
        return validation

    # Basic metrics
    word_count = len(content.split())
    line_count = len(content.split("\n"))
    section_count = len(re.findall(r"^#+\s+", content, re.MULTILINE))

    validation["metrics"] = {
        "word_count": word_count,
        "line_count": line_count,
        "section_count": section_count,
    }

    # Validate minimum content
    if word_count < min_word_count:
        validation["valid"] = False
        validation["errors"].append(
            f"Content is short ({word_count} words, minimum {min_word_count})"
        )

    # Check for proper structure
    if section_count == 0:
        validation["warnings"].append("No sections found (no headers)")

    # Check for balanced content
    if section_count > 0:
        avg_words_per_section = word_count / section_count
        if avg_words_per_section < 50:
            validation["warnings"].append("Sections are very short on average")

    # Check for repeated content (simple check)
    sentences = re.split(r"[.!?]+", content)
    if len(sentences) > 5:
        unique_sentences = set(s.strip().lower() for s in sentences if s.strip())
        if len(unique_sentences) / len(sentences) < 0.8:
            validation["warnings"].append("Content may contain repetitive text")

    return validation


def extract_sections(content: str) -> Dict[str, str]:
    """Extract sections from curriculum content.

    Args:
        content: Curriculum content with markdown headers

    Returns:
        Dictionary mapping section names to content

    Raises:
        ValueError: If content is invalid
    """
    if not content or not content.strip():
        raise ValueError("Content cannot be empty")

    sections: Dict[str, str] = {}
    current_section: Optional[str] = None
    current_content: list[str] = []
    lines = content.split("\n")
    # Treat any header level of two or more hashes (##, ###, etc.) as a section delimiter
    has_sections = any(re.match(r"^##+\s", line) for line in lines)

    if not has_sections:
        # If no sections, return the entire content as "Research Content"
        return {"Research Content": content.strip()}

    for line in lines:
        if re.match(r"^##+\s", line):
            # Save previous section
            if current_section:
                section_content = "\n".join(current_content).strip()
                if section_content:  # Only add non-empty sections
                    if current_section in sections:
                        raise ValueError(f"Duplicate section name: {current_section}")
                    sections[current_section] = section_content

            # Start new section
            # Remove leading hashes and whitespace to get the title
            current_section = re.sub(r"^##+\s", "", line).strip()
            if not current_section:
                print("Warning: Found header without title")
                current_section = "Untitled Section"
            current_content = []
        elif current_section:
            current_content.append(line)

    # Save final section
    if current_section:
        section_content = "\n".join(current_content).strip()
        if section_content:
            if current_section in sections:
                raise ValueError(f"Duplicate section name: {current_section}")
            sections[current_section] = section_content

    if not sections:
        raise ValueError("No valid sections found in content")

    return sections


def _load_research_content(research_file: str) -> tuple[str, str]:
    """Load research content from a file, supporting Markdown and JSON inputs.

    Args:
        research_file: Path to a research file (.md or .json)

    Returns:
        Tuple of (entity_or_domain_name, markdown_content)
    """
    path = Path(research_file)
    stem_name = re.split(r"_research(?:_|$)", path.stem, maxsplit=1)[0] or path.stem
    if path.suffix.lower() == ".json":
        # Parse JSON and combine known content fields into a single markdown document
        try:
            import json

            raw = read_text(path)
            data = json.loads(raw)
        except Exception as exc:
            raise ValueError(f"Failed to parse JSON research file {path.name}: {exc}") from exc
        parts: list[str] = []
        # Audience research
        if isinstance(data.get("research_data"), str) and data["research_data"].strip():
            parts.append(data["research_data"].strip())
        # Domain research
        if isinstance(data.get("domain_analysis"), str) and data["domain_analysis"].strip():
            parts.append("# Domain Analysis\n\n" + data["domain_analysis"].strip())
        if isinstance(data.get("curriculum_content"), str) and data["curriculum_content"].strip():
            parts.append("# Curriculum Content\n\n" + data["curriculum_content"].strip())
        markdown_content = "\n\n".join(parts).strip()
        if not markdown_content:
            # Fallback to raw text if no known fields present
            markdown_content = raw
        return stem_name, markdown_content
    # Markdown input
    return stem_name, read_text(path)


def save_section(output_dir: str, entity_name: str, section_name: str, content: str) -> Path:
    if not isinstance(entity_name, str) or not entity_name.strip():
        raise ValueError("entity_name cannot be empty")
    if not isinstance(section_name, str) or not section_name.strip():
        raise ValueError("section_name cannot be empty")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("section content cannot be empty")
    base = Path(output_dir) if output_dir else data_written_curriculums_dir()
    entity_dir = ensure_directory(base / safe_name(entity_name))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{safe_name(section_name).lower()}_{timestamp}.md"
    file_path = next_available_path(entity_dir / filename)
    write_text(file_path, f"# {section_name}\n\n{content}")
    return file_path


def concatenate_sections(entity_dir: str, sections: Dict[str, str]) -> str:
    parts: list[str] = []
    parts.append("---")
    parts.append(f"generated: {datetime.now().isoformat()}")
    parts.append(f"entity: {Path(entity_dir).name}")
    parts.append("---\n")
    for section_name, content in sections.items():
        parts.append(f"# {section_name}\n")
        parts.append(content)
        parts.append("\n---\n")
    return "\n".join(parts)


def save_complete_curriculum(
    output_dir: str,
    entity_name: str,
    sections: Dict[str, str],
    *,
    save_intermediate_results: bool = False,
    metadata: Optional[Dict[str, Any]] = None,
    entity_id: Optional[str] = None,
) -> Path:
    base = Path(output_dir) if output_dir else data_written_curriculums_dir()
    if not isinstance(entity_name, str) or not entity_name.strip():
        raise ValueError("entity_name cannot be empty")
    if not isinstance(sections, dict) or not sections:
        raise ValueError("Cannot save an empty curriculum")
    if any(
        not isinstance(name, str)
        or not name.strip()
        or not isinstance(content, str)
        or not content.strip()
        for name, content in sections.items()
    ):
        raise ValueError("Curriculum sections must have non-empty names and content")
    stable_entity_id = stable_identifier(entity_id or entity_name)
    entity_dir = base / stable_entity_id
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    md_path, json_path = next_available_bundle(
        entity_dir, f"complete_curriculum_{timestamp}", (".md", ".json")
    )
    stored_metadata = {
        "version": "1.0",
        "generation_date": datetime.now().isoformat(),
        "file_type": "complete_curriculum",
        "entity_id": stable_entity_id,
        **(metadata or {}),
    }
    json_content = (
        json.dumps(
            {
                "timestamp": timestamp,
                "entity_name": entity_name,
                "sections": sections,
                "metadata": stored_metadata,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )
    write_text_bundle(
        {
            **{
                md_path: _concatenate_sections_with_metadata(
                    str(entity_dir), sections, stored_metadata
                ),
                json_path: json_content,
            },
            **(
                _intermediate_section_files(entity_dir, sections, timestamp)
                if save_intermediate_results
                else {}
            ),
        }
    )
    return md_path


def _concatenate_sections_with_metadata(
    entity_dir: str, sections: Dict[str, str], metadata: Dict[str, Any]
) -> str:
    """Render the canonical curriculum document with auditable frontmatter."""

    lines = ["---"]
    for key in (
        "entity_name",
        "entity_id",
        "evidence_status",
        "provider",
        "model",
        "prompt_sha256",
    ):
        if key in metadata:
            value = str(metadata[key]).replace("\n", " ")
            lines.append(f"{key}: {value}")
    lines.extend(
        [
            f"generated: {datetime.now().isoformat()}",
            f"entity: {Path(entity_dir).name}",
            "---",
            "",
        ]
    )
    for section_name, content in sections.items():
        lines.extend([f"# {section_name}", "", content, "", "---", ""])
    return "\n".join(lines)


def _intermediate_section_files(
    entity_dir: Path, sections: Dict[str, str], timestamp: str
) -> dict[Path, str]:
    """Prepare section artifacts for the same publication transaction."""
    files: dict[Path, str] = {}
    for section_name, section_content in sections.items():
        base_path = entity_dir / f"section_{safe_name(section_name).lower()}_{timestamp}.md"
        section_path = next_available_path(base_path)
        while section_path in files:
            section_path = next_available_path(
                section_path.with_name(f"{section_path.stem}_1{section_path.suffix}")
            )
        files[section_path] = f"# {section_name}\n\n{section_content}"
    return files


def process_research_file(
    client: OpenAI,
    research_file: str,
    fep_actinf_file: str,
    output_dir: str,
    model: Optional[str] = None,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    timeout: float = 120.0,
    delay_seconds: float = 0.0,
    save_intermediate_results: bool = True,
    strict_schema: bool = False,
    limiter: RequestLimiter | None = None,
    cancellation_event: threading.Event | None = None,
) -> Optional[Path]:
    """Process a research file and generate curriculum content.

    Args:
        client: OpenAI client for content generation
        research_file: Path to research file
        fep_actinf_file: Path to FEP-ActInf base content
        output_dir: Output directory for generated curricula

    Returns:
        Path to generated complete curriculum file, or None if failed

    Raises:
        ValueError: If inputs are invalid
        RuntimeError: If processing fails
    """
    if not client:
        raise ValueError("OpenAI client is required")

    if not Path(research_file).exists():
        raise FileNotFoundError(f"Research file not found: {research_file}")

    if not Path(fep_actinf_file).exists():
        raise FileNotFoundError(f"FEP-ActInf file not found: {fep_actinf_file}")

    try:
        entity_name, research_content = _load_research_content(research_file)
        validation = validate_curriculum_content(research_content, min_word_count=50)
        if not validation["valid"]:
            raise ValueError(
                f"Research content validation failed: {', '.join(validation['errors'])}"
            )

        fep_actinf_data = read_text(fep_actinf_file)
        entity_name = entity_name or "unknown_entity"
        sections = extract_sections(research_content)
        generated_sections: Dict[str, str] = {}
        generation_records: list[dict[str, Any]] = []
        usage: dict[str, Any] = {}
        failures: list[str] = []

        for section_name, content in sections.items():
            try:
                prompt = render_prompt(
                    "curriculum_section",
                    {
                        "section_name": section_name,
                        "entity_name": entity_name,
                        "section_content": content,
                        "fep_actinf_data": fep_actinf_data,
                    },
                )
                response = chat_result(
                    client,
                    prompt,
                    SYSTEM,
                    model,
                    max_retries,
                    retry_delay,
                    timeout,
                    delay_seconds,
                    strict_schema,
                    limiter,
                    cancellation_event,
                )
                structured = (
                    parse_structured_response(response.content, "curriculum")
                    if strict_schema
                    else None
                )
                section_content = payload_markdown(structured) if structured else response.content
                section_validation = validate_curriculum_content(
                    section_content, min_word_count=100
                )
                structured_response = parse_curriculum_response(section_content)
                section_validation["structured"] = structured_response.quality.as_dict()
                if not section_validation["valid"]:
                    raise ValueError(
                        f"Generated content invalid: {', '.join(section_validation['errors'])}"
                    )
                generated_sections[section_name] = section_content
                generation_records.append(
                    generation_metadata(
                        provider=response.provider,
                        model=response.model,
                        prompt_name="curriculum_section",
                        prompt=prompt,
                        evidence_status=(
                            "synthetic_foundation"
                            if Path(fep_actinf_file).name.startswith("Synthetic_")
                            else "source_material"
                        ),
                        inputs=[
                            file_input_record(research_file, label="research"),
                            file_input_record(fep_actinf_file, label="fep_actinf"),
                        ],
                    )
                )
                usage[section_name] = response.usage.as_dict()
            except Exception as exc:
                failures.append(f"{section_name}: {exc}")

        if failures:
            raise RuntimeError(
                f"Curriculum generation failed for {entity_name}; no partial output written: "
                + "; ".join(failures)
            )
        complete_path = save_complete_curriculum(
            output_dir,
            entity_name,
            generated_sections,
            save_intermediate_results=save_intermediate_results,
            entity_id=stable_identifier(entity_name),
            metadata={
                "evidence_status": (
                    "synthetic_foundation"
                    if Path(fep_actinf_file).name.startswith("Synthetic_")
                    else "source_material"
                ),
                "provider": "openrouter",
                "model": model or os.environ.get("OPENROUTER_MODEL", "unknown"),
                "entity_id": stable_identifier(entity_name),
                "source_inputs": [
                    file_input_record(research_file, label="research"),
                    file_input_record(fep_actinf_file, label="fep_actinf"),
                ],
                "generations": generation_records,
                "usage": usage,
                "quality": {
                    section_name: validate_generated_text(
                        section_content, min_words=100, require_sections=False
                    ).as_dict()
                    for section_name, section_content in generated_sections.items()
                },
            },
        )
        return complete_path
    except Exception as exc:
        raise RuntimeError(f"Error processing research file {research_file}: {exc}") from exc
