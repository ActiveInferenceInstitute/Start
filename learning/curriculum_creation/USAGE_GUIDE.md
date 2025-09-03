an# Curriculum Creation Usage Guide

This guide provides step-by-step instructions for using the Active Inference curriculum creation scripts, from initial setup to final output generation.

## Quick Start

### 1. Prerequisites
Ensure you have the following:
- Python 3.11+ installed
- API keys for Perplexity and OpenRouter
- Input data files in the correct structure

### 2. Environment Setup
```bash
# Clone the repository and navigate to the project
cd /path/to/start

# Install dependencies
uv sync --all-extras --dev

# Set up environment variables
export PERPLEXITY_API_KEY="your-perplexity-api-key"
export OPENROUTER_API_KEY="your-openrouter-api-key"

# Optional: Configure specific models
export PERPLEXITY_MODEL="llama-3.1-sonar-small-128k-online"
export OPENROUTER_MODEL="anthropic/claude-3.5-sonnet"
```

### 3. Prepare Input Data
Create the required input directory structure:

```
Languages/
└── Inputs_and_Outputs/
    ├── Domain/
    │   ├── Synthetic_FEP-ActInf.md          # Core FEP content
    │   ├── Synthetic_Neuroscience.md        # Domain example
    │   └── Synthetic_MachineLearning.md     # Domain example
    └── Entity/
        ├── data_scientist.py                # Entity example
        └── neuroscientist.py               # Entity example
```

**Domain Files** should contain:
- Comprehensive domain descriptions
- Key concepts and methodologies
- Professional backgrounds and requirements
- Current challenges and opportunities

**Entity Files** should contain:
- Target audience descriptions
- Learning preferences and goals
- Background knowledge and expertise
- Specific use cases and applications

## Step-by-Step Workflow

### Step 1: Domain Research
Analyze domain characteristics and generate domain-specific curriculum foundations.

```bash
cd learning/curriculum_creation
python 1_Research_Domain.py
```

**What it does**:
- Reads domain files from `Languages/Inputs_and_Outputs/Domain/`
- Uses Perplexity API for online research and analysis
- Generates comprehensive domain analysis reports
- Creates initial curriculum structures tailored to each domain
- Saves results to `data/domain_research/`

**Expected outputs**:
```
data/domain_research/
├── Synthetic_Neuroscience_research_20240315_143022.json
├── Synthetic_Neuroscience_research_20240315_143022.md
├── Synthetic_MachineLearning_research_20240315_143155.json
└── Synthetic_MachineLearning_research_20240315_143155.md
```

**Monitoring progress**:
- Check logs for processing status
- Verify JSON files contain structured data
- Review Markdown files for readability

### Step 2: Entity Research
Analyze target audiences to create personalized curriculum recommendations.

```bash
python 1_Research_Entity.py
```

**What it does**:
- Reads entity files from `Languages/Inputs_and_Outputs/Entity/`
- Analyzes audience characteristics and learning needs
- Generates personalized curriculum recommendations
- Saves audience research to `data/audience_research/`

**Expected outputs**:
```
data/audience_research/
├── data_scientist_research_20240315.json
└── neuroscientist_research_20240315.json
```

**Key features analyzed**:
- Educational background and expertise
- Learning preferences and cognitive style
- Existing knowledge connections to Active Inference
- Optimal learning pathways and strategies

### Step 3: Curriculum Generation
Convert research reports into comprehensive Active Inference curricula.

```bash
python 2_Write_Introduction.py
```

**What it does**:
- Processes research files from both domain and audience research
- Uses OpenRouter API for high-quality content generation
- Creates modular curriculum sections with detailed content
- Generates complete curriculum packages
- Saves curricula to `data/written_curriculums/`

**Expected outputs**:
```
data/written_curriculums/
├── data_scientist/
│   ├── background_analysis_20240315_150322.md
│   ├── learning_strategy_20240315_150422.md
│   ├── curriculum_recommendations_20240315_150522.md
│   ├── complete_curriculum_20240315_150622.md
│   └── complete_curriculum_20240315_150622.json
└── neuroscientist/
    ├── background_analysis_20240315_150722.md
    ├── learning_strategy_20240315_150822.md
    ├── curriculum_recommendations_20240315_150922.md
    ├── complete_curriculum_20240315_151022.md
    └── complete_curriculum_20240315_151022.json
```

**Content structure**:
Each curriculum includes:
- Domain-specific introduction and motivation
- Conceptual foundations with relevant analogies
- Technical framework adapted to audience
- Practical applications and use cases
- Advanced topics and future directions

### Step 4: Visualization Generation
Create PNG charts and Mermaid diagrams to visualize curriculum structure and metrics.

```bash
python 3_Introduction_Visualizations.py
```

**Advanced usage**:
```bash
# Custom input/output directories
python 3_Introduction_Visualizations.py --input /path/to/curricula --output /path/to/visualizations

# Using default data directories
python 3_Introduction_Visualizations.py
```

**What it does**:
- Analyzes curriculum content for metrics and structure
- Generates comprehensive PNG charts using matplotlib/seaborn
- Creates Mermaid diagrams for learning flow visualization
- Produces JSON files with detailed metrics data
- Saves visualizations to `data/visualizations/`

**Expected outputs**:
```
data/visualizations/
├── curriculum_metrics.png              # Comprehensive metrics dashboard
├── curriculum_structure.mmd            # Overall curriculum structure
├── data_scientist_flow.mmd             # Learning flow diagram
├── neuroscientist_flow.mmd             # Learning flow diagram
└── curriculum_metrics.json             # Detailed metrics data
```

**Visualization features**:
- **Metrics Charts**: Word counts, section analysis, technical content distribution
- **Flow Diagrams**: Learning progression paths with milestones
- **Structure Diagrams**: Overall curriculum organization and relationships
- **Analytics Data**: Detailed JSON metrics for further analysis

### Step 5: Translation
Translate curricula into multiple configured languages.

```bash
python 4_Translate_Introductions.py
```

**Advanced usage**:
```bash
# Translate specific languages only
python 4_Translate_Introductions.py --languages Spanish French German

# Custom input/output directories
python 4_Translate_Introductions.py --input /path/to/curricula --output /path/to/translations

# Combine options
python 4_Translate_Introductions.py --input custom_curricula --output custom_translations --languages Chinese Arabic Hindi
```

**What it does**:
- Loads target languages from `data/config/languages.yaml`
- Validates requested languages against available options
- Uses OpenRouter API for high-quality translation
- Applies proper script mappings and cultural adaptations
- Saves translated curricula to `data/translated_curriculums/`

**Expected outputs**:
```
data/translated_curriculums/
├── chinese/
│   ├── data_scientist_curriculum_chinese_20240315_160122.md
│   └── neuroscientist_curriculum_chinese_20240315_160222.md
├── spanish/
│   ├── data_scientist_curriculum_spanish_20240315_160322.md
│   └── neuroscientist_curriculum_spanish_20240315_160422.md
└── french/
    ├── data_scientist_curriculum_french_20240315_160522.md
    └── neuroscientist_curriculum_french_20240315_160622.md
```

## Configuration

### Language Configuration
Edit `data/config/languages.yaml` to customize target languages:

```yaml
target_languages:
  - Chinese      # Simplified Chinese by default
  - Spanish      # Standard Spanish
  - Arabic       # Modern Standard Arabic
  - Hindi        # Devanagari script
  - French       # Standard French
  - Japanese     # Standard Japanese
  - German       # Standard German
  - Russian      # Cyrillic script
  - Portuguese   # Standard Portuguese
  - Swahili      # Standard Swahili
  - Tagalog      # Standard Tagalog

script_mappings:
  Arabic: "Modern Standard Arabic"
  Chinese: "Simplified Chinese"
  Hindi: "Devanagari"
  Japanese: "Standard Japanese"
  # ... additional mappings
```

### Prompt Customization
Customize generation prompts in `data/prompts/`:

**research_domain_analysis.md**: Controls domain analysis depth and focus
**research_domain_curriculum.md**: Shapes curriculum structure and content
**research_entity.md**: Defines audience analysis approach
**curriculum_section.md**: Templates for individual curriculum sections
**translation.md**: Translation quality and cultural adaptation guidelines

### Model Configuration
Override default models via environment variables:

```bash
# For research tasks (requires online capability)
export PERPLEXITY_MODEL="llama-3.1-sonar-large-128k-online"

# For content generation and translation
export OPENROUTER_MODEL="anthropic/claude-3.5-sonnet"
export OPENROUTER_MODEL="openai/gpt-4-turbo-preview"
```

## Monitoring and Debugging

### Progress Monitoring
All scripts provide detailed logging:

```bash
# Run with verbose output
python 1_Research_Domain.py 2>&1 | tee domain_research.log

# Monitor in real-time
tail -f domain_research.log
```

### Common Success Indicators

**Domain Research**:
- ✅ "Found N domain files to process"
- ✅ "Successfully processed: {domain_name}"
- ✅ "Domain analysis completed: N/N successful"

**Entity Research**:
- ✅ "Found N entity files to process"
- ✅ "Successfully processed: {entity_name}"
- ✅ "Entity research completed: N/N successful"

**Curriculum Generation**:
- ✅ "Processing N audience research files"
- ✅ "Processing N domain research files"
- ✅ "Successfully processed: {research_file}"
- ✅ "Generated curricula saved to: {output_dir}"

**Visualization**:
- ✅ "Found N curricula to visualize"
- ✅ "Created metrics chart: {path}"
- ✅ "Created structure diagram: {path}"
- ✅ "Visualization generation completed successfully"

**Translation**:
- ✅ "Target languages: {language_list}"
- ✅ "Successful translations: N"
- ✅ "Translated curricula saved to: {output_dir}"

### Error Troubleshooting

The curriculum creation scripts now provide enhanced error handling and validation:

**Configuration Errors**:
```
Error: "Domains configuration file not found"
Solution: The script will show you exactly what structure is needed:
  domains:
    - name: example_domain
      description: Example domain description
      category: general
      keywords: [keyword1, keyword2]
      priority: medium
```

**API Connection Issues**:
```
Error: "PERPLEXITY_API_KEY appears to be invalid (too short)"
Solution: Check your API key format - it should be at least 10 characters
Also ensure environment variables are properly set:
export PERPLEXITY_API_KEY="your-key-here"
export OPENROUTER_API_KEY="your-key-here"
```

**Content Validation Warnings**:
```
Warning: "Content is short (45 words, minimum 100)"
Warning: "Sections are very short on average"
Warning: "Content may contain repetitive text"
These warnings help identify quality issues but don't stop processing
```

**File Processing Errors**:
```
Error: "Research file not found: /path/to/file"
Solution: Scripts now validate file existence and provide full paths
Check that your input directories contain the expected files
```

**API Retry Logic**:
```
Info: "API request failed (attempt 1/3): rate limit exceeded"
Info: "Retrying in 2 seconds..."
The scripts now automatically retry failed requests with exponential backoff
```

**Progress Tracking**:
```
Info: "Processing domain 3/10: biochemistry"
Info: "Processing entity research 2/5: karl_friston"
All scripts now show clear progress indicators
```

## Quality Assurance

### Content Validation
After generation, validate outputs:

1. **Check file completeness**:
   ```bash
   find data/ -name "*.md" -exec wc -l {} + | sort -n
   ```

2. **Validate JSON structure**:
   ```bash
   find data/ -name "*.json" -exec python -m json.tool {} \; > /dev/null
   ```

3. **Review content quality**:
   - Open sample Markdown files
   - Check for coherent structure and content
   - Verify domain-specific terminology usage

### Metrics Analysis
Use the generated metrics to assess quality:

```python
import json

# Load curriculum metrics
with open('data/visualizations/curriculum_metrics.json', 'r') as f:
    metrics = json.load(f)

# Analyze curriculum characteristics
for curriculum in metrics:
    print(f"Entity: {curriculum['entity_name']}")
    print(f"  Sections: {curriculum['section_count']}")
    print(f"  Learning objectives: {curriculum['objectives_count']}")
    print(f"  Code examples: {curriculum['code_block_count']}")
    print(f"  Math expressions: {curriculum['math_expressions_count']}")
    print(f"  Words per section: {curriculum['words_per_section']:.1f}")
    print()
```

## Advanced Usage

### Batch Processing
Process multiple datasets efficiently:

```bash
#!/bin/bash
# batch_process.sh

# Set up environment
export PERPLEXITY_API_KEY="your-key"
export OPENROUTER_API_KEY="your-key"

# Process multiple domain sets
for domain_set in neuroscience machine_learning biology psychology; do
    echo "Processing domain set: $domain_set"
    
    # Switch to domain-specific input
    cp -r "inputs/${domain_set}" "Languages/Inputs_and_Outputs/"
    
    # Run full pipeline
    python 1_Research_Domain.py
    python 1_Research_Entity.py
    python 2_Write_Introduction.py
    python 3_Introduction_Visualizations.py
    python 4_Translate_Introductions.py
    
    # Archive results
    mv data "results/${domain_set}_$(date +%Y%m%d_%H%M%S)"
    mkdir -p data/{domain_research,audience_research,written_curriculums,visualizations,translated_curriculums}
done
```

### Custom Integration
Integrate with external systems:

```python
# custom_integration.py
import json
import subprocess
from pathlib import Path

def run_curriculum_pipeline(domain_files, entity_files, output_dir):
    """Run the full curriculum generation pipeline with custom inputs."""
    
    # Prepare input directories
    setup_inputs(domain_files, entity_files)
    
    # Run pipeline
    steps = [
        "1_Research_Domain.py",
        "1_Research_Entity.py", 
        "2_Write_Introduction.py",
        "3_Introduction_Visualizations.py",
        "4_Translate_Introductions.py"
    ]
    
    results = {}
    for step in steps:
        result = subprocess.run(
            ["python", step], 
            capture_output=True, 
            text=True,
            cwd="learning/curriculum_creation"
        )
        results[step] = {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    # Collect outputs
    return collect_results(output_dir)

def setup_inputs(domain_files, entity_files):
    """Set up input files for processing."""
    input_dir = Path("Languages/Inputs_and_Outputs")
    
    # Copy domain files
    domain_dir = input_dir / "Domain"
    domain_dir.mkdir(parents=True, exist_ok=True)
    for domain_file in domain_files:
        shutil.copy(domain_file, domain_dir)
    
    # Copy entity files
    entity_dir = input_dir / "Entity"  
    entity_dir.mkdir(parents=True, exist_ok=True)
    for entity_file in entity_files:
        shutil.copy(entity_file, entity_dir)

def collect_results(output_dir):
    """Collect all generated results."""
    results = {
        "curricula": list(Path("data/written_curriculums").rglob("*.md")),
        "visualizations": list(Path("data/visualizations").rglob("*")),
        "translations": list(Path("data/translated_curriculums").rglob("*.md")),
        "metrics": "data/visualizations/curriculum_metrics.json"
    }
    
    # Copy to custom output directory if specified
    if output_dir:
        shutil.copytree("data", output_dir, dirs_exist_ok=True)
    
    return results
```

## Performance Optimization

### API Rate Limiting
The scripts include built-in rate limiting, but for heavy usage:

1. **Monitor API usage**:
   ```bash
   # Track API calls in logs
   grep -c "API call" *.log
   ```

2. **Batch processing delays**:
   ```python
   # Add delays between batches
   import time
   time.sleep(2)  # 2-second delay between API calls
   ```

3. **Parallel processing**:
   ```bash
   # Process multiple domains in parallel
   python 1_Research_Domain.py &
   python 1_Research_Entity.py &
   wait
   ```

### Resource Management
For large datasets:

1. **Memory optimization**:
   - Process files in batches
   - Clear intermediate variables
   - Use generators for large file lists

2. **Storage management**:
   ```bash
   # Compress old results
   tar -czf "results_$(date +%Y%m%d).tar.gz" data/
   rm -rf data/*
   ```

3. **Network optimization**:
   - Use CDN endpoints when available
   - Cache API responses locally
   - Implement retry mechanisms with exponential backoff

This completes the comprehensive usage guide for the Active Inference curriculum creation scripts.
