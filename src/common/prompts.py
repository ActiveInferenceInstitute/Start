"""Prompts loader for reading Markdown templates with variable substitution."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Optional

from src.common.io import read_text, write_text
from src.common.paths import data_root


def prompts_dir() -> Path:
    """Return the prompts directory under data/."""
    return data_root() / "prompts"


def load_prompt_template(name: str) -> str:
    """Load a prompt template from data/prompts/{name}.md.
    
    Args:
        name: Name of the prompt template (without .md extension)
        
    Returns:
        The template content as a string
        
    Raises:
        FileNotFoundError: If the template file doesn't exist
    """
    template_path = prompts_dir() / f"{name}.md"
    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {template_path}")
    return read_text(template_path)


def save_prompt_template(name: str, content: str) -> Path:
    """Save a prompt template to data/prompts/{name}.md.
    
    Args:
        name: Name of the prompt template (without .md extension)
        content: The template content
        
    Returns:
        Path to the saved template file
    """
    prompts_dir().mkdir(parents=True, exist_ok=True)
    template_path = prompts_dir() / f"{name}.md"
    return write_text(template_path, content)


def substitute_variables(template: str, variables: Dict[str, Any], strict: bool = False) -> str:
    """Substitute variables in a template using {{variable_name}} syntax.
    
    Args:
        template: The template string with {{variable_name}} placeholders
        variables: Dictionary of variable names to values
        strict: If True, raises error for missing variables
        
    Returns:
        Template with variables substituted
        
    Raises:
        ValueError: If strict=True and variables are missing or template is invalid
        
    Example:
        >>> template = "Hello {{name}}, welcome to {{place}}!"
        >>> substitute_variables(template, {"name": "Alice", "place": "Wonderland"})
        'Hello Alice, welcome to Wonderland!'
    """
    if not template:
        raise ValueError("Template cannot be empty")
    
    if variables is None:
        variables = {}
    
    missing_vars = []
    used_vars = set()
    
    def replace_var(match):
        var_name = match.group(1).strip()
        used_vars.add(var_name)
        
        if var_name in variables:
            value = variables[var_name]
            # Handle None values gracefully
            if value is None:
                return ""
            return str(value)
        else:
            missing_vars.append(var_name)
            if strict:
                return match.group(0)  # Keep original for error reporting
            return match.group(0)  # Return original if variable not found
    
    result = re.sub(r'\{\{\s*([^}]+)\s*\}\}', replace_var, template)
    
    if strict and missing_vars:
        raise ValueError(f"Missing required template variables: {', '.join(missing_vars)}")
    
    return result


def validate_prompt_template(template: str) -> Dict[str, Any]:
    """Validate a prompt template and extract metadata.
    
    Args:
        template: The template string to validate
        
    Returns:
        Dictionary with validation results and metadata
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "variables": set(),
        "word_count": len(template.split()),
        "line_count": len(template.split('\n')),
    }
    
    if not template or not template.strip():
        result["valid"] = False
        result["errors"].append("Template is empty")
        return result
    
    # Extract all template variables
    variables = re.findall(r'\{\{\s*([^}]+)\s*\}\}', template)
    result["variables"] = set(var.strip() for var in variables)
    
    # Check for malformed template syntax
    malformed = re.findall(r'\{[^{]|\}[^}]', template)
    if malformed:
        result["warnings"].append("Possible malformed template syntax found")
    
    # Check for very long variables (might be accidents)
    for var in result["variables"]:
        if len(var) > 50:
            result["warnings"].append(f"Variable name is very long: {var[:30]}...")
        if ' ' in var and not var.replace('_', '').replace(' ', '').isalnum():
            result["warnings"].append(f"Variable name contains unusual characters: {var}")
    
    # Check template size
    if result["word_count"] < 10:
        result["warnings"].append("Template is very short")
    elif result["word_count"] > 1000:
        result["warnings"].append("Template is very long")
    
    return result


def render_prompt(name: str, variables: Optional[Dict[str, Any]] = None, strict: bool = False) -> str:
    """Load a prompt template and render it with variables.
    
    Args:
        name: Name of the prompt template (without .md extension)
        variables: Dictionary of variables to substitute in the template
        strict: If True, raises error for missing variables
        
    Returns:
        Rendered prompt with variables substituted
        
    Raises:
        FileNotFoundError: If template file doesn't exist
        ValueError: If strict=True and required variables are missing
    """
    template = load_prompt_template(name)
    
    # Validate template if in strict mode
    if strict:
        validation = validate_prompt_template(template)
        if not validation["valid"]:
            raise ValueError(f"Invalid template '{name}': {', '.join(validation['errors'])}")
    
    if variables:
        return substitute_variables(template, variables, strict=strict)
    return template


def list_prompt_templates() -> list[str]:
    """List all available prompt template names (without .md extension).
    
    Returns:
        List of template names
    """
    prompts_path = prompts_dir()
    if not prompts_path.exists():
        return []
    return [p.stem for p in prompts_path.glob("*.md")]
