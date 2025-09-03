"""Domain analysis using Perplexity for online research.

This module handles domain research tasks using Perplexity, which provides
access to real-time online information for comprehensive domain analysis.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional

from openai import OpenAI

from src.common.io import read_text, write_text, write_json
from src.common.paths import data_domain_research_dir
from src.common.prompts import render_prompt


SYSTEM_ANALYSIS = (
    "You are an expert researcher specializing in domain analysis and curriculum development "
    "for complex scientific concepts."
)
SYSTEM_CURRICULUM = (
    "You are an expert curriculum developer specializing in creating domain-specific "
    "introductions to Active Inference."
)


def chat(client: OpenAI, prompt: str, system: str, max_retries: int = 3, retry_delay: float = 1.0) -> str:
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
    
    model = os.environ.get("PERPLEXITY_MODEL", "llama-3.1-sonar-small-128k-online")
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                timeout=60,  # 60 second timeout
            )
            
            if not response.choices or not response.choices[0].message.content:
                raise RuntimeError("Empty response from Perplexity API")
            
            return response.choices[0].message.content
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"Perplexity API request failed after {max_retries} attempts: {str(e)}") from e
            
            # Log the retry attempt
            print(f"API request failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
            retry_delay *= 2  # Exponential backoff


@dataclass
class DomainResult:
    timestamp: str
    domain_name: str
    domain_analysis: str
    curriculum_content: str
    processing_time: str


def analyze_domain(
    client: OpenAI, 
    domain_input: str, 
    fep_actinf_input: str, 
    output_dir: str,
    domain_name: Optional[str] = None
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
        if len(domain_input) < 500 and domain_path.exists():
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
        if len(fep_actinf_input) < 500 and fep_actinf_path.exists():
            fep_actinf_data = read_text(fep_actinf_input)
        else:
            fep_actinf_data = fep_actinf_input
    except (OSError, ValueError):
        fep_actinf_data = fep_actinf_input

    # Analysis
    analysis_prompt = render_prompt("research_domain_analysis", {
        "domain_content": domain_content
    })
    start = time.time()
    domain_analysis = chat(client, analysis_prompt, SYSTEM_ANALYSIS)

    # Curriculum
    curriculum_prompt = render_prompt("research_domain_curriculum", {
        "domain_analysis": domain_analysis,
        "fep_actinf_data": fep_actinf_data
    })
    curriculum_content = chat(client, curriculum_prompt, SYSTEM_CURRICULUM)
    elapsed = time.time() - start

    result = DomainResult(
        timestamp=datetime.now().isoformat(),
        domain_name=domain_name,
        domain_analysis=domain_analysis,
        curriculum_content=curriculum_content,
        processing_time=f"{elapsed:.2f} seconds",
    )

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = f"{domain_name}_research_{ts}.json"
    md_filename = f"{domain_name}_research_{ts}.md"
    out_base = output_dir or str(data_domain_research_dir())
    write_json(os.path.join(out_base, json_filename), result.__dict__)
    markdown = (
        f"# {result.domain_name} Domain Research Report\n\n"
        f"**Date:** {result.timestamp[:10]}\n"
        f"**Processing Time:** {result.processing_time}\n\n"
        "---\n\n"
        "## Domain Analysis\n\n"
        f"{result.domain_analysis}\n\n"
        "## Curriculum Content\n\n"
        f"{result.curriculum_content}"
    )
    write_text(os.path.join(out_base, md_filename), markdown)
    return result



