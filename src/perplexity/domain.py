"""Domain analysis using Perplexity for online research.

This module handles domain research tasks using Perplexity, which provides
access to real-time online information for comprehensive domain analysis.
"""

from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from openai import OpenAI

from src.common.io import next_available_bundle, read_text, write_text_bundle
from src.common.paths import data_domain_research_dir
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

SYSTEM_ANALYSIS = (
    "You are an expert researcher specializing in domain analysis and curriculum development "
    "for complex scientific concepts."
)
SYSTEM_CURRICULUM = (
    "You are an expert curriculum developer specializing in creating domain-specific "
    "introductions to Active Inference."
)


def chat_result(
    client: OpenAI,
    prompt: str,
    system: str,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    model: Optional[str] = None,
    timeout: float = 60.0,
    strict_schema: bool = False,
    limiter: RequestLimiter | None = None,
    cancellation_event: threading.Event | None = None,
) -> CompletionResult:
    """Send chat completion request to Perplexity for domain research.

    Args:
        client: OpenAI client configured for Perplexity API
        prompt: User prompt for domain research
        system: System prompt defining the AI's research role
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds

    Returns:
        Research results from Perplexity's online-enabled models

    Raises:
        ValueError: If inputs are invalid
        RuntimeError: If API request fails after all retries
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
class DomainResult:
    timestamp: str
    domain_name: str
    domain_analysis: str
    curriculum_content: str
    processing_time: str
    metadata: dict[str, Any] = field(default_factory=dict)
    output_paths: list[str] = field(default_factory=list)


def analyze_domain(
    client: OpenAI,
    domain_input: str,
    fep_actinf_input: str,
    output_dir: str,
    domain_name: Optional[str] = None,
    model: Optional[str] = None,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    timeout: float = 60.0,
    strict_schema: bool = False,
    domain_id: Optional[str] = None,
    limiter: RequestLimiter | None = None,
    cancellation_event: threading.Event | None = None,
) -> DomainResult:
    """Analyze domain using Perplexity API for online research.

    Args:
        client: OpenAI client configured for Perplexity API
        domain_input: Either file path or domain content directly
        fep_actinf_input: Either file path or FEP/ActInf content directly
        output_dir: Directory to save research results
        domain_name: Optional domain name for output files (extracted from path if not provided)

    Returns:
        DomainResult containing analysis, curriculum content, and metadata

    Raises:
        ValueError: If inputs are invalid
        FileNotFoundError: If specified files don't exist
        RuntimeError: If analysis fails
    """
    # Validate inputs
    if not client:
        raise ValueError("OpenAI client is required")

    if not domain_input or not domain_input.strip():
        raise ValueError("Domain input cannot be empty")

    if not fep_actinf_input or not fep_actinf_input.strip():
        raise ValueError("FEP-ActInf input cannot be empty")

    if not output_dir or not output_dir.strip():
        raise ValueError("Output directory cannot be empty")
    # Determine if inputs are file paths or content
    try:
        # Check if it's a valid path and the file exists
        domain_path = Path(domain_input)
        if domain_path.is_file():
            domain_content = read_text(domain_input)
            if domain_name is None:
                domain_name = domain_path.stem
        else:
            # Assume it's content directly
            domain_content = domain_input
            if domain_name is None:
                domain_name = "unknown_domain"
    except (OSError, ValueError):
        # If Path() fails (e.g., content too long), treat as content
        domain_content = domain_input
        if domain_name is None:
            domain_name = "unknown_domain"

    try:
        fep_actinf_path = Path(fep_actinf_input)
        if fep_actinf_path.is_file():
            fep_actinf_data = read_text(fep_actinf_input)
        else:
            fep_actinf_data = fep_actinf_input
    except (OSError, ValueError):
        fep_actinf_data = fep_actinf_input

    # Analysis
    analysis_prompt = render_prompt(
        "research_domain_analysis", {"domain_content": as_data_block(domain_content)}
    )
    start = time.time()
    analysis_response = chat_result(
        client,
        analysis_prompt,
        SYSTEM_ANALYSIS,
        max_retries,
        retry_delay,
        model,
        timeout,
        strict_schema,
        limiter,
        cancellation_event,
    )
    analysis_payload = (
        parse_structured_response(analysis_response.content, "research") if strict_schema else None
    )
    domain_analysis = (
        payload_markdown(analysis_payload) if analysis_payload else analysis_response.content
    )

    # Curriculum
    curriculum_prompt = render_prompt(
        "research_domain_curriculum",
        {"domain_analysis": domain_analysis, "fep_actinf_data": as_data_block(fep_actinf_data)},
    )
    curriculum_response = chat_result(
        client,
        curriculum_prompt,
        SYSTEM_CURRICULUM,
        max_retries,
        retry_delay,
        model,
        timeout,
        strict_schema,
        limiter,
        cancellation_event,
    )
    curriculum_payload = (
        parse_structured_response(curriculum_response.content, "curriculum")
        if strict_schema
        else None
    )
    curriculum_content = (
        payload_markdown(curriculum_payload) if curriculum_payload else curriculum_response.content
    )
    elapsed = time.time() - start

    domain_input_record = (
        file_input_record(domain_input, label="domain")
        if Path(domain_input).is_file()
        else input_record(domain_content, label="domain")
    )
    fep_input_record = (
        file_input_record(fep_actinf_input, label="fep_actinf")
        if Path(fep_actinf_input).is_file()
        else input_record(fep_actinf_data, label="fep_actinf")
    )
    evidence_status = (
        "synthetic_foundation"
        if Path(fep_actinf_input).name.startswith("Synthetic_")
        else "source_material"
    )
    metadata = generation_metadata(
        provider="perplexity",
        model=analysis_response.model,
        prompt_name="research_domain_analysis",
        prompt=analysis_prompt,
        evidence_status=evidence_status,
        inputs=[domain_input_record, fep_input_record],
    )
    metadata.update(
        {
            "domain_id": stable_identifier(domain_id or domain_name or "unknown_domain"),
            "citations_analysis": list(
                dict.fromkeys(
                    [
                        *(analysis_payload.citations if analysis_payload else ()),
                        *parse_research_response(domain_analysis).citations,
                    ]
                )
            ),
            "citations_curriculum": list(parse_research_response(curriculum_content).citations),
            "prompt_sha256_curriculum": generation_metadata(
                provider="perplexity",
                model=curriculum_response.model,
                prompt_name="research_domain_curriculum",
                prompt=curriculum_prompt,
                evidence_status=evidence_status,
                inputs=[],
            )["prompt_sha256"],
            "usage": {
                "analysis": analysis_response.usage.as_dict(),
                "curriculum": curriculum_response.usage.as_dict(),
            },
            "quality": {
                "analysis": parse_research_response(domain_analysis).quality.as_dict(),
                "curriculum": parse_research_response(curriculum_content).quality.as_dict(),
            },
        }
    )

    result = DomainResult(
        timestamp=datetime.now().isoformat(),
        domain_name=domain_name,
        domain_analysis=domain_analysis,
        curriculum_content=curriculum_content,
        processing_time=f"{elapsed:.2f} seconds",
        metadata=metadata,
    )

    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    safe_domain = stable_identifier(domain_id or domain_name or "unknown_domain")
    output_base = Path(output_dir or str(data_domain_research_dir()))
    json_path, md_path = next_available_bundle(
        output_base,
        f"{safe_domain}_research_{ts}",
        (".json", ".md"),
    )
    markdown = (
        f"# {result.domain_name} Domain Research Report\n\n"
        f"**Date:** {result.timestamp[:10]}\n"
        f"**Processing Time:** {result.processing_time}\n\n"
        f"**Evidence Status:** {result.metadata.get('evidence_status', 'unknown')}\n"
        f"**Domain ID:** {result.metadata.get('domain_id', 'unknown')}\n"
        f"**Provider:** {result.metadata.get('provider', 'unknown')}\n"
        f"**Model:** {result.metadata.get('model', 'unknown')}\n\n"
        "---\n\n"
        "## Domain Analysis\n\n"
        f"{result.domain_analysis}\n\n"
        "## Curriculum Content\n\n"
        f"{result.curriculum_content}"
    )
    result.output_paths = [str(json_path), str(md_path)]
    write_text_bundle(
        {
            json_path: json.dumps(result.__dict__, ensure_ascii=False, indent=2) + "\n",
            md_path: markdown,
        }
    )
    return result
