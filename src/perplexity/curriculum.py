"""Curriculum generation using OpenRouter for content creation.

This module handles curriculum generation tasks using OpenRouter,
which is optimized for content creation rather than research.
"""

from __future__ import annotations

import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from openai import OpenAI

from src.common.io import read_text, write_json, write_text
from src.common.paths import data_written_curriculums_dir
from src.common.prompts import render_prompt

SYSTEM = (
    "You are an expert researcher and educator specializing in creating comprehensive, "
    "high-quality technical content. Your goal is to provide the most thorough, accurate, "
    "and well-structured information possible, with extensive references and practical applications."
)


def chat(client: OpenAI, prompt: str, system: str, model: Optional[str] = None) -> str:
    """Send chat completion request to OpenRouter for content generation.

    Args:
        client: OpenAI client configured for OpenRouter
        prompt: User prompt for content generation
        system: System prompt defining the AI's role
        model: Optional model override (defaults to OPENROUTER_MODEL)

    Returns:
        Generated content from the model
    """
    response = client.chat.completions.create(
        model=model or os.environ.get("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"),
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


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
        validation["warnings"].append(
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
                    sections[current_section] = section_content
                else:
                    print(f"Warning: Empty section found: {current_section}")

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
            sections[current_section] = section_content
        else:
            print(f"Warning: Empty final section: {current_section}")

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
    stem_name = path.stem.split("_research_")[0] or path.stem
    if path.suffix.lower() == ".json":
        # Parse JSON and combine known content fields into a single markdown document
        try:
            import json

            raw = read_text(path)
            data = json.loads(raw)
        except Exception as exc:
            raise ValueError(f"Failed to parse JSON research file {path.name}: {exc}")
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
    base = Path(output_dir) if output_dir else data_written_curriculums_dir()
    entity_dir = base / entity_name
    entity_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{section_name.lower().replace(' ', '_')}_{timestamp}.md"
    file_path = entity_dir / filename
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


def save_complete_curriculum(output_dir: str, entity_name: str, sections: Dict[str, str]) -> Path:
    base = Path(output_dir) if output_dir else data_written_curriculums_dir()
    entity_dir = base / entity_name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_filename = f"complete_curriculum_{timestamp}.md"
    md_path = entity_dir / md_filename
    write_text(md_path, concatenate_sections(str(entity_dir), sections))
    json_filename = f"complete_curriculum_{timestamp}.json"
    write_json(
        entity_dir / json_filename,
        {
            "timestamp": timestamp,
            "entity_name": entity_name,
            "sections": sections,
            "metadata": {
                "version": "1.0",
                "generation_date": datetime.now().isoformat(),
                "file_type": "complete_curriculum",
            },
        },
    )
    return md_path


def process_research_file(
    client: OpenAI, research_file: str, fep_actinf_file: str, output_dir: str
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
        # Load and validate research content (supports .md and .json inputs)
        entity_or_domain, research_content = _load_research_content(research_file)
        validation = validate_curriculum_content(research_content, min_word_count=50)

        if not validation["valid"]:
            print(f"Research content validation failed: {', '.join(validation['errors'])}")
            return None

        if validation["warnings"]:
            for warning in validation["warnings"]:
                print(f"Research content warning: {warning}")

        # Load FEP-ActInf data
        fep_actinf_data = read_text(fep_actinf_file)

        # Derive entity or domain name from file
        entity_name = entity_or_domain
        if not entity_name:
            print(f"Warning: Could not extract entity name from {research_file}")
            entity_name = "unknown_entity"

        # Extract sections from research content
        sections = extract_sections(research_content)
        print(f"Extracted {len(sections)} sections for {entity_name}")

        generated_sections: Dict[str, str] = {}

        # Generate curriculum content for each section
        for i, (section_name, content) in enumerate(sections.items(), 1):
            print(f"Processing section {i}/{len(sections)}: {section_name}")

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

                # Simple retry loop for model generation
                last_error: Optional[Exception] = None
                for attempt in range(3):
                    try:
                        section_content = chat(client, prompt, SYSTEM)
                        # Validate generated section content
                        section_validation = validate_curriculum_content(
                            section_content, min_word_count=100
                        )
                        if not section_validation["valid"]:
                            raise ValueError(
                                f"Generated content invalid: {', '.join(section_validation['errors'])}"
                            )
                        # Optionally log warnings but proceed
                        for warning in section_validation.get("warnings", []):
                            print(f"Generated section warning for {section_name}: {warning}")
                        # Save individual section
                        save_section(output_dir, entity_name, section_name, section_content)
                        generated_sections[section_name] = section_content
                        break
                    except Exception as gen_exc:
                        last_error = gen_exc
                        # Backoff before retrying
                        time.sleep(1.0 * (attempt + 1))
                        continue
                else:
                    # All attempts failed
                    raise last_error or RuntimeError("Unknown generation error")

                # Brief delay between API calls
                time.sleep(0.5)

            except Exception as e:
                print(f"Failed to process section {section_name}: {str(e)}")
                continue

        # Save complete curriculum if we have any sections
        if generated_sections:
            print(f"Generated {len(generated_sections)} sections for {entity_name}")
            return save_complete_curriculum(output_dir, entity_name, generated_sections)
        else:
            print(f"No sections generated for {entity_name}")
            return None

    except Exception as e:
        print(f"Error processing research file {research_file}: {str(e)}")
        return None
