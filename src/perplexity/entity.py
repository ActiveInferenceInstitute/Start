"""Entity research using Perplexity for audience analysis.

This module handles entity/audience research tasks using Perplexity, which provides
access to real-time online information for comprehensive audience analysis.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from openai import OpenAI

from src.common.io import read_text, write_json
from src.common.paths import data_audience_research_dir
from src.common.prompts import render_prompt


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
    try:
        lines = entity_data.strip().split('\n')
        for line in lines:
            if line.startswith('Description:'):
                return line.replace('Description:', '').strip()
        # If no Description: line found, return the full data
        return entity_data
    except Exception:
        # If anything goes wrong, return the full data
        return entity_data


def chat(client: OpenAI, prompt: str, system: str) -> str:
    """Send chat completion request to Perplexity for entity research.
    
    Args:
        client: OpenAI client configured for Perplexity API
        prompt: User prompt for entity/audience research
        system: System prompt defining the AI's research role
        
    Returns:
        Research results from Perplexity's online-enabled models
    """
    response = client.chat.completions.create(
        model=os.environ.get("PERPLEXITY_MODEL", "llama-3.1-sonar-small-128k-online"),
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


@dataclass
class ResearchResult:
    timestamp: str
    entity_name: str
    entity_description: str
    research_data: str
    processing_time: str


def research_target_audience(
    client: OpenAI, 
    entity_input: str, 
    fep_actinf_input: str, 
    output_dir: str,
    entity_name: Optional[str] = None
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
        if len(entity_input) < 500 and entity_path.exists():
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
        if len(fep_actinf_input) < 500 and fep_actinf_path.exists():
            fep_actinf_data = read_text(fep_actinf_input)
        else:
            fep_actinf_data = fep_actinf_input
    except (OSError, ValueError):
        fep_actinf_data = fep_actinf_input
    prompt = render_prompt("research_entity", {
        "entity_data": entity_data,
        "fep_actinf_data": fep_actinf_data
    })

    start_time = time.time()
    content = chat(client, prompt, SYSTEM_DESCRIPTION)
    elapsed = time.time() - start_time
    
    # Extract entity description for separate storage
    entity_description = extract_entity_description(entity_data)

    result = ResearchResult(
        timestamp=datetime.now().isoformat(),
        entity_name=entity_name,
        entity_description=entity_description,
        research_data=content,
        processing_time=f"{elapsed:.2f} seconds",
    )

    date_str = datetime.now().strftime("%Y%m%d")
    json_filename = f"{entity_name}_research_{date_str}.json"
    out_base = output_dir or str(data_audience_research_dir())
    write_json(os.path.join(out_base, json_filename), result.__dict__)

    return result



