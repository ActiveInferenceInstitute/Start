# Interactive Curriculum Generator Guide

## Quick Start - Interactive Mode

The `generate_custom_curriculum.py` script now runs **interactively by default**! Simply run:

```bash
python generate_custom_curriculum.py
```

## How It Works

### 1. Default Values
The script has sensible defaults set at the top:
```python
DEFAULT_DOMAIN = "biochemistry"
DEFAULT_ENTITY = "karl_friston"  
DEFAULT_LANGUAGE = "Spanish"
```

### 2. Interactive Prompts
When you run the script, you'll see prompts like:

```
🎯 Active Inference Curriculum Generator
==================================================
Press Enter to use default values, or type your custom choice.

📚 Select Domain (default: biochemistry)
Available domains: biochemistry, neuroscience, artificial_intelligence, psychology...
💡 Tip: You can also enter a new domain name to create a custom domain!
Domain [biochemistry]: 

👤 Select Target Entity (default: karl_friston)
Available entities: karl_friston, tulsi_gabbard, elon_musk...
💡 Tip: You can also enter a new entity name to create a custom target audience!
Entity [karl_friston]: 

🌍 Select Target Language (default: Spanish)
Available languages: Spanish, French, Chinese, Arabic, Hindi...
💡 Tip: You can also enter a new language name to create a custom translation target!
Language [Spanish]: 

✅ Selected Configuration:
   Domain: biochemistry
   Entity: karl_friston
   Language: Spanish

Proceed with this configuration? [Y/n]: 
```

### 3. Easy Usage
- **Press Enter** to use the default value shown in brackets
- **Type a custom value** to override the default
- **Create new entries** by typing names not in the existing options
- Invalid inputs are **validated and re-prompted**
- **Confirm your choices** before the pipeline starts

### 4. Creating Custom Entries
The script now allows you to create custom domains, entities, and languages on the fly!

#### Custom Domains
```
Domain [biochemistry]: art
🆕 'art' is not in the existing domains.
Create this as a new custom domain? [y/N]: y
✅ Created custom domain: 'art'
```

#### Custom Entities (Target Audiences)  
```
Entity [karl_friston]: artist
🆕 'artist' is not in the existing entities.
Create this as a new custom entity? [y/N]: y
Enter a brief description for 'artist': Professional visual artists working in galleries
✅ Created custom entity: 'artist' - Professional visual artists working in galleries
```

#### Custom Languages
```
Language [Spanish]: Portuguese
🆕 'Portuguese' is not in the existing languages.
Create this as a new custom language? [y/N]: y
✅ Created custom language: 'Portuguese'
🔤 Note: Translation quality may vary for custom languages not in the AI model's training.
```

## Example Usage Scenarios

### Use All Defaults
```bash
python generate_custom_curriculum.py
# Just press Enter three times, then Y to confirm
```

### Customize Domain Only
```bash
python generate_custom_curriculum.py
# Type: neuroscience
# Press Enter for entity (karl_friston)  
# Press Enter for language (Spanish)
# Type: Y to confirm
```

### Customize All Options
```bash
python generate_custom_curriculum.py
# Type: artificial_intelligence
# Type: elon_musk
# Type: Chinese
# Type: Y to confirm
```

### Create Custom Entries
```bash
python generate_custom_curriculum.py
# Type: art (new custom domain)
# Type: y to create custom domain
# Type: curator (new custom entity)
# Type: y to create custom entity
# Type: Museum curator specializing in contemporary art
# Type: Portuguese (new custom language)
# Type: y to create custom language
# Type: Y to confirm and proceed
```

## Command-Line Mode (Non-Interactive)

You can still use command-line arguments to skip interactive mode:

```bash
# Use specific configuration
python generate_custom_curriculum.py --domains neuroscience --entities tulsi_gabbard --languages French

# Force non-interactive with defaults
python generate_custom_curriculum.py --non-interactive

# Force interactive mode even with args
python generate_custom_curriculum.py --interactive
```

## What Happens Next

After confirming your configuration, the script will:

1. **🔬 Research Domain** - Analyze your chosen domain using Perplexity API
2. **👤 Research Entity** - Study your target entity/audience using Perplexity API  
3. **📝 Generate Curriculum** - Create tailored content using OpenRouter API
4. **📊 Create Visualizations** - Generate charts and diagrams
5. **🌍 Translate Content** - Translate to your chosen language

## Configuration Files

The script reads from these configuration files:
- `data/config/domains.yaml` - Available domains
- `data/config/entities.yaml` - Available entities/audiences
- `data/config/languages.yaml` - Available target languages

## Tips for Success

1. **Prerequisites**: Ensure you have your API keys set:
   ```bash
   export PERPLEXITY_API_KEY="your-key"
   export OPENROUTER_API_KEY="your-key"
   ```

2. **Check Available Options**: The script shows available choices from your config files

3. **Start Simple**: Use defaults first to test the pipeline, then customize

4. **Monitor Progress**: The script provides detailed logging throughout the process

5. **Results Location**: Generated content will be saved to:
   - `data/domain_research/` - Domain analysis
   - `data/audience_research/` - Entity analysis
   - `data/written_curriculums/` - Generated curricula
   - `data/visualizations/` - Charts and diagrams
   - `data/translated_curriculums/` - Translations

## Troubleshooting

**Invalid Domain/Entity/Language**: The script validates your inputs against available options in the config files. If you get an error, check the available options shown in the prompt.

**API Errors**: Ensure your API keys are properly set and have sufficient credits.

**No Config Files**: The script includes fallback defaults if config files aren't found.

---

**Enjoy creating personalized Active Inference curricula!** 🎯
