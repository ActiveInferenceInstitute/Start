# Configuration Files Technical Reference

## Overview

Technical documentation for configuration file formats and schemas.

## File: `domains.yaml`

### Schema

```yaml
domains:
  - name: "string"
    category: "string"
    priority: "string (high|medium|low)"
```

### Example

```yaml
domains:
  - name: "biochemistry"
    category: "life_sciences"
    priority: "high"
```

## File: `entities.yaml`

### Schema

```yaml
entities:
  - name: "string"
    description: "string"
    category: "string"
    priority: "string (high|medium|low)"
```

### Example

```yaml
entities:
  - name: "karl_friston"
    description: "Neuroscientist and Active Inference researcher"
    category: "scientist"
    priority: "high"
```

## File: `languages.yaml`

### Schema

```yaml
target_languages:
  - "string (language name)"

script_mappings:
  "language_name": "script_name"
```

### Example

```yaml
target_languages:
  - Chinese
  - Spanish
  - Arabic

script_mappings:
  Arabic: "Modern Standard Arabic"
  Chinese: "Simplified Chinese"
```

## Cross-References

- [README.md](README.md) - Configuration overview
- [../../src/config/languages.py](../../src/config/languages.py) - Language configuration loader
- [../../src/common/config.py](../../src/common/config.py) - Configuration loading utilities
