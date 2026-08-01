"""Entity research using Perplexity for audience analysis.

This module handles entity/audience research tasks using Perplexity, which provides
access to real-time online information for comprehensive audience analysis.
"""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from openai import OpenAI

from src.common.io import next_available_path, read_text, write_json
from src.common.paths import data_audience_research_dir
from src.common.prompts import as_data_block, render_prompt
from src.config.schemas import stable_identifier
from src.perplexity.clients import (
    ChatPolicy,
    CompletionResult,
    ProviderAdapter,
    RequestLimiter,
)
from src.pipeline import (
    file_input_record,
    generation_metadata,
    input_record,
    parse_research_response,
    parse_structured_response,
    payload_markdown,
)

SYSTEM_DESCRIPTION = (
    "You are an expert researcher specializing in audience analysis and curriculum development "
    "for complex scientific concepts."
)


def extract_entity_description(entity_data: str) -> str:
    """Extract entity description from formatted entity data.

    Args:
        entity_data: Formatted entity data containing name, description, and category

    Returns:
        The entity description string, or the full data if parsing fails
    """
    lines = entity_data.strip().split("\n")
    for line in lines:
        if line.startswith("Description:"):
            return line.replace("Description:", "").strip()
    return entity_data


def chat_result(
    client: OpenAI,
    prompt: str,
    system: str,
    model: Optional[str] = None,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    timeout: float = 60.0,
    strict_schema: bool = False,
    limiter: RequestLimiter | None = None,
    cancellation_event: threading.Event | None = None,
) -> CompletionResult:
    """Send chat completion request to Perplexity for entity research.

    Args:
        client: OpenAI client configured for Perplexity API
        prompt: User prompt for entity/audience research
        system: System prompt defining the AI's research role

    Returns:
        Research results from Perplexity's online-enabled models
    """
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty")
    if not system or not system.strip():
        raise ValueError("System prompt cannot be empty")
    return ProviderAdapter(
        client,
        provider="perplexity",
        policy=ChatPolicy(
            model=model or os.environ.get("PERPLEXITY_MODEL", "llama-3.1-sonar-small-128k-online"),
            timeout=timeout,
            max_retries=max_retries,
            backoff_seconds=retry_delay,
            response_format={"type": "json_object"} if strict_schema else None,
        ),
        limiter=limiter,
        cancellation_event=cancellation_event,
    ).complete([{"role": "system", "content": system}, {"role": "user", "content": prompt}])


@dataclass
class ResearchResult:
    timestamp: str
    entity_name: str
    entity_description: str
    research_data: str
    processing_time: str
    metadata: dict[str, Any] = field(default_factory=dict)
    output_paths: list[str] = field(default_factory=list)


def research_target_audience(
    client: OpenAI,
    entity_input: str,
    fep_actinf_input: str,
    output_dir: str,
    entity_name: Optional[str] = None,
    model: Optional[str] = None,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    timeout: float = 60.0,
    strict_schema: bool = False,
    entity_id: Optional[str] = None,
    limiter: RequestLimiter | None = None,
    cancellation_event: threading.Event | None = None,
) -> ResearchResult:
    """Research target audience using Perplexity API.

    Args:
        client: OpenAI client configured for Perplexity API
        entity_input: Either file path or entity content directly
        fep_actinf_input: Either file path or FEP/ActInf content directly
        output_dir: Directory to save research results
        entity_name: Optional entity name for output files (extracted from path if not provided)

    Returns:
        ResearchResult containing analysis and metadata
    """
    # Determine if inputs are file paths or content
    try:
        # Check if it's a valid path and the file exists
        entity_path = Path(entity_input)
        if entity_path.is_file():
            entity_data = read_text(entity_input)
            if entity_name is None:
                entity_name = entity_path.stem
        else:
            # Assume it's content directly
            entity_data = entity_input
            if entity_name is None:
                entity_name = "unknown_entity"
    except (OSError, ValueError):
        # If Path() fails (e.g., content too long), treat as content
        entity_data = entity_input
        if entity_name is None:
            entity_name = "unknown_entity"

    try:
        fep_actinf_path = Path(fep_actinf_input)
        if fep_actinf_path.is_file():
            fep_actinf_data = read_text(fep_actinf_input)
        else:
            fep_actinf_data = fep_actinf_input
    except (OSError, ValueError):
        fep_actinf_data = fep_actinf_input
    prompt = render_prompt(
        "research_entity",
        {
            "entity_data": as_data_block(entity_data),
            "fep_actinf_data": as_data_block(fep_actinf_data),
        },
    )

    start_time = time.time()
    response = chat_result(
        client,
        prompt,
        SYSTEM_DESCRIPTION,
        model,
        max_retries,
        retry_delay,
        timeout,
        strict_schema,
        limiter,
        cancellation_event,
    )
    payload = parse_structured_response(response.content, "research") if strict_schema else None
    content = payload_markdown(payload) if payload else response.content
    elapsed = time.time() - start_time

    # Extract entity description for separate storage
    entity_description = extract_entity_description(entity_data)

    evidence_status = (
        "synthetic_foundation"
        if Path(fep_actinf_input).name.startswith("Synthetic_")
        else "source_material"
    )
    inputs = [
        (
            file_input_record(entity_input, label="entity")
            if Path(entity_input).is_file()
            else input_record(entity_data, label="entity")
        ),
        (
            file_input_record(fep_actinf_input, label="fep_actinf")
            if Path(fep_actinf_input).is_file()
            else input_record(fep_actinf_data, label="fep_actinf")
        ),
    ]
    metadata = generation_metadata(
        provider="perplexity",
        model=response.model,
        prompt_name="research_entity",
        prompt=prompt,
        evidence_status=evidence_status,
        inputs=inputs,
    )
    metadata["entity_id"] = stable_identifier(entity_id or entity_name or "unknown_entity")
    metadata["usage"] = response.usage.as_dict()
    parsed_response = parse_research_response(content)
    metadata["citations"] = list(
        dict.fromkeys([*(payload.citations if payload else ()), *parsed_response.citations])
    )
    metadata["quality"] = parsed_response.quality.as_dict()

    result = ResearchResult(
        timestamp=datetime.now().isoformat(),
        entity_name=entity_name,
        entity_description=entity_description,
        research_data=content,
        processing_time=f"{elapsed:.2f} seconds",
        metadata=metadata,
    )

    date_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    stable_entity_id = stable_identifier(entity_id or entity_name or "unknown_entity")
    json_filename = f"{stable_entity_id}_research_{date_str}.json"
    out_base = output_dir or str(data_audience_research_dir())
    output_path = next_available_path(Path(out_base) / json_filename)
    result.output_paths = [str(output_path)]
    write_json(output_path, result.__dict__)

    return result
