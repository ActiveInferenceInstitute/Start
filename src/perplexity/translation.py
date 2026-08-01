"""Translation services using OpenRouter for content generation.

This module handles translation tasks using OpenRouter, which provides
better language models for translation compared to research-focused APIs.
"""

from __future__ import annotations

import os
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

from openai import OpenAI

from src.common.io import ensure_directory, next_available_path, read_text, write_text
from src.common.paths import data_translated_curriculums_dir
from src.common.prompts import render_prompt
from src.config.languages import get_script_mapping
from src.config.schemas import stable_identifier
from src.perplexity.clients import ChatPolicy, ProviderAdapter, RequestLimiter
from src.pipeline import (
    generation_metadata,
    input_record,
    parse_structured_response,
    parse_translation_response,
    payload_markdown,
)


def generate_translation_prompt(content: str, target_language: str) -> str:
    """Generate translation prompt using template with variables."""
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Translation content cannot be empty")
    if not isinstance(target_language, str) or not target_language.strip():
        raise ValueError("Target language cannot be empty")
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
    if max_chunk_size <= 0:
        raise ValueError("max_chunk_size must be greater than zero")
    if not content:
        return []
    chunks: list[str] = []
    import re

    sections = [part for part in re.split(r"(?=^#{1,6}\s.*$)", content, flags=re.MULTILINE) if part]
    for section in sections:
        if len(section) <= max_chunk_size:
            if chunks and len(chunks[-1]) + 1 + len(section) <= max_chunk_size:
                chunks[-1] += "\n" + section
            else:
                chunks.append(section)
            continue
        # A single section may exceed the limit; split it by lines, then by
        # hard character boundaries for an unusually long line.
        buffer = ""
        for line in section.splitlines(keepends=True):
            if len(line) > max_chunk_size:
                if buffer:
                    chunks.append(buffer)
                    buffer = ""
                chunks.extend(
                    line[i : i + max_chunk_size] for i in range(0, len(line), max_chunk_size)
                )
            elif len(buffer) + len(line) > max_chunk_size:
                chunks.append(buffer)
                buffer = line
            else:
                buffer += line
        if buffer:
            chunks.append(buffer)
    return chunks


@dataclass
class TranslationResult:
    """Translated content with chunk-level provenance and usage telemetry."""

    content: str
    target_language: str
    records: list[dict[str, Any]] = field(default_factory=list)
    usage: dict[str, Any] = field(default_factory=dict)


def translate_curriculum_result(
    client: OpenAI,
    content: str,
    target_language: str,
    max_chunk_size: int = 4000,
    model: Optional[str] = None,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    timeout: float = 120.0,
    delay_seconds: float = 0.0,
    strict_schema: bool = False,
    limiter: RequestLimiter | None = None,
    cancellation_event: threading.Event | None = None,
) -> TranslationResult:
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
    if client is None or not hasattr(client, "chat"):
        raise ValueError("OpenAI client is required")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Translation content cannot be empty")
    if not isinstance(target_language, str) or not target_language.strip():
        raise ValueError("Target language cannot be empty")
    chunks = split_content_into_chunks(content, max_chunk_size)
    translated_chunks: list[str] = []
    records: list[dict[str, Any]] = []
    usage: dict[str, Any] = {}
    system = (
        f"You are an expert translator specializing in academic and technical content translation "
        f"to {target_language}, with deep understanding of the target language's "
        f"cultural and academic context."
    )
    for chunk in chunks:
        prompt = generate_translation_prompt(chunk, target_language)
        response = ProviderAdapter(
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
        structured = (
            parse_structured_response(response.content, "translation") if strict_schema else None
        )
        if structured and structured.target_language.casefold() != target_language.casefold():
            raise ValueError(
                "translation provider payload target_language does not match requested language"
            )
        translated_chunks.append(payload_markdown(structured) if structured else response.content)
        records.append(
            generation_metadata(
                provider=response.provider,
                model=response.model,
                prompt_name="translation",
                prompt=prompt,
                evidence_status="derived_translation",
                inputs=[input_record(chunk, label="source_chunk")],
            )
        )
        usage[str(len(records))] = response.usage.as_dict()
    translated = "\n".join(translated_chunks)
    quality = parse_translation_response(content, translated, target_language).quality
    if not quality.valid:
        raise ValueError("Translation quality validation failed: " + "; ".join(quality.errors))
    return TranslationResult(
        content=translated,
        target_language=target_language,
        records=records,
        usage=usage,
    )


def save_translation(
    output_dir: str,
    entity_name: str,
    language: str,
    content: str,
    *,
    entity_id: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> Path:
    if not isinstance(entity_name, str) or not entity_name.strip():
        raise ValueError("entity_name cannot be empty")
    if not isinstance(language, str) or not language.strip():
        raise ValueError("language cannot be empty")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("translation content cannot be empty")
    base = Path(output_dir) if output_dir else data_translated_curriculums_dir()
    stable_entity_id = entity_id or stable_identifier(entity_name)
    stable_language_id = stable_identifier(language)
    lang_dir = ensure_directory(base / stable_language_id)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{stable_entity_id}_curriculum_{stable_language_id}_{timestamp}.md"
    file_path = next_available_path(lang_dir / filename)
    stored_metadata = metadata or {}
    header = (
        "---\n"
        f"language: {language}\n"
        f"translation_date: {datetime.now().isoformat()}\n"
        f"original_entity: {entity_name}\n"
        f"entity_id: {stable_entity_id}\n"
        f"language_id: {stable_language_id}\n"
        f"script: {get_script_mapping(language)}\n"
        + "".join(
            f"{key}: {str(value).replace(chr(10), ' ')}\n"
            for key, value in stored_metadata.items()
            if isinstance(value, (str, int, float, bool))
        )
        + "---\n\n"
    )
    write_text(file_path, header + content)
    return file_path


def process_translations_detailed(
    client: OpenAI,
    curriculum_dir: str,
    output_dir: str,
    target_languages: List[str],
    *,
    model: Optional[str] = None,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    timeout: float = 120.0,
    delay_seconds: float = 0.0,
    skip_existing: bool = True,
    max_concurrent: int = 1,
    max_chunk_size: int = 4000,
    strict_schema: bool = False,
    limiter: RequestLimiter | None = None,
    cancellation_event: threading.Event | None = None,
) -> tuple[int, int, list[dict[str, Any]]]:
    if max_concurrent < 1:
        raise ValueError("max_concurrent must be at least one")
    if not isinstance(target_languages, list) or not target_languages:
        raise ValueError("target_languages must be a non-empty list")
    if any(not isinstance(language, str) or not language.strip() for language in target_languages):
        raise ValueError("target_languages must contain non-empty strings")
    if len({language.casefold() for language in target_languages}) != len(target_languages):
        raise ValueError("target_languages contains duplicate values")
    curriculum_files = sorted(Path(curriculum_dir).glob("*/complete_curriculum_*.md"))
    jobs: list[tuple[str, str, str]] = []
    skipped_items: list[dict[str, Any]] = []

    def translation_fresh(existing: list[Path], current_hash: str) -> bool:
        """True when an existing translation provably matches the source hash.

        Legacy files without a recorded source_sha256 are treated as fresh so
        skip_existing does not force a full re-translation, but a verifiable
        mismatch (source changed after the translation was made) is never
        silently reused.
        """
        for path in existing:
            try:
                prefix = path.read_text(encoding="utf-8")[:4000]
            except OSError:
                continue
            for line in prefix.splitlines():
                if line.startswith("source_sha256:"):
                    recorded = line.split(":", 1)[1].strip()
                    if recorded:
                        return recorded == current_hash
        return True

    for curr_file in curriculum_files:
        entity_name = curr_file.parent.name
        content = read_text(curr_file)
        if not content.strip():
            continue
        for language in target_languages:
            normalized_language = stable_identifier(language)
            normalized_entity = stable_identifier(entity_name)
            lang_dir = Path(output_dir) / normalized_language
            existing = (
                list(lang_dir.glob(f"{normalized_entity}_curriculum_{normalized_language}_*.md"))
                if lang_dir.exists()
                else []
            )
            source_hash = input_record(content, label="source")["sha256"]
            if existing and skip_existing and translation_fresh(existing, source_hash):
                skipped_items.append(
                    {
                        "item_id": f"{normalized_entity}:{normalized_language}",
                        "status": "skipped",
                        "output_paths": [str(path) for path in existing],
                        "provenance": {"mode": "existing_output"},
                        "input_hashes": {"source": source_hash},
                    }
                )
                continue
            jobs.append((entity_name, language, content))

    def process(
        job: tuple[str, str, str],
    ) -> tuple[bool, str, Path | None, TranslationResult | None, str]:
        entity_name, language, content = job
        source_hash = input_record(content, label="source")["sha256"]
        try:
            translation = translate_curriculum_result(
                client,
                content,
                language,
                max_chunk_size=max_chunk_size,
                model=model,
                max_retries=max_retries,
                retry_delay=retry_delay,
                timeout=timeout,
                delay_seconds=delay_seconds,
                strict_schema=strict_schema,
                limiter=limiter,
                cancellation_event=cancellation_event,
            )
            translated = translation.content
            if not translated.strip():
                raise ValueError(f"Empty translation returned for {entity_name}/{language}")
            output_path = save_translation(
                output_dir,
                entity_name,
                language,
                translated,
                entity_id=stable_identifier(entity_name),
                metadata={
                    "provider": "openrouter",
                    "model": model or os.environ.get("OPENROUTER_MODEL", "unknown"),
                    "evidence_status": "derived_translation",
                    "source_sha256": source_hash,
                    "quality_status": "passed",
                    "source_word_count": len(content.split()),
                },
            )
            return True, f"{entity_name}/{language}", output_path, translation, source_hash
        except Exception as exc:
            return False, f"{entity_name}/{language}: {exc}", None, None, source_hash

    with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        outcomes = list(executor.map(process, jobs))
    for success, message, _output_path, _translation, _source_hash in outcomes:
        if not success:
            print(f"Translation failed: {message}")
    items = list(skipped_items)
    for (entity_name, language, _content), (
        success,
        message,
        output_path,
        translation,
        source_hash,
    ) in zip(jobs, outcomes, strict=True):
        item_id = f"{stable_identifier(entity_name)}:{stable_identifier(language)}"
        item: dict[str, Any] = {
            "item_id": item_id,
            "status": "succeeded" if success else "failed",
            "input_hashes": {"source": source_hash},
        }
        if success and output_path is not None and translation is not None:
            item.update(
                {
                    "output_paths": [str(output_path)],
                    "provenance": {
                        "records": translation.records,
                        "target_language": translation.target_language,
                        "evidence_status": "derived_translation",
                    },
                    "usage": translation.usage,
                }
            )
        elif not success:
            # The failure message is "{entity}/{language}: {detail}"; strip the
            # prefix when present but never assume a colon exists.
            item["errors"] = [
                message.split(":", 1)[1].strip() if ":" in message else message.strip()
            ]
        items.append(item)
    return (
        sum(outcome[0] for outcome in outcomes),
        sum(not outcome[0] for outcome in outcomes),
        items,
    )
