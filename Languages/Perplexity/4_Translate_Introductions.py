import os
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from openai import OpenAI
import time
from typing import List, Dict, Optional
import re

# Target Languages Configuration
TARGET_LANGUAGES = [
    # 'English',      
    'Chinese',      
    'Spanish',      
    'Arabic',       
    'Hindi',       
    'French',      
    'Japanese',     
    'German',      
    'Russian',    
    'Portuguese',   
    'Swahili',
    'Tagalog'
    # 'Afrikaans',
    # 'Albanian',
    # 'Amharic',
    # 'Armenian',
    # 'Assamese',
    # 'Azerbaijani',
    # 'Basque',
    # 'Bengali',
    # 'Bhojpuri',
    # 'Bulgarian',
    # 'Burmese',
    # 'Catalan',
    # 'Cebuano',
    # 'Croatian',
    # 'Czech',
    # 'Danish',
    # 'Dutch',
    # 'Estonian',
    # 'Finnish',
    # 'Galician',
    # 'Georgian',
    # 'Greek',
    # 'Gujarati',
    # 'Hausa',
    # 'Hebrew',
    # 'Hungarian',
    # 'Icelandic',
    # 'Igbo',
    # 'Indonesian',
    # 'Irish',
    # 'Italian',
    # 'Javanese',
    # 'Kannada',
    # 'Kazakh',
    # 'Khmer',
    # 'Korean',
    # 'Kurdish',
    # 'Kyrgyz',
    # 'Lao',
    # 'Latin',
    # 'Latvian',
    # 'Lithuanian',
    # 'Macedonian',
    # 'Maithili',
    # 'Malay',
    # 'Malayalam',
    # 'Maltese',
    # 'Marathi',
    # 'Mongolian',
    # 'Nepali',
    # 'Norwegian',
    # 'Odia',
    # 'Pashto',
    # 'Persian',
    # 'Polish',
    # 'Punjabi',
    # 'Romanian',
    # 'Sanskrit',
    # 'Serbian',
    # 'Sinhala',
    # 'Slovak',
    # 'Slovenian',
    # 'Somali',
    # 'Sundanese',
    # 'Swedish',
    # 'Tamil',
    # 'Telugu',
    # 'Thai',
    # 'Turkish',
    # 'Ukrainian',
    # 'Urdu',
    # 'Uzbek',
    # 'Vietnamese',
    # 'Welsh',
    # 'Yiddish',
    # 'Yoruba',
    # 'Zulu'
]

# Language Script Mappings
SCRIPT_MAPPINGS = {
    'Arabic': 'Modern Standard Arabic',  # Default to MSA
    'Chinese': 'Simplified Chinese',  # Default to Simplified Chinese
    'Kurdish': 'Sorani',  # Default Kurdish dialect
    'Mongolian': 'Cyrillic',  # Default to Cyrillic script
    'Persian': 'Farsi',  # Default Persian dialect
    'Serbian': 'Latin',  # Default to Latin script
    'Chinese_Traditional': 'Traditional Chinese',  # Alternative Chinese script
    'Japanese': 'Standard Japanese',  # Default to standard Japanese
    'Korean': 'Hangul',  # Default to Hangul script
    'Urdu': 'Nastaliq',  # Default Urdu script
    'Hindi': 'Devanagari',  # Default Hindi script
    'Bengali': 'Bengali Script',  # Default Bengali script
    'Thai': 'Thai Script',  # Default Thai script
    'Hebrew': 'Hebrew Script',  # Default Hebrew script
    'Georgian': 'Mkhedruli',  # Default Georgian script
    'Armenian': 'Armenian Script',  # Default Armenian script
    'Greek': 'Greek Script',  # Default Greek script
    'Khmer': 'Khmer Script',  # Default Khmer script
    'Lao': 'Lao Script',  # Default Lao script
    'Myanmar': 'Myanmar Script',  # Default Burmese script
    'Sinhala': 'Sinhala Script',  # Default Sinhala script
    'Tamil': 'Tamil Script',  # Default Tamil script
    'Telugu': 'Telugu Script',  # Default Telugu script
    'Gujarati': 'Gujarati Script',  # Default Gujarati script
    'Kannada': 'Kannada Script',  # Default Kannada script
    'Malayalam': 'Malayalam Script',  # Default Malayalam script
    'Tibetan': 'Tibetan Script',  # Default Tibetan script
    'Yiddish': 'Hebrew Script',  # Default script for Yiddish
    'Sanskrit': 'Devanagari'  # Default Sanskrit script
}

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_api_key(key_file_path: str) -> str:
    """Load Perplexity API key from file."""
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

def get_language_script(language: str) -> str:
    """Get the appropriate script/variant for a language."""
    return SCRIPT_MAPPINGS.get(language, language)

def generate_translation_prompt(content: str, target_language: str) -> str:
    """Generate prompt for curriculum translation."""
    language_script = get_language_script(target_language)
    
    return f"""Please translate the following curriculum into {language_script}. 
Maintain all formatting, including Markdown syntax, code blocks, and mathematical notation.
Ensure technical terms are accurately translated while preserving their scientific meaning.
If certain technical terms should remain in English, keep them as is.

Curriculum Content:
{content}

Translation Guidelines:
1. Preserve all Markdown formatting and structure
2. Maintain mathematical equations and formulas
3. Keep code blocks unchanged
4. Preserve hyperlinks and references
5. Keep technical terms accurate and consistent
6. Maintain section numbering and hierarchy
7. Preserve any metadata or front matter
8. Keep citations in their original format
9. Use appropriate script and dialect as specified
10. Maintain proper text direction (RTL for Arabic, Hebrew, etc.)
11. Handle language-specific formatting requirements
12. Preserve any cultural context while adapting appropriately

Please provide a high-quality, professional translation that maintains the academic and technical integrity of the content.
For technical terms without direct translations, provide the English term followed by a brief explanation in {language_script}."""

def translate_curriculum(client: OpenAI,
                       content: str,
                       target_language: str,
                       max_chunk_size: int = 4000) -> str:
    """Translate curriculum content using Perplexity API."""
    try:
        # Split content into manageable chunks
        chunks = split_content_into_chunks(content, max_chunk_size)
        translated_chunks = []
        
        for i, chunk in enumerate(chunks, 1):
            logger.info(f"Translating chunk {i} of {len(chunks)} to {target_language}")
            
            prompt = generate_translation_prompt(chunk, target_language)
            
            messages = [
                {
                    "role": "system",
                    "content": f"You are an expert translator specializing in academic and technical content translation to {target_language}, with deep understanding of the target language's cultural and academic context."
                },
                {"role": "user", "content": prompt}
            ]
            
            try:
                response = client.chat.completions.create(
                    model="llama-3.1-sonar-small-128k-online",
                    messages=messages,
                )
                
                translated_chunk = response.choices[0].message.content
                translated_chunks.append(translated_chunk)
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error translating chunk {i}: {e}")
                # Return partial translation if some chunks were successful
                if translated_chunks:
                    logger.warning(f"Returning partial translation due to error in chunk {i}")
                    break
                raise
        
        # Combine translated chunks
        full_translation = "\n".join(translated_chunks)
        
        return full_translation
        
    except Exception as e:
        logger.error(f"Error in translation: {e}")
        raise

def split_content_into_chunks(content: str, max_chunk_size: int) -> List[str]:
    """Split content into chunks while preserving Markdown structure."""
    chunks = []
    current_chunk = []
    current_size = 0
    
    # Split by headers first
    sections = re.split(r'(^#{1,6}\s.*$)', content, flags=re.MULTILINE)
    
    for section in sections:
        section_size = len(section)
        
        if current_size + section_size > max_chunk_size and current_chunk:
            # Save current chunk
            chunks.append('\n'.join(current_chunk))
            current_chunk = []
            current_size = 0
        
        current_chunk.append(section)
        current_size += section_size
    
    # Add any remaining content
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    return chunks

def save_translation(output_dir: str, entity_name: str, language: str, content: str) -> None:
    """Save translated curriculum to file."""
    try:
        # Create language-specific subdirectory
        lang_dir = os.path.join(output_dir, language.lower())
        os.makedirs(lang_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{entity_name}_curriculum_{language.lower()}_{timestamp}.md"
        file_path = os.path.join(lang_dir, filename)
        
        # Add language metadata header
        full_content = f"""---
language: {language}
translation_date: {datetime.now().isoformat()}
original_entity: {entity_name}
script: {get_language_script(language)}
---

{content}"""
        
        # Save translation
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        logger.info(f"Saved {language} translation to: {file_path}")
        
    except Exception as e:
        logger.error(f"Error saving {language} translation: {e}")

def process_translations(client: OpenAI,
                        curriculum_dir: str,
                        output_dir: str,
                        target_languages: List[str] = TARGET_LANGUAGES) -> None:
    """Process translations for all curriculums."""
    try:
        # Get all complete curriculum files
        curriculum_files = list(Path(curriculum_dir).glob("*/complete_curriculum_*.md"))
        total_success = 0
        total_failed = 0
        
        for curr_file in curriculum_files:
            try:
                # Extract entity name from parent directory
                entity_name = curr_file.parent.name
                logger.info(f"Processing translations for {entity_name}")
                
                # Load curriculum content
                with open(curr_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                if not content:
                    logger.error(f"Empty curriculum file: {curr_file}")
                    continue
                
                # Process each target language
                for language in target_languages:
                    try:
                        logger.info(f"Translating {entity_name} curriculum to {language}")
                        
                        # Skip if translation already exists
                        lang_dir = os.path.join(output_dir, language.lower())
                        if os.path.exists(lang_dir) and list(Path(lang_dir).glob(f"{entity_name}_curriculum_{language.lower()}_*.md")):
                            logger.info(f"Translation for {language} already exists, skipping...")
                            continue
                        
                        # Translate content
                        translated_content = translate_curriculum(
                            client,
                            content,
                            language
                        )
                        
                        # Save translation
                        save_translation(
                            output_dir,
                            entity_name,
                            language,
                            translated_content
                        )
                        
                        total_success += 1
                        
                    except Exception as e:
                        logger.error(f"Error translating to {language}: {e}")
                        total_failed += 1
                        continue
                
            except Exception as e:
                logger.error(f"Error processing {curr_file}: {e}")
                continue
        
        if not curriculum_files:
            logger.warning("No complete curriculum files found")
        
        logger.info(f"Translation processing complete:")
        logger.info(f"  - Successful translations: {total_success}")
        logger.info(f"  - Failed translations: {total_failed}")
        
    except Exception as e:
        logger.error(f"Error in translation processing: {e}")
        raise

def main():
    """Main function to orchestrate curriculum translation."""
    parser = argparse.ArgumentParser(description="Translate curriculum content to multiple languages.")
    parser.add_argument("--input", default="Inputs_and_Outputs/Written_Curriculums",
                       help="Path to directory containing curriculum files")
    parser.add_argument("--output", default="Inputs_and_Outputs/Translated_Curriculums",
                       help="Path to save translated files")
    parser.add_argument("--languages", nargs='+',
                       help="List of target languages for translation (default: all supported languages)")
    args = parser.parse_args()
    
    try:
        # Setup paths
        script_dir = os.path.dirname(os.path.abspath(__file__))
        key_file_path = os.path.join(script_dir, "RR_LLM_keys.key")
        input_dir = os.path.join(script_dir, '..', args.input)
        output_dir = os.path.join(script_dir, '..', args.output)
        
        # Load API key and initialize client
        perplexity_api_key = load_api_key(key_file_path)
        client = OpenAI(
            api_key=perplexity_api_key,
            base_url="https://api.perplexity.ai"
        )
        
        # Use specified languages or all supported languages
        target_languages = args.languages if args.languages else TARGET_LANGUAGES
        
        # Process translations
        process_translations(
            client,
            input_dir,
            output_dir,
            target_languages
        )
        
        logger.info("Translation processing complete")
        
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        raise

if __name__ == "__main__":
    main()
