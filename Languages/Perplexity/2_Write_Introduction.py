import os
import json
import time
from openai import OpenAI
from datetime import datetime
import logging
import glob
import re
from pathlib import Path
from typing import List, Dict, Optional

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    logger = logging.getLogger('')
    logger.handlers = [console_handler]
    return logger

logger = setup_logging()

def load_api_key(key_file_path):
    try:
        with open(key_file_path, 'r') as key_file:
            keys = key_file.read().strip().split('\n')
            api_keys = dict(key.split('=') for key in keys)
            perplexity_api_key = api_keys.get('PERPLEXITY_API_KEY')
        
        if not perplexity_api_key:
            raise ValueError("PERPLEXITY_API_KEY not found in the key file")
        
        logger.info("Perplexity API Key loaded successfully")
        return perplexity_api_key
    except Exception as e:
        logger.error(f"Error reading API key: {str(e)}")
        raise

def load_file(file_path):
    try:
        with open(file_path, "r", encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        raise

def extract_sections(content: str) -> Dict[str, str]:
    """Extract sections starting with ## from the research content.
    If no ## sections found, treat entire content as a single section."""
    sections = {}
    current_section = None
    current_content = []
    
    lines = content.split('\n')
    has_sections = any(line.startswith('## ') for line in lines)
    
    if not has_sections:
        # If no ## sections found, treat entire content as "Research Content"
        return {"Research Content": content}
    
    for line in lines:
        if line.startswith('## '):
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = line[3:].strip()
            current_content = []
        elif current_section:
            current_content.append(line)
    
    if current_section:
        sections[current_section] = '\n'.join(current_content).strip()
    
    return sections

def generate_section_prompt(section_name: str, section_content: str, fep_actinf_data: str) -> str:
    """Generate prompt for any curriculum section, focusing on maximum quality and depth."""
    return f"""Based on the following section content and core Active Inference material, create a comprehensive, 
in-depth expansion that maintains the highest standards of accuracy, clarity, and usefulness.

Section: {section_name}

Section Content:
{section_content}

Core FEP/Active Inference Content:
{fep_actinf_data}

Please provide an extensive, well-structured response that:
1. Maximizes depth and insight while maintaining clarity
2. Includes detailed explanations and examples
3. Provides extensive cross-references and hyperlinks to relevant resources
4. Connects ideas across different domains and perspectives
5. Anticipates and addresses potential questions
6. Builds clear conceptual frameworks
7. Offers practical applications and implementations
8. Maintains rigorous academic standards
9. Includes relevant citations and references
10. Provides clear learning pathways

Requirements:
- Aim for maximum possible length while maintaining quality and coherence
- Include extensive hyperlinks to papers, resources, and related concepts
- Use clear hierarchical structure with subsections
- Provide concrete examples and applications
- Include both theoretical depth and practical implementation
- Connect to broader contexts and implications
- Maintain precise technical accuracy
- Use clear, professional language
- Include relevant equations and formalizations where appropriate
- Suggest further reading and exploration paths

Format:
- Use Markdown formatting
- Include clear section headings
- Provide bullet points for key concepts
- Use code blocks for implementation examples
- Include blockquotes for important insights
- Add tables for comparisons where useful
- Use emphasis for key terms
- Include numbered lists for sequences
- Add horizontal rules for major transitions

The goal is to create the most thorough, high-quality content possible for this section, 
regardless of its specific type or position in the curriculum."""

def get_perplexity_response(client: OpenAI, prompt: str, system_description: str) -> Optional[str]:
    """Get response from Perplexity API with retries."""
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.1-sonar-small-128k-online",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert researcher and educator specializing in creating comprehensive, "
                                 "high-quality technical content. Your goal is to provide the most thorough, accurate, "
                                 "and well-structured information possible, with extensive references and practical applications."
                    },
                    {"role": "user", "content": prompt}
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"API call failed (attempt {attempt + 1}): {e}")
                time.sleep(retry_delay * (attempt + 1))
            else:
                logger.error(f"API call failed after {max_retries} attempts: {e}")
                raise
    return None

def save_section(output_dir: str, entity_name: str, section_name: str, content: str):
    """Save a curriculum section to entity-specific directory."""
    try:
        # Create entity-specific directory
        entity_dir = os.path.join(output_dir, entity_name)
        os.makedirs(entity_dir, exist_ok=True)
        
        # Save section file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{section_name.lower().replace(' ', '_')}_{timestamp}.md"
        file_path = os.path.join(entity_dir, filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# {section_name}\n\n")
            f.write(content)
        
        logger.info(f"Saved section {section_name} to: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Error saving section {section_name}: {e}")
        raise

def concatenate_sections(entity_dir: str, sections: Dict[str, str]) -> str:
    """Combine all sections into a single curriculum document."""
    combined_content = []
    
    # Add metadata header
    combined_content.append("---")
    combined_content.append(f"generated: {datetime.now().isoformat()}")
    combined_content.append(f"entity: {os.path.basename(entity_dir)}")
    combined_content.append("---\n")
    
    # Add each section in order
    for section_name, content in sections.items():
        combined_content.append(f"# {section_name}\n")
        combined_content.append(content)
        combined_content.append("\n---\n")
    
    return "\n".join(combined_content)

def save_complete_curriculum(output_dir: str, entity_name: str, sections: Dict[str, str]):
    """Save the complete curriculum with all sections."""
    try:
        entity_dir = os.path.join(output_dir, entity_name)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save combined Markdown
        md_filename = f"complete_curriculum_{timestamp}.md"
        md_path = os.path.join(entity_dir, md_filename)
        
        combined_content = concatenate_sections(entity_dir, sections)
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(combined_content)
        
        # Save JSON version
        json_filename = f"complete_curriculum_{timestamp}.json"
        json_path = os.path.join(entity_dir, json_filename)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": timestamp,
                "entity_name": entity_name,
                "sections": sections,
                "metadata": {
                    "version": "1.0",
                    "generation_date": datetime.now().isoformat(),
                    "file_type": "complete_curriculum"
                }
            }, f, indent=2)
        
        logger.info(f"Saved complete curriculum:")
        logger.info(f"  - Markdown: {md_path}")
        logger.info(f"  - JSON: {json_path}")
        
        return md_path
    except Exception as e:
        logger.error(f"Error saving complete curriculum: {e}")
        raise

def process_research_file(client: OpenAI, research_file: str, fep_actinf_file: str, output_dir: str) -> Optional[str]:
    """Process a research file and generate section-by-section curriculum."""
    try:
        # Load content
        research_content = load_file(research_file)
        fep_actinf_data = load_file(fep_actinf_file)
        
        if not research_content or not fep_actinf_data:
            logger.error(f"Failed to load required files for {research_file}")
            return None
        
        # Extract entity name and sections
        entity_name = Path(research_file).stem.split('_research_')[0]
        sections = extract_sections(research_content)
        
        if not sections:
            logger.error(f"No sections found in {research_file}")
            return None
        
        generated_sections = {}
        
        # Process each section
        for section_name, content in sections.items():
            try:
                logger.info(f"Processing section: {section_name} for {entity_name}")
                
                prompt = generate_section_prompt(section_name, content, fep_actinf_data)
                if not prompt:
                    logger.warning(f"Skipping section {section_name} - no prompt template available")
                    continue
                
                # Use consistent system description
                system_description = ("You are an expert researcher and educator specializing in creating comprehensive, "
                                   "high-quality technical content. Your goal is to provide the most thorough, accurate, "
                                   "and well-structured information possible, with extensive references and practical applications.")
                
                section_content = get_perplexity_response(client, prompt, system_description)
                if section_content:
                    # Save individual section
                    save_section(output_dir, entity_name, section_name, section_content)
                    generated_sections[section_name] = section_content
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error processing section {section_name}: {e}")
                continue
        
        if generated_sections:
            # Save complete curriculum
            return save_complete_curriculum(output_dir, entity_name, generated_sections)
        
        return None
        
    except Exception as e:
        logger.error(f"Error processing {research_file}: {e}")
        return None

def main():
    logger = setup_logging()
    
    # Setup paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    key_file_path = os.path.join(script_dir, "RR_LLM_keys.key")
    
    # Define input/output paths
    base_dir = os.path.join(script_dir, '..')
    audience_research_dir = os.path.join(base_dir, 'Inputs_and_Outputs', 'Audience_Research')
    domain_research_dir = os.path.join(base_dir, 'Inputs_and_Outputs', 'Domain_Research')
    fep_actinf_file = os.path.join(base_dir, 'Inputs_and_Outputs', 'Domain', 'Synthetic_FEP-ActInf.md')
    output_dir = os.path.join(base_dir, 'Inputs_and_Outputs', 'Written_Curriculums')
    
    # Create necessary directories
    os.makedirs(audience_research_dir, exist_ok=True)
    os.makedirs(domain_research_dir, exist_ok=True)
    os.makedirs(os.path.dirname(fep_actinf_file), exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Initialize API client
        perplexity_api_key = load_api_key(key_file_path)
        client = OpenAI(
            api_key=perplexity_api_key,
            base_url="https://api.perplexity.ai"
        )
        
        success_count = 0
        error_count = 0
        
        # Process audience research
        for research_file in glob.glob(os.path.join(audience_research_dir, '*_research_*.md')):
            try:
                logger.info(f"Processing audience research: {research_file}")
                result = process_research_file(client, research_file, fep_actinf_file, output_dir)
                if result:
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                logger.error(f"Failed to process audience research {research_file}: {e}")
                error_count += 1
                continue
        
        # Process domain research
        for research_file in glob.glob(os.path.join(domain_research_dir, '*_research_*.md')):
            try:
                logger.info(f"Processing domain research: {research_file}")
                result = process_research_file(client, research_file, fep_actinf_file, output_dir)
                if result:
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                logger.error(f"Failed to process domain research {research_file}: {e}")
                error_count += 1
                continue
        
        logger.info(f"Curriculum generation complete:")
        logger.info(f"  - Successful: {success_count}")
        logger.info(f"  - Failed: {error_count}")
        
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        raise

if __name__ == "__main__":
    main()
