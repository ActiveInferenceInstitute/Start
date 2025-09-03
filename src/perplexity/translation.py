"""Translation services using OpenRouter for content generation.

This module handles translation tasks using OpenRouter, which provides
better language models for translation compared to research-focused APIs.
"""

from __future__ import annotations

import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from openai import OpenAI

from src.common.io import read_text, write_text
from src.common.paths import data_translated_curriculums_dir
from src.common.prompts import render_prompt
from src.config.languages import get_script_mapping


def generate_translation_prompt(content: str, target_language: str) -> str:
    """Generate translation prompt using template with variables."""
    language_script = get_script_mapping(target_language)
    return render_prompt(
        "translation",
        {
            "content": content,
            "target_language": target_language,
            "language_script": language_script,
        },
    )


def split_content_into_chunks(content: str, max_chunk_size: int) -> List[str]:
    chunks: list[str] = []
    current_chunk: list[str] = []
    current_size = 0
    import re

    sections = re.split(r"(^#{1,6}\s.*$)", content, flags=re.MULTILINE)
    for section in sections:
        section_size = len(section)
        if current_size + section_size > max_chunk_size and current_chunk:
            chunks.append("\n".join(current_chunk))
            current_chunk = []
            current_size = 0
        current_chunk.append(section)
        current_size += section_size
    if current_chunk:
        chunks.append("\n".join(current_chunk))
    return chunks


def translate_curriculum(
    client: OpenAI,
    content: str,
    target_language: str,
    max_chunk_size: int = 4000,
    model: Optional[str] = None,
) -> str:
    """Translate curriculum content to target language using OpenRouter.

    Args:
        client: OpenAI client configured for OpenRouter
        content: Content to translate
        target_language: Target language for translation
        max_chunk_size: Maximum size of content chunks for translation
        model: Optional model override (defaults to OPENROUTER_MODEL)

    Returns:
        Translated content as a single string
    """
    chunks = split_content_into_chunks(content, max_chunk_size)
    translated_chunks: list[str] = []
    system = (
        f"You are an expert translator specializing in academic and technical content translation "
        f"to {target_language}, with deep understanding of the target language's cultural and academic context."
    )
    for chunk in chunks:
        prompt = generate_translation_prompt(chunk, target_language)
        response = client.chat.completions.create(
            model=model or os.environ.get("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"),
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        )
        translated_chunks.append(response.choices[0].message.content)
        time.sleep(1)
    return "\n".join(translated_chunks)


def save_translation(output_dir: str, entity_name: str, language: str, content: str) -> Path:
    base = Path(output_dir) if output_dir else data_translated_curriculums_dir()
    lang_dir = base / language.lower()
    lang_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{entity_name}_curriculum_{language.lower()}_{timestamp}.md"
    file_path = lang_dir / filename
    header = (
        "---\n"
        f"language: {language}\n"
        f"translation_date: {datetime.now().isoformat()}\n"
        f"original_entity: {entity_name}\n"
        f"script: {get_script_mapping(language)}\n"
        "---\n\n"
    )
    write_text(file_path, header + content)
    return file_path


def process_translations(
    client: OpenAI, curriculum_dir: str, output_dir: str, target_languages: List[str]
) -> tuple[int, int]:
    curriculum_files = list(Path(curriculum_dir).glob("*/complete_curriculum_*.md"))
    total_success = 0
    total_failed = 0
    for curr_file in curriculum_files:
        entity_name = curr_file.parent.name
        content = read_text(curr_file)
        if not content:
            continue
        for language in target_languages:
            lang_dir = Path(output_dir) / language.lower()
            existing = (
                list(lang_dir.glob(f"{entity_name}_curriculum_{language.lower()}_*.md"))
                if lang_dir.exists()
                else []
            )
            if existing:
                continue
            try:
                translated = translate_curriculum(client, content, language)
                save_translation(output_dir, entity_name, language, translated)
                total_success += 1
            except Exception:
                total_failed += 1
                continue
    return total_success, total_failed
