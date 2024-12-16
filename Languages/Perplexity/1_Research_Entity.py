import json
import os
from datetime import datetime
import traceback
import logging
from openai import OpenAI
import time

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

def generate_research_prompt(entity_data, fep_actinf_data):
    """Generate research prompt for understanding target audience perspective."""
    return f"""Research Task: Analyze the background and perspective of this target audience for creating a personalized Active Inference and Free Energy Principle curriculum.

Target Audience Information:
{entity_data}

Core FEP/Active Inference Content to be Taught:
{fep_actinf_data}

Please provide a comprehensive analysis covering:

1. Audience Background Analysis:
   - Academic and professional background
   - Current knowledge domains and expertise levels
   - Research interests and methodological experience
   - Learning style preferences and cognitive approaches
   - Potential knowledge gaps and prerequisites
   - Cultural and linguistic considerations
   - Professional goals and motivations

2. Conceptual Bridges:
   - Identify concepts from their domain that connect to FEP/Active Inference
   - Find analogies and metaphors that will resonate
   - Map familiar frameworks to FEP concepts
   - Highlight overlapping principles and methodologies
   - Connect to existing mental models
   - Build progressive understanding paths
   - Identify transferable skills and knowledge

3. Learning Challenges:
   - Potential conceptual hurdles and misconceptions
   - Mathematical/technical prerequisites
   - Areas needing extra support or scaffolding
   - Common misconceptions to address
   - Cognitive load considerations
   - Time management challenges
   - Resource accessibility issues

4. Engagement Opportunities:
   - Relevant applications in their field
   - Practical examples that will resonate
   - Project opportunities and hands-on exercises
   - Collaboration potential
   - Research integration possibilities
   - Career development opportunities
   - Community engagement paths

5. Resources and References:
   - Key papers aligned with their interests
   - Tools and software relevant to their work
   - Learning resources matching their level
   - Community connections and networks
   - Online courses and tutorials
   - Workshops and conferences
   - Mentorship opportunities

6. Recent Developments:
   - Latest publications in their field relating to FEP/Active Inference
   - Current debates and discussions
   - Emerging applications and tools
   - New methodological approaches
   - Recent success stories and case studies
   - Upcoming opportunities and events

7. Learning Environment Needs:
   - Preferred learning formats (online/offline)
   - Technical infrastructure requirements
   - Support system needs
   - Time commitment considerations
   - Assessment preferences
   - Feedback mechanisms
   - Collaboration tools

8. Success Metrics:
   - Key performance indicators
   - Learning outcome measurements
   - Progress tracking methods
   - Evaluation criteria
   - Portfolio development opportunities
   - Professional development goals
   - Research output potential

Please provide detailed, specific insights that will help create an effective, personalized curriculum. Include citations and links to relevant resources where applicable."""

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
            f.write(f"# {content['entity_name']} Research Report\n\n")
            f.write(f"**Date:** {content['timestamp'][:10]}\n")
            f.write(f"**Processing Time:** {content['processing_time']}\n\n")
            f.write("---\n\n")
            f.write(content['research_data'])
        logging.info(f"Saved Markdown report: {file_path}")
    except Exception as e:
        logging.error(f"Error saving Markdown report {filename}: {e}")
        traceback.print_exc()

def research_target_audience(client, entity_file, fep_actinf_file, output_dir):
    """Conduct research on a target audience for FEP/Active Inference curriculum."""
    try:
        # Load entity and FEP/ActInf data
        entity_data = load_file(entity_file)
        fep_actinf_data = load_file(fep_actinf_file)
        
        if not entity_data or not fep_actinf_data:
            raise ValueError("Failed to load required data files")
        
        entity_name = os.path.splitext(os.path.basename(entity_file))[0]
        
        # Generate research prompt
        prompt = generate_research_prompt(entity_data, fep_actinf_data)
        
        logging.info(f"Starting research for {entity_name}")
        start_time = time.time()
        
        # Get research from Perplexity
        system_description = "You are an expert researcher specializing in audience analysis and curriculum development for complex scientific concepts."
        research_content = get_perplexity_response(client, prompt, system_description)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        research_result = {
            "timestamp": datetime.now().isoformat(),
            "entity_name": entity_name,
            "research_data": research_content,
            "processing_time": f"{elapsed_time:.2f} seconds"
        }
        
        # Save both JSON and Markdown versions
        date_str = datetime.now().strftime('%Y%m%d')
        json_filename = f"{entity_name}_research_{date_str}.json"
        markdown_filename = f"{entity_name}_research_{date_str}.md"
        
        save_research_report(output_dir, json_filename, research_result)
        save_markdown_report(output_dir, markdown_filename, research_result)
        
        logging.info(f"Completed research for {entity_name}")
        logging.info(f"Time taken: {elapsed_time:.2f} seconds")
        
        return research_result
        
    except Exception as e:
        logging.error(f"Error researching {entity_name}: {e}")
        traceback.print_exc()
        return None

def main():
    """Main function to orchestrate target audience research."""
    logger = setup_logging()
    
    # Setup paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    key_file_path = os.path.join(script_dir, "RR_LLM_keys.key")
    
    # Define input/output paths
    entity_dir = os.path.join(script_dir, '..', 'Inputs_and_Outputs', 'Entity')
    fep_actinf_file = os.path.join(script_dir, '..', 'Inputs_and_Outputs', 'Domain', 'Synthetic_FEP-ActInf.md')
    output_dir = os.path.join(script_dir, '..', 'Inputs_and_Outputs', 'Audience_Research')
    
    try:
        # Initialize API client
        perplexity_api_key = load_api_key(key_file_path)
        client = OpenAI(
            api_key=perplexity_api_key,
            base_url="https://api.perplexity.ai"
        )
        
        # Get list of entity files
        entity_files = []
        for root, _, files in os.walk(entity_dir):
            for file in files:
                if file.endswith('.py'):
                    entity_files.append(os.path.join(root, file))
        
        # Process each entity
        for entity_file in entity_files:
            try:
                research_target_audience(client, entity_file, fep_actinf_file, output_dir)
            except Exception as e:
                logger.error(f"Failed to process {entity_file}: {e}")
                continue
        
        logger.info("All target audience research completed")
        
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        raise

if __name__ == "__main__":
    main()
