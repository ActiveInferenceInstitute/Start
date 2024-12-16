import json
import os
from datetime import datetime
import traceback
import logging
from openai import OpenAI
import time
from pathlib import Path

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    logger = logging.getLogger('')
    logger.handlers = [console_handler]
    return logger

def load_api_key(key_file_path):
    """Load API key from file."""
    try:
        with open(key_file_path, 'r') as key_file:
            keys = key_file.read().strip().split('\n')
            api_keys = dict(key.split('=') for key in keys)
            perplexity_api_key = api_keys.get('PERPLEXITY_API_KEY')
        
        if not perplexity_api_key:
            raise ValueError("PERPLEXITY_API_KEY not found in the key file")
        
        logging.info("Perplexity API Key loaded successfully")
        return perplexity_api_key
    except Exception as e:
        logging.error(f"Error reading API key: {str(e)}")
        raise

def load_file(file_path):
    """Load content from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logging.error(f"Error loading {file_path}: {e}")
        return None

def save_research_report(output_dir, filename, content):
    """Save research report to specified directory."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2)
        logging.info(f"Saved report: {file_path}")
    except Exception as e:
        logging.error(f"Error saving report {filename}: {e}")
        traceback.print_exc()

def generate_domain_analysis_prompt(domain_content: str) -> str:
    """Generate prompt to analyze domain content and identify key concepts and audience characteristics."""
    return f"""Analyze this domain content to understand the typical industry professional's background, knowledge, and perspective.

Domain Content:
{domain_content}

Please provide a comprehensive analysis covering:

1. Domain Expert Profile:
   - Typical educational background
   - Core knowledge areas and expertise
   - Common methodologies and frameworks used
   - Technical vocabulary and concepts
   - Professional goals and challenges
   - Industry context and trends
   - Learning preferences and approaches

2. Key Domain Concepts:
   - Fundamental principles and theories
   - Important methodologies and techniques
   - Standard tools and technologies
   - Common applications and use cases
   - Industry best practices
   - Current challenges and opportunities
   - Emerging trends and developments

3. Conceptual Bridges to Active Inference:
   - Parallel concepts between domain and Active Inference
   - Natural analogies and metaphors
   - Shared mathematical or theoretical foundations
   - Potential applications of Active Inference
   - Integration opportunities
   - Value propositions for the domain

4. Learning Considerations:
   - Existing knowledge that can be leveraged
   - Potential conceptual barriers
   - Required prerequisites
   - Optimal learning sequence
   - Practical application opportunities
   - Assessment approaches
   - Support needs

Please provide detailed insights that will help create an effective Active Inference curriculum for this domain's professionals."""

def generate_curriculum_prompt(domain_analysis: str, fep_actinf_data: str) -> str:
    """Generate prompt for domain-specific Active Inference curriculum."""
    return f"""Create a comprehensive introduction to Active Inference and the Free Energy Principle for domain professionals, based on the following analysis and core content.

Domain Analysis:
{domain_analysis}

Core FEP/Active Inference Content:
{fep_actinf_data}

Please create a detailed curriculum following this structure:

1. Domain-Specific Introduction (2 pages):
   - Welcome message acknowledging domain expertise
   - Relevance of Active Inference to the domain
   - Value proposition and potential applications
   - Connection to existing domain knowledge
   - Overview of learning journey
   - Success stories and examples

2. Conceptual Foundations (3 pages):
   - Core Active Inference concepts using domain analogies
   - Mathematical principles with domain-relevant examples
   - Practical applications in domain context
   - Integration with existing domain frameworks
   - Case studies from the domain
   - Interactive examples and exercises

3. Technical Framework (2 pages):
   - Mathematical formalization using domain notation
   - Computational aspects with domain tools
   - Implementation considerations
   - Integration strategies
   - Best practices and guidelines
   - Common pitfalls and solutions

4. Practical Applications (2 pages):
   - Domain-specific use cases
   - Implementation examples
   - Integration strategies
   - Project templates
   - Code examples
   - Evaluation methods
   - Success metrics

5. Advanced Topics (1 page):
   - Cutting-edge research relevant to domain
   - Future opportunities
   - Research directions
   - Collaboration possibilities
   - Resources for further learning
   - Community engagement

Required Elements:
1. Domain-specific terminology and examples
2. Clear connections to existing knowledge
3. Practical applications and exercises
4. Case studies from the domain
5. Code examples using domain tools
6. Assessment methods
7. Further resources

Please ensure the content is:
1. Technically accurate
2. Domain-relevant
3. Practically applicable
4. Well-structured
5. Engaging
6. Appropriately challenging
7. Implementation-focused

Target length: 10 pages with comprehensive coverage of all topics."""

def get_perplexity_response(client, prompt, system_description):
    """Get response from Perplexity API."""
    messages = [
        {
            "role": "system",
            "content": system_description
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    try:
        response = client.chat.completions.create(
            model="llama-3.1-sonar-small-128k-online",
            messages=messages,
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error getting Perplexity response: {e}")
        raise

def save_markdown_report(output_dir, filename, content):
    """Save research report as Markdown."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# {content['domain_name']} Domain Research Report\n\n")
            f.write(f"**Date:** {content['timestamp'][:10]}\n")
            f.write(f"**Processing Time:** {content['processing_time']}\n\n")
            f.write("---\n\n")
            f.write("## Domain Analysis\n\n")
            f.write(content['domain_analysis'])
            f.write("\n\n## Curriculum Content\n\n")
            f.write(content['curriculum_content'])
        logging.info(f"Saved Markdown report: {file_path}")
    except Exception as e:
        logging.error(f"Error saving Markdown report {filename}: {e}")
        traceback.print_exc()

def analyze_domain(client, domain_file: str, fep_actinf_file: str, output_dir: str):
    """Analyze domain content and create domain-specific Active Inference curriculum."""
    try:
        # Load domain and FEP/ActInf data
        domain_content = load_file(domain_file)
        fep_actinf_data = load_file(fep_actinf_file)
        
        if not domain_content or not fep_actinf_data:
            raise ValueError("Failed to load required data files")
        
        domain_name = Path(domain_file).stem
        
        # First, analyze the domain
        logging.info(f"Analyzing domain: {domain_name}")
        domain_prompt = generate_domain_analysis_prompt(domain_content)
        
        system_description = "You are an expert researcher specializing in domain analysis and curriculum development for complex scientific concepts."
        domain_analysis = get_perplexity_response(client, domain_prompt, system_description)
        
        # Then, generate domain-specific curriculum
        logging.info(f"Generating curriculum for {domain_name}")
        curriculum_prompt = generate_curriculum_prompt(domain_analysis, fep_actinf_data)
        
        system_description = f"You are an expert curriculum developer specializing in creating domain-specific introductions to Active Inference for {domain_name} professionals."
        curriculum_content = get_perplexity_response(client, curriculum_prompt, system_description)
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result = {
            "timestamp": datetime.now().isoformat(),
            "domain_name": domain_name,
            "domain_analysis": domain_analysis,
            "curriculum_content": curriculum_content,
            "processing_time": timestamp
        }
        
        # Save both JSON and Markdown versions
        json_filename = f"{domain_name}_research_{timestamp}.json"
        markdown_filename = f"{domain_name}_research_{timestamp}.md"
        
        save_research_report(output_dir, json_filename, result)
        save_markdown_report(output_dir, markdown_filename, result)
        
        logging.info(f"Completed analysis and curriculum for {domain_name}")
        
        return result
        
    except Exception as e:
        logging.error(f"Error analyzing domain {domain_name}: {e}")
        traceback.print_exc()
        return None

def main():
    """Main function to orchestrate domain analysis and curriculum generation."""
    logger = setup_logging()
    
    # Setup paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    key_file_path = os.path.join(script_dir, "RR_LLM_keys.key")
    
    # Define input/output paths
    domain_dir = os.path.join(script_dir, '..', 'Inputs_and_Outputs', 'Domain')
    fep_actinf_file = os.path.join(domain_dir, 'Synthetic_FEP-ActInf.md')
    output_dir = os.path.join(script_dir, '..', 'Inputs_and_Outputs', 'Domain_Research')
    
    try:
        # Initialize API client
        perplexity_api_key = load_api_key(key_file_path)
        client = OpenAI(
            api_key=perplexity_api_key,
            base_url="https://api.perplexity.ai"
        )
        
        # Get list of domain files
        domain_files = []
        for file in Path(domain_dir).glob("Synthetic_*.md"):
            if file.stem != "Synthetic_FEP-ActInf":  # Skip the FEP/ActInf file itself
                domain_files.append(str(file))
        
        if not domain_files:
            logger.error("No domain files found")
            return
        
        # Process each domain
        for domain_file in domain_files:
            try:
                analyze_domain(client, domain_file, fep_actinf_file, output_dir)
            except Exception as e:
                logger.error(f"Failed to process {domain_file}: {e}")
                continue
        
        logger.info("All domain analysis and curriculum generation completed")
        
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        raise

if __name__ == "__main__":
    main()
